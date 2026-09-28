"""Render a line of text to an alpha mask using Windows' own text engine.

Pillow is the obvious tool and cannot do this job: the wheel on this
machine reports raqm = False, so it lays out one glyph per codepoint, left
to right. Arabic comes out unjoined and backwards, Devanagari and Bengali
come out as unreordered pieces, and none of it is visible unless you can
read the script -- which is exactly the failure a screenshot generator must
not have.

Windows shapes all of it correctly through Uniscribe/DirectWrite, and
DrawTextW goes through that. So the text is drawn white on black into an
off-screen DIB and the result is read back as a coverage mask. White on
black means the luminance IS the alpha, anti-aliasing included, so the
caller can composite it over any background.

No window is created and nothing is mapped; this is a memory bitmap.

Every ctypes signature below is declared. An undeclared 64-bit handle is
the bug this project has hit more than once: ctypes assumes int, and the
HDC either overflows or silently loses its top half.
"""

import ctypes
from ctypes import wintypes

gdi32, user32 = ctypes.windll.gdi32, ctypes.windll.user32

FW_BOLD = 700
ANSI_CHARSET, DEFAULT_CHARSET = 0, 1
OUT_TT_PRECIS, CLIP_DEFAULT_PRECIS = 4, 0
ANTIALIASED_QUALITY, CLEARTYPE_QUALITY = 4, 5
DEFAULT_PITCH, FF_DONTCARE = 0, 0
TRANSPARENT = 1
DT_LEFT, DT_CENTER = 0x0, 0x1
DT_SINGLELINE, DT_NOCLIP, DT_NOPREFIX = 0x20, 0x100, 0x800
DT_CALCRECT, DT_RTLREADING = 0x400, 0x20000
BI_RGB = 0
DIB_RGB_COLORS = 0


