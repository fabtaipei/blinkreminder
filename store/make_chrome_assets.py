"""Compose the Chrome Web Store listing images from the raw captures.

    py store/make_chrome_assets.py

chrome/e2e/store-shots.js takes the screenshots in a real headless Chrome;
two of them need composing before they can carry a listing tile, and the
promo tile is drawn here from the app's own icon.

Everything lands in store/chrome/. The numbered PNGs are the screenshots to
upload, 1280x800 each; the "-raw" files are the untouched captures, kept so
this can be re-run without taking them again.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "chrome")
sys.path.insert(0, REPO)

from PIL import Image, ImageDraw, ImageFont          # noqa: E402

W, H = 1280, 800
INK = (26, 29, 35)
DARK = (32, 32, 32)
MUTED = (160, 166, 176)


def font(size, bold=False):
    """Segoe UI if this machine has it, the default bitmap face if not."""
    for name in (("segoeuib.ttf", "seguisb.ttf") if bold else ("segoeui.ttf",)):
        path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def rounded_shadow(base, box, radius=10, spread=18):
    """A soft shadow under `box`, drawn straight onto `base`."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(spread, 0, -1):
        a = int(42 * (1 - i / float(spread)) ** 2)
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


# -- 3. the corner dot, with the corner magnified -----------------------------
page = shot("3-corner-dot-raw.png")
# The dot sits 20 in from the right, 14 up from the bottom and 9 across, so
# the crop is drawn tight around it -- magnifying an inch of blank page
# would say nothing.
inset(page, (W - 52, H - 46, W - 4, H - 4), 8, (W - 500, H - 440))
save(page, "3-corner-dot.png")

# -- 5. the pop-up, on the page it belongs over -------------------------------
back = shot("1-blink-cue.png")
# Dimmed, so the pop-up is what the eye lands on.
back.alpha_composite(Image.new("RGBA", back.size, (255, 255, 255, 120)))
pop = shot("5-popup-raw.png")
at = (W - pop.width - 70, 20)
rounded_shadow(back, (at[0], at[1], at[0] + pop.width, at[1] + pop.height), 12, 26)
back.paste(pop, at)
ImageDraw.Draw(back).rounded_rectangle(
    (at[0], at[1], at[0] + pop.width - 1, at[1] + pop.height - 1), 12,
    outline=(90, 95, 104, 255), width=1)
save(back, "5-popup.png")

# -- the 440x280 promo tile ---------------------------------------------------
import blink_reminder                                  # noqa: E402

tile = Image.new("RGBA", (440, 280), DARK + (255,))
icon = blink_reminder.app_icon(96).convert("RGBA")
tile.paste(icon, (40, 58), icon)
d = ImageDraw.Draw(tile)
d.text((40, 174), "Dry Eyes", font=font(27, True), fill=(242, 243, 245))
d.text((40, 206), "Blink Reminder Lite", font=font(27, True), fill=(242, 243, 245))
d.text((42, 244), "A gentle cue to blink", font=font(15), fill=MUTED)
save(tile, "promo-440x280.png")

# -- the 128x128 store icon ---------------------------------------------------
# The Store reads this from the package itself, so this copy exists only for a
# form that asks for the file. Drawn from the same code, so it cannot drift
# from the icon the extension actually ships -- and written with its alpha
# kept, not through save(), which flattens to RGB and would leave the ring
# sitting on a black square.
_icon = blink_reminder.app_icon(128).convert("RGBA")
_icon.save(os.path.join(OUT, "icon-128.png"))
print("  icon-128.png  %dx%d" % _icon.size)

print("\nupload the numbered PNGs as screenshots, promo-440x280.png as the "
      "small promo tile, icon-128.png only if a field asks for it.")
