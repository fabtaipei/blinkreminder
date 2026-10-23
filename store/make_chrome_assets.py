"""Lay out and caption the Chrome Web Store listing images.

    node chrome/e2e/store-shots.js     # the raw frames, from a real Chrome
    py store/make_chrome_assets.py     # this: composes, captions, writes

A screenshot of a quiet app says nothing on its own: a lime circle over an
article could be anything. Each frame carries one word across it, the way the
Windows listing puts BLINK across its own. A line of small print at the top
is not read; a word this size is not missed.

Everything lands in store/chrome/. The numbered PNGs are what gets uploaded,
1280x800 each; the "-raw" files are the untouched captures, kept so this can
be re-run without taking them again.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "chrome")
sys.path.insert(0, REPO)

from PIL import Image, ImageDraw, ImageFont          # noqa: E402

W, H = 1280, 800
TEXT = (242, 243, 245)
MUTED = (150, 156, 166)
DARK = (32, 32, 32)

# The word on each frame, and where its middle sits as a fraction of the
# height -- chosen per frame to fall on the emptiest part of it.
SHOTS = [
    ("1-blink-cue", "BLINK", 0.62),
    ("4-settings", "CUSTOMISABLE", 0.86),
    ("5-popup", "SNOOZE ANY TIME", 0.86),
    ("2-break", "TAKE A BREAK", 0.62),
    ("3-corner-dot", "WORKING QUIETLY", 0.88),
]


def font(size, bold=False):
    """Segoe UI if this machine has it, the default face if not."""
    names = ("segoeuib.ttf", "seguisb.ttf") if bold else ("segoeui.ttf",)
    for name in names:
        path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def rounded_shadow(base, box, radius=10, spread=18, strength=42):
    """A soft shadow under `box`, drawn straight onto `base`."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(spread, 0, -1):
        a = int(strength * (1 - i / float(spread)) ** 2)
        d.rounded_rectangle((x0 - i, y0 - i + 3, x1 + i, y1 + i + 3),
                            radius + i, fill=(0, 0, 0, a))
    base.alpha_composite(layer)


def inset(src, crop, scale, at, radius=10):
    """A magnified corner of `src`, framed, pasted at `at`."""
    piece = src.crop(crop)
    piece = piece.resize((piece.width * scale, piece.height * scale), Image.NEAREST)
    box = (at[0], at[1], at[0] + piece.width, at[1] + piece.height)
    rounded_shadow(src, box, radius)
    mask = Image.new("L", piece.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, piece.width - 1, piece.height - 1),
                                           radius, fill=255)
    src.paste(piece, at, mask)
    ImageDraw.Draw(src).rounded_rectangle(
        (box[0], box[1], box[2] - 1, box[3] - 1), radius,
        outline=(120, 128, 140, 255), width=2)


def shot(name):
    return Image.open(os.path.join(OUT, name)).convert("RGBA")


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, img.width, img.height))


