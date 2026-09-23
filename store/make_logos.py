"""Generate the Store listing images from the app's own mark.

    py store\\make_logos.py

Partner Center wants several fixed sizes, in two families:

  poster / box art   large key art, shown as the main logo on Windows 10/11
  app tile icons     300, 150 and 71 px, shown in Store listings

They are drawn here rather than by hand for the same reason the .ico and the
MSIX tiles are: the mark exists once, in blink_reminder.app_icon, and anything
that redraws it by hand drifts. These add only a background plate and, on the
large sizes, the product name.

A PLATE, not transparency. The Store composites these onto surfaces whose
colour it chooses, light or dark depending on the customer's theme, so a
transparent logo is a logo you have not designed -- the amber mark would sit at
2.25:1 on a light surface. On its own dark plate it is always the contrast it
was measured at.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont

import blink_reminder as app

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")

# The same plate the manifest gives the app's tile, so the Store listing and
# the Start menu tile are the same object.
PLATE = (43, 43, 43, 255)
NAME = app.DISPLAY_NAME
SUB = "Blink. Then rest your eyes."

# (filename, width, height, mark as a fraction of the short side, caption?)
ASSETS = [
    # 16:9 key art. Partner Center will not show a trailer at the TOP of the
    # listing without this one -- the trailer uploads and validates fine, then
    # quietly appears further down the page instead. A smaller mark than the
    # posters use, because 1080 is the short side here and the name has the
    # whole width to sit in.
    ("hero-1920x1080.png", 1920, 1080, 0.34, "tagline"),
    ("poster-720x1080.png", 720, 1080, 0.52, "full"),
    ("poster-1440x2160.png", 1440, 2160, 0.52, "full"),
    ("boxart-1080x1080.png", 1080, 1080, 0.46, "full"),
    ("boxart-2160x2160.png", 2160, 2160, 0.46, "full"),
    ("tile-300x300.png", 300, 300, 0.62, None),
    ("tile-150x150.png", 150, 150, 0.62, None),
    ("tile-71x71.png", 71, 71, 0.66, None),
]


def font(size, bold=False):
    """A real Windows UI font, falling back rather than failing."""
    for name in (("segoeuib.ttf", "seguisb.ttf") if bold
                 else ("segoeui.ttf", "seguisb.ttf")):
        try:
            return ImageFont.truetype(
                os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                             "Fonts", name), size)
        except OSError:
            continue
    return ImageFont.load_default()


def centred(draw, text, fnt, cx, top, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    draw.text((cx - (r - l) / 2 - l, top), text, font=fnt, fill=fill)
    return b - t


def build(name, w, h, mark_frac, caption):
    """caption: "full" = mark, name and tagline; "tagline" = mark and tagline
    only; None = mark alone.

    The middle mode exists for one asset. Partner Center's Super hero slot says
    "Must not include the product's title" -- the title is drawn over the image
    by the Store itself, so art that carries its own name renders it twice. A
    tagline is not a title, so the line below the mark stays.
    """
    img = Image.new("RGBA", (w, h), PLATE)
    d = ImageDraw.Draw(img)

    side = int(min(w, h) * mark_frac)
    # app_icon supersamples internally, so asking for the final size is right.
    mark = app.app_icon(side)

    if caption == "full":
        # Mark sits above centre; the name and a line of subtitle below it.
        title_px = int(min(w, h) * 0.072)
        sub_px = int(min(w, h) * 0.038)
        gap = int(min(w, h) * 0.055)
        block = side + gap + title_px + int(sub_px * 1.9)
        top = (h - block) // 2
        img.alpha_composite(mark, ((w - side) // 2, top))
        y = top + side + gap
        y += centred(d, NAME, font(title_px, "full"), w // 2, y,
                     (242, 243, 245, 255)) + int(sub_px * 0.9)
        centred(d, SUB, font(sub_px), w // 2, y, (160, 166, 176, 255))
    elif caption == "tagline":
        sub_px = int(min(w, h) * 0.042)
        gap = int(min(w, h) * 0.068)
        block = side + gap + int(sub_px * 1.4)
        top = (h - block) // 2
        img.alpha_composite(mark, ((w - side) // 2, top))
        centred(d, SUB, font(sub_px), w // 2, top + side + gap,
                (176, 182, 192, 255))
    else:
        img.alpha_composite(mark, ((w - side) // 2, (h - side) // 2))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "PNG")
    return path, os.path.getsize(path)


# ---------------------------------------------------------------------------
# Buy Me a Coffee. Not Store assets, but drawn here for the same reason the
# rest are: the mark exists once, in blink_reminder.app_icon. A support page
# reached from a button inside the app should look like it belongs to the app,
# and the one thing that makes that instant is the same mark on the same plate.
#
# The cover is 4:1, so the mark goes BESIDE the words rather than above them --
# the stacked layout the posters use leaves a 1600x400 strip almost empty.
# ---------------------------------------------------------------------------

SUPPORT = [
    ("bmc-cover-1600x400.png", 1600, 400),
]
AVATAR = ("bmc-avatar-500x500.png", 500)


def build_cover(name, w, h):
    img = Image.new("RGBA", (w, h), PLATE)
    d = ImageDraw.Draw(img)

    side = int(h * 0.56)
    mark = app.app_icon(side)
    gap = int(h * 0.16)
    title_px, sub_px = int(h * 0.125), int(h * 0.072)
    f_title, f_sub = font(title_px, True), font(sub_px)

    # Centred as ONE group, mark and words together. The first cut anchored the
    # mark to a left margin, which pushed everything into the left third -- the
    # corner where Buy Me a Coffee overlays its own avatar and display name, so
    # the art collided with the page furniture and left two thirds empty.
    tl, tt, tr, tb = d.textbbox((0, 0), NAME, font=f_title)
    sl, st, sr, sb = d.textbbox((0, 0), SUB, font=f_sub)
    text_w = max(tr - tl, sr - sl)
    x = (w - (side + gap + text_w)) // 2

    img.alpha_composite(mark, (x, (h - side) // 2))

    tx = x + side + gap
    block = (tb - tt) + int(sub_px * 1.7)
    y = (h - block) // 2
    d.text((tx - tl, y - tt), NAME, font=f_title, fill=(242, 243, 245, 255))
    d.text((tx - sl, y + (tb - tt) + int(sub_px * 0.7) - st), SUB, font=f_sub,
           fill=(168, 175, 186, 255))

    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "PNG")
    return path, os.path.getsize(path)


def build_avatar(name, size):
    """Square, but shown as a circle -- so the mark is sized to the inscribed
    circle, not to the square, or the rim clips on every side."""
    img = Image.new("RGBA", (size, size), PLATE)
    side = int(size * 0.66)
    mark = app.app_icon(side)
    img.alpha_composite(mark, ((size - side) // 2, (size - side) // 2))
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "PNG")
    return path, os.path.getsize(path)


if __name__ == "__main__":
    print("writing to %s" % OUT)
    for name, w, h, frac, cap in ASSETS:
        path, size = build(name, w, h, frac, cap)
        print("  %-24s %5dx%-5d %6.1f KB" % (name, w, h, size / 1024.0))
    print()
    for name, w, h in SUPPORT:
        path, size = build_cover(name, w, h)
        print("  %-24s %5dx%-5d %6.1f KB" % (name, w, h, size / 1024.0))
    path, size = build_avatar(*AVATAR)
    print("  %-24s %5dx%-5d %6.1f KB"
          % (AVATAR[0], AVATAR[1], AVATAR[1], size / 1024.0))
    print()
    print("All are PNG and far under the limits (50 MB poster/box, 5 MB tiles).")
