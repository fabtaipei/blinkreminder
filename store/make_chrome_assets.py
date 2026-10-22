"""Lay out and caption the Chrome Web Store listing images.

    node chrome/e2e/store-shots.js     # the raw frames, from a real Chrome
    py store/make_chrome_assets.py     # this: composes, captions, writes

A screenshot of a quiet app says nothing on its own -- a lime circle over an
article could be anything. Each frame is set on a dark card under one line
saying what it is, the way the Windows listing puts BLINK across its own.

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
GROUND = (20, 21, 23)
TEXT = (242, 243, 245)
MUTED = (150, 156, 166)
DARK = (32, 32, 32)

# Each frame, and the one line that says what it is. Short enough to read in
# the thumbnail strip, which is where most people see them.
SHOTS = [
    ("1-blink-cue", "A gentle cue to blink", "Click and type straight through it"),
    ("4-settings", "Yours to tune", "Style, strength, size, timing, sound \u2014 and 30 languages"),
    ("5-popup", "One click from the toolbar", "On, off, snooze, or blink now"),
    ("2-break", "And a reminder to look away", "On the hour and the half hour"),
    ("3-corner-dot", "A small dot says it is running", "Switch it off if you would rather not see it"),
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


def slide(frame, title, note):
    """One frame on a dark card, under a line saying what it is."""
    card = Image.new("RGBA", (W, H), GROUND + (255,))
    d = ImageDraw.Draw(card)
    d.text((64, 46), title, font=font(34, True), fill=TEXT)
    d.text((64, 92), note, font=font(19), fill=MUTED)

    # Scaled to leave room for the caption, and kept in proportion: a browser
    # window stretched to fit would be the one dishonest thing here.
    inner_w, inner_h = W - 128, H - 206
    k = min(inner_w / float(frame.width), inner_h / float(frame.height))
    small = frame.resize((int(frame.width * k), int(frame.height * k)), Image.LANCZOS)
    at = ((W - small.width) // 2, 158)
    box = (at[0], at[1], at[0] + small.width, at[1] + small.height)
    rounded_shadow(card, box, 12, 22, 60)
    mask = Image.new("L", small.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, small.width - 1, small.height - 1),
                                           12, fill=255)
    card.paste(small, at, mask)
    return card


# -- the two frames that need composing before they are captioned -------------

page = shot("3-corner-dot-raw.png")
# The dot sits 20 in from the right, 14 up from the bottom and 9 across, so
# the crop is drawn tight around it -- magnifying an inch of blank page would
# say nothing.
inset(page, (W - 52, H - 46, W - 4, H - 4), 8, (W - 500, H - 440))
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

# -- the five slides ----------------------------------------------------------

SOURCE = {"3-corner-dot": "3-corner-dot-composed.png",
          "5-popup": "5-popup-composed.png"}
for name, title, note in SHOTS:
    save(slide(shot(SOURCE.get(name, name + "-raw.png")), title, note), name + ".png")
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