def headline(frame, word, y):
    """The frame at full size, with one word laid across it.

    Set in white, because the cue can be any colour the user picks and white
    is the one that holds against all of them, and over a soft dark wash so
    that it stays legible whatever is behind it -- a page can be any colour
    too. The wash is under the word only, not across the whole frame: it
    lifts the text off its background without hiding what is being shown.
    """
    card = frame.convert("RGBA")
    d = ImageDraw.Draw(card)
    size = 104
    f = font(size, True)
    while d.textlength(word, font=f) > W - 200 and size > 44:
        size -= 4
        f = font(size, True)
    tw = d.textlength(word, font=f)
    cx, cy = W // 2, int(H * y)

    wash = Image.new("RGBA", card.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    pad_x, pad_y = 100, int(size * 0.92)
    for i in range(30, 0, -1):
        a = int(86 * (1 - i / 30.0) ** 1.7)
        wd.rounded_rectangle((cx - tw / 2 - pad_x - i, cy - pad_y - i,
                              cx + tw / 2 + pad_x + i, cy + pad_y + i),
                             pad_y + i, fill=(0, 0, 0, a))
    card.alpha_composite(wash)

    ImageDraw.Draw(card).text((cx, cy), word, font=f, fill=(255, 255, 255, 255),
                              anchor="mm")
    return card


# -- the two frames that need composing before the word goes on ---------------

page = shot("3-corner-dot-raw.png")
# The dot sits 20 in from the right, 14 up from the bottom and 9 across, so
# the crop is drawn tight around it -- magnifying an inch of blank page would
# say nothing.
inset(page, (W - 52, H - 46, W - 4, H - 4), 8, (W - 470, H - 500))
page.convert("RGB").save(os.path.join(OUT, "3-corner-dot-composed.png"))

back = shot("1-blink-cue-raw.png")
# Dimmed, so the pop-up is what the eye lands on. Toward black, since the
# page behind it is dark.
back.alpha_composite(Image.new("RGBA", back.size, (0, 0, 0, 120)))
pop = shot("5-popup-raw.png")
at = (W - pop.width - 70, 20)
rounded_shadow(back, (at[0], at[1], at[0] + pop.width, at[1] + pop.height), 12, 26)
back.paste(pop, at)
ImageDraw.Draw(back).rounded_rectangle(
    (at[0], at[1], at[0] + pop.width - 1, at[1] + pop.height - 1), 12,
    outline=(90, 95, 104, 255), width=1)
back.convert("RGB").save(os.path.join(OUT, "5-popup-composed.png"))

# -- the five screenshots -----------------------------------------------------

SOURCE = {"3-corner-dot": "3-corner-dot-composed.png",
          "5-popup": "5-popup-composed.png"}
for name, word, y in SHOTS:
    save(headline(shot(SOURCE.get(name, name + "-raw.png")), word, y), name + ".png")
for tmp in SOURCE.values():
    os.remove(os.path.join(OUT, tmp))

# -- the promo tiles ----------------------------------------------------------
# These sit in a list of other extensions, at thumbnail size, next to a name
# the Store prints for us -- so the tile does not have to repeat the name. It
# has to catch the eye and make one promise. The cue itself does the first
# job: a lime circle on a dark field is what the product actually looks like,
# and nothing else in the category looks like it.

import blink_reminder                                  # noqa: E402

TILE_BG = (22, 24, 27)
LIME = (189, 228, 1)


def fit(d, text, bold, want, room, floor=12):
    """The largest size at or below `want` that keeps `text` inside `room`.

    It stops at `floor` rather than shrinking indefinitely: text small enough
    to fit anywhere is text nobody reads, so a line that will not fit is a
    line to shorten, not to shrink.
    """
    size = want
    f = font(size, bold)
    while d.textlength(text, font=f) > room and size > floor:
        size -= 2
        f = font(size, bold)
    if d.textlength(text, font=f) > room:
        raise SystemExit("too long for a %dpx column: %r" % (room, text))
    return f


def tile(w, h, lines, sub, dot_r, dot_c, pad):
    """The cue beside the promise.

    The words stay off the disc. Laid over it they need a dark wash to be
    legible, and that wash turns the lime olive -- killing the one thing on
    the tile anyone will recognise. So the disc keeps its colour, and the
    headline is broken over two lines to stay large in the narrower column.
    """
    card = Image.new("RGBA", (w, h), TILE_BG + (255,))

    glow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(18, 0, -1):
        gd.ellipse((dot_c[0] - dot_r - i * 3, dot_c[1] - dot_r - i * 3,
                    dot_c[0] + dot_r + i * 3, dot_c[1] + dot_r + i * 3),
                   fill=LIME + (int(5 * (1 - i / 18.0) ** 2),))
    gd.ellipse((dot_c[0] - dot_r, dot_c[1] - dot_r,
                dot_c[0] + dot_r, dot_c[1] + dot_r), fill=LIME + (255,))
    card.alpha_composite(glow)

    d = ImageDraw.Draw(card)
    room = dot_c[0] - dot_r - int(pad * 1.6)
    widest = max(lines, key=len)
    fh = fit(d, widest, True, int(h * 0.2), room, floor=int(h * 0.1))
    fs = fit(d, sub, False, int(h * 0.075), room, floor=int(h * 0.045))
    lh = int((fh.getbbox(widest)[3] - fh.getbbox(widest)[1]) * 1.32)
    sh = fs.getbbox(sub)[3] - fs.getbbox(sub)[1]
    gap = int(h * 0.055)
    top = (h - (lh * len(lines) + gap + sh)) // 2

    for i, line in enumerate(lines):
        d.text((pad, top + i * lh), line, font=fh, fill=(255, 255, 255, 255))
    d.text((pad + 2, top + lh * len(lines) + gap), sub, font=fs,
           fill=(186, 193, 203))
    return card


# Frequency is what a reminder can honestly change. The app cannot make a
# blink complete -- it can only arrive often enough that you take one.
HEAD = ["Blink", "more often."]
save(tile(440, 280, HEAD, "Every few minutes.", 100, (360, 140), 32),
     "promo-440x280.png")
save(tile(1400, 560, HEAD, "30 languages · no tracking", 236, (1120, 280), 96),
     "marquee-1400x560.png")

# -- the 128x128 store icon ---------------------------------------------------
# The Store reads this from the package itself, so this copy exists only for a
# form that asks for the file. Drawn from the same code, so it cannot drift
# from the icon the extension ships -- and written with its alpha kept, not
# through save(), which flattens to RGB and would leave the ring on a black
# square.
_icon = blink_reminder.app_icon(128).convert("RGBA")
_icon.save(os.path.join(OUT, "icon-128.png"))
print("  icon-128.png  %dx%d" % _icon.size)

print("\nupload the numbered PNGs as screenshots, promo-440x280.png as the "
      "small promo tile, icon-128.png only if a field asks for it.")
