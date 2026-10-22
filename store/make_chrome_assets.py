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

# -- the 440x280 promo tile ---------------------------------------------------

import blink_reminder                                  # noqa: E402

tile = Image.new("RGBA", (440, 280), DARK + (255,))
icon = blink_reminder.app_icon(96).convert("RGBA")
tile.paste(icon, (40, 58), icon)
d = ImageDraw.Draw(tile)
d.text((40, 174), "Dry Eyes", font=font(27, True), fill=TEXT)
d.text((40, 206), "Blink Reminder Lite", font=font(27, True), fill=TEXT)
d.text((42, 244), "A gentle cue to blink", font=font(15), fill=MUTED)
save(tile, "promo-440x280.png")

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
