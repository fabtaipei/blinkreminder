"""Localise the two caption-bearing Store screenshots into every language.

    py store\\make_screenshots.py

The two PDFs in store/screenshots still carry their layers, which is what
makes this possible: the background is a flat image with no text in it, and
the caption is a separate object whose position, size and colour can be
measured exactly. So each language gets the untouched background with its
own caption drawn where the English one sits, rather than a re-typeset
picture that only resembles the original.

Matched to the original rather than guessed:

  * Arial Bold, identified by rendering candidates at the measured cap
    height and comparing ink width and letterforms. Segoe UI Bold came
    within 1.5% on width, but its R, K and G are visibly different.

The text itself is drawn by Windows, through gditext, not by Pillow. The
Pillow wheel here has raqm = False, so it places one glyph per codepoint
left to right: Arabic came out unjoined and reversed, Devanagari and
Bengali came out as unreordered pieces, and nothing about that is visible
unless you read the script.
  * Tracking is tightened until the English caption lands on the original's
    exact ink width, then carried to every other Latin-script language.
  * Cap height, optical centre and baseline all come from the PDF, so each
    language's caption sits where the English one does.

English is deliberately NOT regenerated. Those two images are already in
the Store and are the reference everything here matches; re-uploading a
near-identical pair would only invite drift.
"""

import io
import os

import pymupdf
from PIL import Image

import gditext

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots")
OUT = os.path.join(HERE, "listing-import", "shots")
FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

# (tag, source pdf, which DesktopScreenshotN it replaces)
SOURCES = [("blink", "Blink reminder - with layers.pdf", 1),
           ("break", "Break reminder - with layers.pdf", 2)]

# Font FAMILY names, which is what GDI wants; it picks the bold weight
# itself. Arial carries Latin, Greek and Cyrillic.
LATIN = "Arial"
FACE = {
    "ja": "Yu Gothic UI",
    "ko": "Malgun Gothic",
    "zh-Hant": "Microsoft JhengHei UI",
    "zh-Hans": "Microsoft YaHei UI",
    "hi": "Nirmala UI",
    "bn": "Nirmala UI",
    "th": "Leelawadee UI",
    "ar": "Segoe UI",
    "ur": "Segoe UI",
}

# Written right to left. DrawTextW needs telling; it will not infer it.
RTL = {"ar", "ur"}

# The two captions, per language. Marketing lines rather than UI strings:
# short, imperative, and upper-cased only where the script has case at all.
CAPTIONS = {
    "fr": ("CLIGNEZ", "FAITES UNE PAUSE"),
    "es": ("PARPADEA", "T\u00d3MATE UN DESCANSO"),
    "de": ("BLINZELN", "MACH EINE PAUSE"),
    "it": ("BATTI LE PALPEBRE", "FAI UNA PAUSA"),
    "pt": ("PISQUE", "FA\u00c7A UMA PAUSA"),
    "nl": ("KNIPPER", "NEEM EEN PAUZE"),
    "pl": ("MRUGNIJ", "ZR\u00d3B PRZERW\u0118"),
    "cs": ("MRKNI", "DEJ SI PAUZU"),
    "ro": ("CLIPE\u0218TE", "IA O PAUZ\u0102"),
    "hu": ("PISLOGJ", "TARTS SZ\u00dcNETET"),
    "el": ("\u0392\u039b\u0395\u03a6\u0391\u03a1\u0399\u03a3\u0395",
           "\u039a\u0391\u039d\u0395 \u0394\u0399\u0391\u039b\u0395\u0399\u039c\u039c\u0391"),
    "sv": ("BLINKA", "TA EN PAUS"),
    "fi": ("R\u00c4P\u00c4YT\u00c4", "PID\u00c4 TAUKO"),
    "da": ("BLINK", "HOLD EN PAUSE"),
    "nb": ("BLUNK", "TA EN PAUSE"),
    "uk": ("\u041a\u041b\u0406\u041f\u041d\u0418",
           "\u0417\u0420\u041e\u0411\u0418 \u041f\u0410\u0423\u0417\u0423"),
    "ru": ("\u041c\u041e\u0420\u0413\u041d\u0418",
           "\u0421\u0414\u0415\u041b\u0410\u0419 \u041f\u0410\u0423\u0417\u0423"),
    "tr": ("G\u00d6Z KIRP", "MOLA VER"),
    "vi": ("CH\u1edaP M\u1eaeT", "NGH\u1ec8 M\u1ed8T L\u00c1T"),
    "id": ("BERKEDIP", "ISTIRAHAT SEJENAK"),
    "th": ("\u0e01\u0e30\u0e1e\u0e23\u0e34\u0e1a\u0e15\u0e32",
           "\u0e1e\u0e31\u0e01\u0e2a\u0e32\u0e22\u0e15\u0e32"),
    "ja": ("\u307e\u3070\u305f\u304d", "\u3072\u3068\u4f11\u307f"),
    "ko": ("\ub208 \uae5c\ubc15\uc784", "\uc7a0\uc2dc \ud734\uc2dd"),
    "zh-Hant": ("\u7728\u7728\u773c", "\u4f11\u606f\u4e00\u4e0b"),
    "zh-Hans": ("\u7728\u7728\u773c", "\u4f11\u606f\u4e00\u4e0b"),
    "hi": ("\u092a\u0932\u0915 \u091d\u092a\u0915\u093e\u090f\u0901",
           "\u0925\u094b\u0921\u093c\u093e \u0906\u0930\u093e\u092e \u0915\u0930\u0947\u0902"),
    "bn": ("\u099a\u09cb\u0996 \u09aa\u09bf\u099f\u09aa\u09bf\u099f",
           "\u098f\u0995\u099f\u09c1 \u09ac\u09bf\u09b6\u09cd\u09b0\u09be\u09ae"),
    "ar": ("\u0627\u0631\u0645\u0634",
           "\u062e\u0630 \u0627\u0633\u062a\u0631\u0627\u062d\u0629"),
    "ur": ("\u067e\u0644\u06a9 \u062c\u06be\u067e\u06a9\u06cc\u06ba",
           "\u0630\u0631\u0627 \u0622\u0631\u0627\u0645 \u06a9\u0631\u06cc\u06ba"),
}