class LOGFONTW(ctypes.Structure):
    _fields_ = [("lfHeight", ctypes.c_long), ("lfWidth", ctypes.c_long),
                ("lfEscapement", ctypes.c_long), ("lfOrientation", ctypes.c_long),
                ("lfWeight", ctypes.c_long), ("lfItalic", ctypes.c_byte),
                ("lfUnderline", ctypes.c_byte), ("lfStrikeOut", ctypes.c_byte),
                ("lfCharSet", ctypes.c_byte), ("lfOutPrecision", ctypes.c_byte),
                ("lfClipPrecision", ctypes.c_byte), ("lfQuality", ctypes.c_byte),
                ("lfPitchAndFamily", ctypes.c_byte),
                ("lfFaceName", ctypes.c_wchar * 32)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class TEXTMETRICW(ctypes.Structure):
    _fields_ = [("tmHeight", ctypes.c_long), ("tmAscent", ctypes.c_long),
                ("tmDescent", ctypes.c_long), ("tmInternalLeading", ctypes.c_long),
                ("tmExternalLeading", ctypes.c_long), ("tmAveCharWidth", ctypes.c_long),
                ("tmMaxCharWidth", ctypes.c_long), ("tmWeight", ctypes.c_long),
                ("tmOverhang", ctypes.c_long), ("tmDigitizedAspectX", ctypes.c_long),
                ("tmDigitizedAspectY", ctypes.c_long), ("tmFirstChar", ctypes.c_wchar),
                ("tmLastChar", ctypes.c_wchar), ("tmDefaultChar", ctypes.c_wchar),
                ("tmBreakChar", ctypes.c_wchar), ("tmItalic", ctypes.c_byte),
                ("tmUnderlined", ctypes.c_byte), ("tmStruckOut", ctypes.c_byte),
                ("tmPitchAndFamily", ctypes.c_byte), ("tmCharSet", ctypes.c_byte)]


for fn, res, args in (
    (gdi32.CreateCompatibleDC, wintypes.HDC, [wintypes.HDC]),
    (gdi32.CreateDIBSection, wintypes.HBITMAP,
     [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
      ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]),
    (gdi32.CreateFontIndirectW, wintypes.HANDLE, [ctypes.c_void_p]),
    (gdi32.SelectObject, wintypes.HGDIOBJ, [wintypes.HDC, wintypes.HGDIOBJ]),
    (gdi32.DeleteObject, wintypes.BOOL, [wintypes.HGDIOBJ]),
    (gdi32.DeleteDC, wintypes.BOOL, [wintypes.HDC]),
    (gdi32.SetTextColor, wintypes.DWORD, [wintypes.HDC, wintypes.DWORD]),
    (gdi32.SetBkMode, ctypes.c_int, [wintypes.HDC, ctypes.c_int]),
    (gdi32.GetTextMetricsW, wintypes.BOOL, [wintypes.HDC, ctypes.c_void_p]),
    (user32.DrawTextW, ctypes.c_int,
     [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.c_void_p, wintypes.UINT]),
):
    fn.restype = res
    fn.argtypes = args


def _logfont(face, px, bold=True):
    lf = LOGFONTW()
    lf.lfHeight = -abs(int(px))          # negative: px is the em size
    lf.lfWeight = FW_BOLD if bold else 400
    lf.lfCharSet = DEFAULT_CHARSET
    lf.lfOutPrecision = OUT_TT_PRECIS
    lf.lfClipPrecision = CLIP_DEFAULT_PRECIS
    lf.lfQuality = ANTIALIASED_QUALITY   # grey coverage, not subpixel colour
    lf.lfPitchAndFamily = DEFAULT_PITCH | FF_DONTCARE
    lf.lfFaceName = face[:31]
    return lf


class _DC(object):
    """A memory DC with a DIB and a font selected into it."""

    def __init__(self, face, px, w, h, bold=True):
        self.w, self.h = max(1, int(w)), max(1, int(h))
        self.dc = gdi32.CreateCompatibleDC(None)
        bi = BITMAPINFO()
        bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bi.bmiHeader.biWidth = self.w
        bi.bmiHeader.biHeight = -self.h          # top-down
        bi.bmiHeader.biPlanes = 1
        bi.bmiHeader.biBitCount = 32
        bi.bmiHeader.biCompression = BI_RGB
        self.bits = ctypes.c_void_p()
        self.bmp = gdi32.CreateDIBSection(self.dc, ctypes.byref(bi), DIB_RGB_COLORS,
                                          ctypes.byref(self.bits), None, 0)
        self.oldbmp = gdi32.SelectObject(self.dc, self.bmp)
        self.font = gdi32.CreateFontIndirectW(ctypes.byref(_logfont(face, px, bold)))
        self.oldfont = gdi32.SelectObject(self.dc, self.font)
        gdi32.SetBkMode(self.dc, TRANSPARENT)
        gdi32.SetTextColor(self.dc, 0x00FFFFFF)

    def metrics(self):
        tm = TEXTMETRICW()
        gdi32.GetTextMetricsW(self.dc, ctypes.byref(tm))
        return tm

    def close(self):
        gdi32.SelectObject(self.dc, self.oldfont)
        gdi32.DeleteObject(self.font)
        gdi32.SelectObject(self.dc, self.oldbmp)
        gdi32.DeleteObject(self.bmp)
        gdi32.DeleteDC(self.dc)


def measure(face, px, text, rtl=False):
    """(width, height) DrawTextW would use, with shaping applied."""
    dc = _DC(face, px, 8, 8)
    try:
        r = wintypes.RECT(0, 0, 0, 0)
        flags = DT_CALCRECT | DT_SINGLELINE | DT_NOPREFIX | DT_NOCLIP
        if rtl:
            flags |= DT_RTLREADING
        user32.DrawTextW(dc.dc, text, -1, ctypes.byref(r), flags)
        return r.right - r.left, r.bottom - r.top
    finally:
        dc.close()


def cap_height(face, px):
    """Height of a capital H, for matching a design's cap height."""
    mask, box = render(face, px, "H")
    return (box[3] - box[1]) if box else 1


def render(face, px, text, rtl=False, pad=40):
    """(mask, ink_box) for `text`: an L-mode image and its tight bounds.

    The mask is white-on-black coverage, so it doubles as an alpha channel.
    """
    from PIL import Image
    w, h = measure(face, px, text, rtl)
    W, H = w + pad * 2, h + pad * 2
    dc = _DC(face, px, W, H)
    try:
        r = wintypes.RECT(pad, pad, W - pad, H - pad)
        flags = DT_SINGLELINE | DT_NOPREFIX | DT_NOCLIP | DT_LEFT
        if rtl:
            flags |= DT_RTLREADING
        user32.DrawTextW(dc.dc, text, -1, ctypes.byref(r), flags)
        buf = ctypes.string_at(dc.bits, W * H * 4)
    finally:
        dc.close()
    img = Image.frombuffer("RGBA", (W, H), buf, "raw", "BGRA", 0, 1)
    mask = img.getchannel("G")               # white on black: any channel
    return mask, mask.getbbox()


def fit_to_cap(face, cap, probe=200):
    """The pixel size at which this face's capitals stand `cap` tall."""
    have = cap_height(face, probe)
    return max(8, int(round(probe * float(cap) / max(1, have))))
