# -*- coding: utf-8 -*-
"""The two windows that only a real window can test.

    py test_ui.py

Everything else in this project tests logic. These two are tested by being
DRAWN, because what goes wrong with them -- a label that never reaches the
widget, a dialog that never appears -- is invisible to any assertion about
the function that was supposed to produce them.

  1. THE STARTUP BUTTON.  A real SettingsWindow is built and its button read:
     that startup_button_text() reaches the widget, that it fits the slot, and
     that refresh_startup_button() re-reads the state and relabels -- which is
     what happens when the user comes back from the Windows Settings page the
     button sent them to.

  2. THE CRASH DIALOG.  report_startup_failure is called for real, and the
     dialog it opens is found, read and dismissed. Every other test suppresses
     it with BLINK_NO_CRASH_DIALOG, because MessageBoxW is modal and would
     hang the run -- so without this, the one thing a user sees when the app
     dies is the one thing nothing checks. The only evidence anyone had of
     the 1.4.2.0 crash was a dialog; this is that dialog.

Both are real windows from the real code, created on a desktop this process
makes for itself. They cannot reach a real screen, keyboard or foreground: no
window appears, and nothing can take a keystroke from whoever is running it.
If the desktop cannot be created or switched to, this REFUSES to run rather
than drawing on the desktop somebody is using.

Every side effect is stubbed first. A test that writes a Startup shortcut or
opens a browser tab has changed the machine it was meant to be inspecting.
"""

import ctypes
import os
import sys
import threading
import time
from ctypes import byref, wintypes

REPO = os.path.dirname(os.path.abspath(__file__))
# Captures go to a temp directory, never beside this file: a test that leaves
# two PNGs in the repo every time it runs is a test people start skipping.
# The path is printed, so a failure can still be looked at.
OUT = None

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# argtypes on every call: an undeclared 64-bit handle gets truncated to int
# and has broken this project more than once.
user32.CreateDesktopW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR,
                                  ctypes.c_void_p, wintypes.DWORD,
                                  wintypes.DWORD, ctypes.c_void_p)
user32.CreateDesktopW.restype = wintypes.HANDLE
user32.SetThreadDesktop.argtypes = (wintypes.HANDLE,)
user32.SetThreadDesktop.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowDC.argtypes = (wintypes.HWND,)
user32.GetWindowDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
user32.ReleaseDC.restype = ctypes.c_int
user32.PrintWindow.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
user32.PrintWindow.restype = wintypes.BOOL
user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetWindowTextW.restype = ctypes.c_int
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT,
                                ctypes.c_void_p, ctypes.c_void_p)
user32.PostMessageW.restype = wintypes.BOOL
user32.SendMessageW.argtypes = (wintypes.HWND, wintypes.UINT,
                                ctypes.c_void_p, ctypes.c_void_p)
user32.SendMessageW.restype = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes = (wintypes.HDC,)
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = (wintypes.HDC, ctypes.c_int,
                                         ctypes.c_int)
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = (wintypes.HDC, wintypes.HGDIOBJ)
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = (wintypes.HGDIOBJ,)
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = (wintypes.HDC,)
gdi32.DeleteDC.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumThreadWindows.argtypes = (wintypes.DWORD, ENUMPROC, wintypes.LPARAM)
user32.EnumThreadWindows.restype = wintypes.BOOL
user32.EnumChildWindows.argtypes = (wintypes.HWND, ENUMPROC, wintypes.LPARAM)
user32.EnumChildWindows.restype = wintypes.BOOL

GENERIC_ALL = 0x10000000
PW_RENDERFULLCONTENT = 2
WM_CLOSE = 0x0010
BM_CLICK = 0x00F5


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]


gdi32.GetDIBits.argtypes = (wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                            wintypes.UINT, ctypes.c_void_p,
                            ctypes.POINTER(BITMAPINFO), wintypes.UINT)
gdi32.GetDIBits.restype = ctypes.c_int


# ---------------------------------------------------------------- desktop
# Before Tk exists. SetThreadDesktop only affects windows created afterwards,
# and blink_reminder imports tkinter at module level -- so this has to run
# before the import, not before the first window.
desk = user32.CreateDesktopW("BlinkVerify", None, None, 0, GENERIC_ALL, None)
if not desk:
    sys.exit("CreateDesktopW failed: %d" % ctypes.get_last_error())