MAX_WIDTH_FRAC = 0.88     # a caption never crosses more of the frame than this
SIDE_MARGIN = 64          # and never comes closer than this to an edge


def draw_caption(frame, code, text, cap, centre, baseline, limit):
    """Paint one caption onto `frame`, shaped by Windows, fitted to `cap`."""
    face = FACE.get(code, LATIN)
    rtl = code in RTL
    px = gditext.fit_to_cap(face, cap)
    mask, box = gditext.render(face, px, text, rtl)
    if box is None:
        raise SystemExit("%s: nothing rendered for %r" % (code, text))
    ink = mask.crop(box)
    if ink.width > limit:                    # shrink rather than crop
        px = max(8, int(px * limit / ink.width))
        mask, box = gditext.render(face, px, text, rtl)
        ink = mask.crop(box)
    x = int(round(centre - ink.width / 2.0))
    x = min(max(x, SIDE_MARGIN), frame.width - SIDE_MARGIN - ink.width)
    y = int(round(baseline - ink.height))
    white = Image.new("RGB", ink.size, (255, 255, 255))
    frame.paste(white, (x, y), ink)
    return ink.width


def source(pdf):
    """(background image, caption ink rect, page size) from a layered PDF."""
    doc = pymupdf.open(os.path.join(SHOTS, pdf))
    page = doc[0]
    xref = page.get_images(full=True)[0][0]
    bg = Image.open(io.BytesIO(doc.extract_image(xref)["image"])).convert("RGB")
    white = [d for d in page.get_drawings() if d.get("fill") == (1.0, 1.0, 1.0)]
    if not white:
        raise SystemExit("%s: no white caption layer found" % pdf)
    rect = white[0]["rect"]
    for other in white[1:]:
        rect |= other["rect"]
    size = (page.rect.width, page.rect.height)
    doc.close()
    return bg, rect, size


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for tag, pdf, slot in SOURCES:
        bg, rect, (pw, ph) = source(pdf)
        W, H = 1922, 1080                    # the size the English PNGs are
        sx, sy = W / pw, H / ph
        base = bg.resize((W, H), Image.LANCZOS)
        cap = rect.height * sy
        cx = (rect.x0 + rect.x1) / 2.0 * sx
        baseline = rect.y1 * sy

        english = {"blink": "BLINK", "break": "TAKE A BREAK"}[tag]
        print("%-6s slot %d  cap=%.1f  centre=%.1f  baseline=%.1f  (en: %s)"
              % (tag, slot, cap, cx, baseline, english))

        for code in sorted(CAPTIONS):
            text = CAPTIONS[code][0 if tag == "blink" else 1]
            frame = base.copy()
            draw_caption(frame, code, text, cap, cx, baseline,
                         W * MAX_WIDTH_FRAC)
            folder = os.path.join(OUT, code)
            os.makedirs(folder, exist_ok=True)
            frame.save(os.path.join(folder, "%d.png" % slot), optimize=True)
            made += 1
        print("       %d languages" % len(CAPTIONS))

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _d, fs in os.walk(OUT) for f in fs)
    print("\n%d images under %s  (%.1f MB)" % (made, OUT, total / 1e6))


if __name__ == "__main__":
    main()
