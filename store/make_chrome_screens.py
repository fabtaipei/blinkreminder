"""The five Chrome Web Store screenshots, drawn rather than captured.

    py store/make_chrome_screens.py

A photograph of a quiet app says nothing. The cue is a faint wash a few
pixels across, and five pictures of the same article are five identical grey
thumbnails. Every extension in this category sells with illustrated slides,
so these are illustrated -- but each one shows something the app actually
does, which is where slides like these usually start lying.

Two rules learned the hard way. Set the type for the size it is really seen
at: the Store shows these in a carousel at about half scale, so anything
under forty pixels here is unreadable there. And cut words until only the
claim is left -- a caption nobody can read is worse than no caption, because
it takes the space one could have used.

One design system across all five: the same palette, the same face, the
headline in the same place every time, so they read as a set.

Writes store/chrome/s1-*.png .. s5-*.png at 1280x800. The 440x280 thumbnail
is a separate asset and comes from make_chrome_assets.py.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "chrome")
sys.path.insert(0, REPO)

from PIL import Image, ImageDraw                       # noqa: E402
from make_chrome_assets import font, fit, LIME, INK    # noqa: E402

W, H = 1280, 800
PAPER = (247, 248, 250)
WHITE = (255, 255, 255)
MUTED = (104, 112, 124)
RULE = (222, 227, 234)
HEAD_Y, SUB_Y, BODY_Y = 74, 176, 266

# The cue's own colour, and two alternatives at exactly its saturation and
# value (S .996, V .894), so a comparison is about hue and not about one
# being brighter than another. Cool is hue 196. Warm is hue 40, which is the
# hue of the app's own icon -- the one colour here with a claim to belong.
# Only the slides showing the cue over a white page are drawn more than one
# way; the dark slide, the privacy list, the tiles and the icon stay lime.
ACCENT = LIME
ALT_COOL = (1, 167, 228)
ALT_WARM = (228, 152, 1)


def slide(head, sub, bg=PAPER, ink=INK, sub_ink=MUTED):
    """A blank slide with its headline already set. Every slide puts the
    headline in the same place; only the middle differs."""
    c = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(c)
    d.text((80, HEAD_Y), head, font=fit(d, head, True, 72, W - 160), fill=ink)
    d.text((80, SUB_Y), sub, font=fit(d, sub, False, 36, W - 160), fill=sub_ink)
    return c, d


def card(d, box, radius=14, fill=WHITE, outline=RULE):
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=1)


def lines(d, x, y, width, rows=6, step=30, colour=(214, 219, 226)):
    """A suggestion of an article, so the cue has something to sit over."""
    for i, frac in enumerate((0.96, 0.88, 1.0, 0.82, 0.93, 0.7)[:rows]):
        d.rounded_rectangle((x, y + i * step, x + int(width * frac),
                             y + i * step + 11), 5, fill=colour)


def cue(c, cx, cy, r, alpha=190, glow=0):
    """The cue as it is really drawn: lime, and see-through."""
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    if glow:
        for i in range(glow, 0, -1):
            g.ellipse((cx - r - i * 4, cy - r - i * 4, cx + r + i * 4, cy + r + i * 4),
                      fill=ACCENT + (int(6 * (1 - i / float(glow)) ** 2),))
    g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT + (alpha,))
    c.alpha_composite(layer)


def wash(c, box, radius=14, alpha=102):
    """The break, as it is really drawn: the same lime over the whole page
    at four-tenths, not a dark panel. Nothing in the app ever goes dark."""
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=ACCENT + (alpha,))
    c.alpha_composite(layer)


def label(d, x, y, text, size=40, bold=True, colour=INK):
    d.text((x, y), text, font=font(size, bold), fill=colour)


def pill(d, box, text, fill=INK, ink=WHITE, size=28):
    d.rounded_rectangle(box, (box[3] - box[1]) // 2, fill=fill)
    f = font(size, True)
    tw = d.textlength(text, font=f)
    d.text((box[0] + ((box[2] - box[0]) - tw) / 2,
            box[1] + ((box[3] - box[1]) - size * 1.35) / 2), text, font=f, fill=ink)


# -- 1. what it is -----------------------------------------------------------
def s1():
    """The only slide that has to work on someone who has never heard of
    this: both reminders, drawn the way they really look, side by side."""
    c, d = slide("Blink reminders and 20-20-20 eye breaks",
                 "One app, two kinds of rest")
    ph = 318
    for i, (x, title, rate) in enumerate(((80, "Blink cue", "every 30 seconds"),
                                          (660, "Eye break", "every 20 minutes"))):
        box = (x, BODY_Y, x + 540, BODY_Y + ph)
        card(d, box)
        lines(d, x + 40, BODY_Y + 50, 450, rows=6, step=38)
        if i == 0:
            cue(c, x + 300, BODY_Y + 150, 64)
        else:
            wash(c, box)
            e = ImageDraw.Draw(c)
            f = font(58, True)
            t = "Look away"
            e.text((x + (540 - e.textlength(t, font=f)) / 2, BODY_Y + 124), t,
                   font=f, fill=(44, 52, 16))
        d = ImageDraw.Draw(c)
        label(d, x, BODY_Y + ph + 26, title, 46)
        pill(d, (x, BODY_Y + ph + 92, x + 300, BODY_Y + ph + 146), rate)
    return c


# -- 2. it works -------------------------------------------------------------
def s2():
    """The cue at a size you can actually see, which is the thing five
    full-page screenshots never managed."""
    c, d = slide("You will see it, and hear it",
                 "So a quiet reminder is not a missed one")
    card(d, (80, BODY_Y, 720, BODY_Y + 400))
    lines(d, 124, BODY_Y + 46, 540, rows=6, step=54)
    cue(c, 400, BODY_Y + 200, 104, glow=14)
    d = ImageDraw.Draw(c)
    for i, r in enumerate((146, 196, 246)):
        d.arc((400 - r, BODY_Y + 200 - r, 400 + r, BODY_Y + 200 + r),
              -50, 50, fill=tuple(int(v * 0.79) for v in ACCENT),
              width=max(3, 8 - i * 2))
    label(d, 790, BODY_Y + 86, "Seen", 56)
    label(d, 790, BODY_Y + 150, "Soft, and gone\nin a second.", 34, False, MUTED)
    label(d, 790, BODY_Y + 250, "Heard", 56)
    label(d, 790, BODY_Y + 314, "A quiet chime,\nor none at all.", 34, False, MUTED)
    return c


# -- 3. it will not annoy you ------------------------------------------------
def s3():
    """The buyer's real fear is being nagged. Four real renders answer it
    better than a sentence does."""
    c, d = slide("Four styles. All adjustable.", "Make it fit the way you work")
    cw, ch = 540, 186
    for name, gx, gy in (("A dot", 0, 0), ("A word", 1, 0),
                         ("Dim screen", 0, 1), ("Corner dot", 1, 1)):
        x, y = 80 + gx * 580, BODY_Y + gy * 262
        box = (x, y, x + cw, y + ch)
        card(d, box)
        lines(d, x + 28, y + 26, cw - 56, rows=4, step=34, colour=(224, 229, 235))
        mx, my = x + cw // 2, y + ch // 2
        if name == "A dot":
            cue(c, mx, my, 52)
        elif name == "A word":
            f = font(56, True)
            layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).text(
                (mx - d.textlength("Blink", font=f) / 2, my - 38), "Blink",
                font=f, fill=ACCENT + (230,))
            c.alpha_composite(layer)
        elif name == "Dim screen":
            wash(c, box)
        else:
            cue(c, x + cw - 34, y + ch - 32, 10, alpha=255)
        d = ImageDraw.Draw(c)
        label(d, x, y + ch + 14, name, 38)
    return c


# -- 4. credibility ----------------------------------------------------------
def s4():
    """The rule people have already heard from their optometrist. It is also
    what they type into the search box."""
    c, d = slide("Every 20 minutes, look 20 feet away, for 20 seconds",
                 "The rule eye-care professionals recommend",
                 bg=INK, ink=WHITE, sub_ink=(170, 178, 190))
    f = font(210, True)
    parts, under = ("20", "20", "20"), ("minutes", "feet away", "seconds")
    gap = 78
    widths = [d.textlength(p, font=f) for p in parts]
    x = (W - (sum(widths) + gap * 2)) / 2
    for i, (p, wd) in enumerate(zip(parts, widths)):
        d.text((x, 320), p, font=f, fill=LIME if i == 1 else WHITE)
        fu = font(42, True)
        d.text((x + (wd - d.textlength(under[i], font=fu)) / 2, 578), under[i],
               font=fu, fill=(170, 178, 190))
        if i < 2:
            cx = x + wd + gap / 2
            d.ellipse((cx - 8, 444, cx + 8, 460), fill=(94, 102, 114))
        x += wd + gap
    return c


# -- 5. trust ----------------------------------------------------------------
def s5():
    """Every line here is checkable in the source, which is the only reason
    to make a claim this flat."""
    c, d = slide("Nothing leaves your device",
                 "No way to send anything anywhere, and nothing to send")
    y = BODY_Y
    for text in ("No account, no sign-in",
                 "No ads, no analytics",
                 "No network connection",
                 "No page content is read",
                 "Page access is opt-in"):
        card(d, (80, y, 1200, y + 86))
        cy = y + 43
        d.ellipse((124, cy - 19, 162, cy + 19), fill=LIME)
        # Drawn, not typed: Segoe UI Bold has no check mark, and the missing
        # glyph comes out as a box.
        d.line([(133, cy + 1), (140, cy + 9), (153, cy - 9)], fill=INK, width=4,
               joint="curve")
        label(d, 196, y + 22, text, 40, False)
        y += 100
    return c


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, img.width, img.height))


NAMES = ("two-reminders", "seen-and-heard", "four-styles", "20-20-20", "private")
for i, fn in enumerate((s1, s2, s3, s4, s5), start=1):
    save(fn(), "s%d-%s.png" % (i, NAMES[i - 1]))

# The same two slides in the cooler accent, kept beside the originals rather
# than replacing them. Three pale slides in a row is a lot of white, and
# whether a second colour relieves that or just breaks the set is a thing to
# look at rather than argue about.
for i, fn, ACCENT in ((2, s2, ALT_COOL), (3, s3, ALT_WARM)):
    save(fn(), "s%d-%s-alt.png" % (i, NAMES[i - 1]))
print("\nUpload these five as the screenshots, in this order.")