if not user32.SetThreadDesktop(desk):
    sys.exit("SetThreadDesktop failed: %d -- refusing to draw on the real "
             "desktop" % ctypes.get_last_error())
print("private desktop: BlinkVerify (nothing below can reach a real screen)")

sys.path.insert(0, REPO)
import blink_reminder as br          # noqa: E402  (must follow the switch)
from PIL import Image                # noqa: E402

FAILURES = []


def check(what, got, want):
    if got == want:
        print("  ok    %s" % what)
    else:
        FAILURES.append(what)
        print("  FAIL  %s\n          got %r, want %r" % (what, got, want))


def capture(hwnd, path):
    """Draw a window into a PNG, sized from GetWindowRect rather than from Tk.

    The bitmap MUST be created from the WINDOW dc, not from the memory dc. A
    fresh memory dc holds a 1x1 monochrome bitmap, so CreateCompatibleBitmap
    against it hands back a monochrome bitmap and every capture comes out pure
    black -- which looks exactly like a window that failed to draw, and sent
    the first version of this hunting DWM instead of its own bug.

    Three draw calls are tried in order anyway, because which one works
    depends on how a given window paints, and the result is inspected rather
    than trusted: the first that puts a non-black pixel on the bitmap wins. A
    capture routine that cannot tell a blank frame from a real one proves
    nothing about the window it was pointed at.
    """
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return None, (w, h), "empty rect"

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h          # negative: top-down rows
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    PRF_FULL = 0x0000001E   # NONCLIENT | CLIENT | ERASEBKGND | CHILDREN
    attempts = (("PrintWindow+RENDERFULLCONTENT", PW_RENDERFULLCONTENT, False),
                ("PrintWindow", 0, False),
                ("WM_PRINT", PRF_FULL, True))
    for name, flag, use_wm_print in attempts:
        win_dc = user32.GetWindowDC(hwnd)
        mem_dc = gdi32.CreateCompatibleDC(win_dc)
        bmp = gdi32.CreateCompatibleBitmap(win_dc, w, h)
        old = gdi32.SelectObject(mem_dc, bmp)
        if use_wm_print:
            user32.SendMessageW(hwnd, 0x0317,          # WM_PRINT
                                ctypes.c_void_p(mem_dc),
                                ctypes.c_void_p(flag))
        else:
            user32.PrintWindow(hwnd, mem_dc, flag)
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem_dc, bmp, 0, h, buf, byref(bmi), 0)
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, win_dc)
        rgb = img.convert("RGB")
        if rgb.getbbox() is not None and max(rgb.getextrema())[1] > 0:
            rgb.save(path)
            return path, (w, h), name
    return None, (w, h), "every method returned black"


def windows_of_thread(tid):
    found = []

    @ENUMPROC
    def cb(hwnd, _lp):
        name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, name, 256)
        found.append((hwnd, name.value))
        return True

    user32.EnumThreadWindows(tid, cb, 0)
    return found


def child_texts(hwnd):
    out = []

    @ENUMPROC
    def cb(child, _lp):
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(child, cls, 256)
        txt = ctypes.create_unicode_buffer(1024)
        user32.GetWindowTextW(child, txt, 1024)
        out.append((cls.value, txt.value, child))
        return True

    user32.EnumChildWindows(hwnd, cb, 0)
    return out


def stub_side_effects(tmp):
    """Nothing this probe does may touch the machine it runs on."""
    br.CONFIG_DIR = tmp
    br.CONFIG_PATH = os.path.join(tmp, "config.json")
    br.LOG_PATH = os.path.join(tmp, "activity.log")
    br.ASKS_PATH = os.path.join(tmp, "asks.json")
    br.TUTORIAL_PATH = os.path.join(tmp, "tutorial.json")
    br.open_link = lambda *a, **k: None        # no browser, no ms-settings
    br.sync_startup = lambda *a, **k: None     # no Startup shortcut
    br.set_startup = lambda *a, **k: False
    br.save_config = lambda *a, **k: None
    br.save_asks = lambda *a, **k: None
    br.save_tutorial = lambda *a, **k: None
    br.set_taskbar_identity = lambda *a, **k: None


# ---------------------------------------------------- 1. the button
def test_startup_button(tmp):
    print("\n1. the Startup button, rendered by the real panel")
    stub_side_effects(tmp)
    app = br.App(dict(br.DEFAULTS))
    # Forced AFTER construction: the panel decides the label in open(), and
    # this keeps PACKAGED out of App.__init__'s startup handling.
    br.PACKAGED = True
    br.PACKAGE_FAMILY = "KennyTechy.BlinkRestReminder_ndvpvnpyhp88g"
    br.packaged_startup_on = lambda: True

    app.settings.open()
    win = app.settings.win
    win.update_idletasks()
    win.update()
    button = app.settings.tog_startup

    check("the panel built a Button, not the switch",
          button.winfo_class(), "TButton")
    check("it carries the ON label from startup_button_text()",
          button.cget("text"), "Starting with Windows: ON")
    fits = button.winfo_reqwidth() <= br.SettingsWindow.STARTUP_BUTTON_W
    check("it fits the slot (%dpx needed of %dpx)"
          % (button.winfo_reqwidth(), br.SettingsWindow.STARTUP_BUTTON_W),
          fits, True)

    # refresh_startup_button has never executed. Flip the state underneath it
    # and re-run it, the way <Activate> does when the user comes back from
    # the Windows Settings page the button sent them to.
    br.packaged_startup_on = lambda: False
    app.settings.refresh_startup_button()
    win.update_idletasks()
    check("refresh_startup_button re-reads the state and relabels",
          button.cget("text"), "Starting with Windows: OFF")

    br.packaged_startup_on = lambda: True
    app.settings.refresh_startup_button()
    win.update_idletasks()
    check("... and back again", button.cget("text"),
          "Starting with Windows: ON")

    # frame(), not winfo_id(): the frame is the whole window, the id is only
    # the client area, and GetWindowRect on the client leaves the title bar
    # out of the bitmap.
    path, size, how = capture(int(win.frame(), 16),
                              os.path.join(OUT, "panel.png"))
    print("  captured %s %s via %s" % (path, size, how))
    return app


# ---------------------------------------------------- 2. the dialog
def test_crash_dialog():
    print("\n2. the crash dialog, actually displayed")
    os.environ.pop("BLINK_NO_CRASH_DIALOG", None)
    text = ('Traceback (most recent call last):\n'
            '  File "blink_reminder.py", line 6019, in build_tray\n'
            '    img = app_icon(64)\n'
            "ImportError: cannot import name '_imagingft' from 'PIL'")
    box = {}

    def show():
        box["tid"] = kernel32.GetCurrentThreadId()
        # Blocks until something closes it, which is why it is on a thread.
        br.report_startup_failure(text)
        box["returned"] = True

    worker = threading.Thread(target=show, daemon=True)
    worker.start()

    hwnd = None
    for _ in range(80):
        time.sleep(0.1)
        tid = box.get("tid")
        if tid:
            for h, cls in windows_of_thread(tid):
                if cls == "#32770":          # the dialog class
                    hwnd = h
                    break
        if hwnd:
            break

    check("a dialog actually appeared", bool(hwnd), True)
    if not hwnd:
        return

    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title, 512)
    kids = child_texts(hwnd)
    body = "\n".join(t for _c, t, _h in kids if t and "Static" in _c) or \
           "\n".join(t for _c, t, _h in kids)
    check("it is titled with the app's name", title.value, br.DISPLAY_NAME)
    check("it says the app could not start",
          "could not start" in body, True)
    check("it names the log file so a user can send it",
          br.LOG_PATH in body, True)
    check("it carries the error's own last line",
          "_imagingft" in body, True)

    path, size, how = capture(hwnd, os.path.join(OUT, "crash.png"))
    print("  captured %s %s via %s" % (path, size, how))
    print("  --- the text a user would read ---")
    for line in body.splitlines():
        print("    " + line)

    # Close it: WM_CLOSE first, then the OK button if the box ignores it.
    user32.PostMessageW(hwnd, WM_CLOSE, None, None)
    for _ in range(20):
        time.sleep(0.1)
        if box.get("returned"):
            break
    if not box.get("returned"):
        for _c, _t, child in kids:
            if _c == "Button":
                user32.SendMessageW(child, BM_CLICK, None, None)
        time.sleep(0.5)
    check("it can be dismissed", bool(box.get("returned")), True)


def main():
    global OUT
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="blink-test-ui-")
    OUT = tmp
    try:
        test_startup_button(tmp)
        test_crash_dialog()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
