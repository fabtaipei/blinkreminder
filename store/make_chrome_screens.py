"""The five Chrome Web Store screenshots, drawn rather than captured.

    py store/make_chrome_screens.py

A photograph of a quiet app says nothing. The cue is a faint wash a few
pixels across, and five pictures of the same article are five identical grey
thumbnails. Every extension in this category sells with illustrated slides,
so these are illustrated -- but each one shows something the app actually
does, which is where slides like these usually start lying.

One design system across all five: the same palette, the same face, the
headline in the same place every time, so they read as a set rather than as
five unrelated posters.

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
MUTED = (108, 116, 128)
RULE = (222, 227, 234)
HEAD_Y, SUB_Y, BODY_Y = 86, 178, 268


def slide(head, sub, bg=PAPER, ink=INK, sub_ink=MUTED):
    """A blank slide with its headline already set. Every slide puts the
    headline in the same place; only the middle differs."""
    c = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(c)
    d.text((80, HEAD_Y), head, font=fit(d, head, True, 60, W - 160), fill=ink)
    d.text((80, SUB_Y), sub, font=fit(d, sub, False, 29, W - 160), fill=sub_ink)
    return c, d


def card(d, box, radius=14, fill=WHITE, outline=RULE):
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=1)


def lines(d, x, y, width, rows=6, step=27, colour=(214, 219, 226)):
    """A suggestion of an article, so the cue has something to sit over."""
    for i, frac in enumerate((0.96, 0.88, 1.0, 0.82, 0.93, 0.7)[:rows]):
        d.rounded_rectangle((x, y + i * step, x + int(width * frac),
                             y + i * step + 10), 5, fill=colour)


def cue(c, cx, cy, r, alpha=190, glow=0):
    """The cue as it is really drawn: lime, and see-through."""
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    if glow:
        for i in range(glow, 0, -1):
            g.ellipse((cx - r - i * 4, cy - r - i * 4, cx + r + i * 4, cy + r + i * 4),
                      fill=LIME + (int(6 * (1 - i / float(glow)) ** 2),))
    g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=LIME + (alpha,))
    c.alpha_composite(layer)


def label(d, x, y, text, size=24, bold=True, colour=INK):
    d.text((x, y), text, font=font(size, bold), fill=colour)


def pill(d, box, text, fill=INK, ink=WHITE, size=20):
    d.rounded_rectangle(box, (box[3] - box[1]) // 2, fill=fill)
    f = font(size, True)
    tw = d.textlength(text, font=f)
    d.text((box[0] + ((box[2] - box[0]) - tw) / 2, box[1] + 9), text, font=f, fill=ink)


# -- 1. what it is -----------------------------------------------------------
def s1():
    """The only slide that has to work on someone who has never heard of
    this: two reminders, at two rates, side by side."""
    c, d = slide("Blink reminders and 20-20-20 eye breaks",
                 "One app, two kinds of rest")
    panels = ((80, "Blink cue", "often, and barely there", "every 30 seconds"),
              (670, "Eye break", "now and then, on the clock", "every 20 minutes"))
    for i, (x, title, note, rate) in enumerate(panels):
        box = (x, BODY_Y, x + 530, BODY_Y + 300)
        card(d, box)
        if i == 0:
            lines(d, x + 40, BODY_Y + 55, 440)
            cue(c, x + 300, BODY_Y + 140, 58)
        else:
            d.rounded_rectangle((x + 1, BODY_Y + 1, x + 529, BODY_Y + 299), 14,
                                fill=(40, 44, 50))
            f = font(46, True)
            t = "Look away"
            d.text((x + (530 - d.textlength(t, font=f)) / 2, BODY_Y + 122), t,
                   font=f, fill=(236, 240, 245))
        d = ImageDraw.Draw(c)
        label(d, x, BODY_Y + 330, title, 32)
        label(d, x, BODY_Y + 374, note, 24, False, MUTED)
        pill(d, (x, BODY_Y + 424, x + 226, BODY_Y + 466), rate)
    return c


# -- 2. it works -------------------------------------------------------------
def s2():
    """The cue at a size you can actually see, which is the thing five
    full-page screenshots never managed."""
    c, d = slide("You will see it, and hear it",
                 "A soft cue and a quiet chime, so it does not pass you by")
    card(d, (80, BODY_Y, 740, BODY_Y + 420))
    lines(d, 120, BODY_Y + 48, 560, rows=6, step=34)
    cue(c, 410, BODY_Y + 210, 108, glow=14)
    d = ImageDraw.Draw(c)
    for i, r in enumerate((152, 202, 252)):
        d.arc((410 - r, BODY_Y + 210 - r, 410 + r, BODY_Y + 210 + r),
              -50, 50, fill=(151, 180, 44), width=max(2, 6 - i * 2))
    label(d, 810, BODY_Y + 110, "Seen", 36)
    label(d, 810, BODY_Y + 156, "Lime, soft, and gone\nin about a second.", 24, False, MUTED)
    label(d, 810, BODY_Y + 250, "Heard", 36)
    label(d, 810, BODY_Y + 296, "A quiet chime at 15%,\nor silence if you prefer.",
          24, False, MUTED)
    return c


# -- 3. it will not annoy you ------------------------------------------------
def s3():
    """The buyer's real fear is being nagged. Four real renders answer it
    better than a sentence does."""
    c, d = slide("Four styles. All adjustable.",
                 "Size, colour, strength, timing, sound — make it fit your work")
    cw, ch = 530, 200
    for name, gx, gy in (("A dot", 0, 0), ("A word", 1, 0),
                         ("Dim screen", 0, 1), ("Corner dot", 1, 1)):
        x, y = 80 + gx * 590, BODY_Y + gy * 258
        card(d, (x, y, x + cw, y + ch))
        lines(d, x + 26, y + 24, cw - 52, rows=4, step=22, colour=(226, 230, 236))
        mx, my = x + cw // 2, y + ch // 2
        if name == "A dot":
            cue(c, mx, my, 50)
        elif name == "A word":
            f = font(52, True)
            layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).text(
                (mx - d.textlength("Blink", font=f) / 2, my - 34), "Blink",
                font=f, fill=LIME + (225,))
            c.alpha_composite(layer)
        elif name == "Dim screen":
            layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).rounded_rectangle(
                (x + 1, y + 1, x + cw - 1, y + ch - 1), 14, fill=INK + (72,))
            c.alpha_composite(layer)
        else:
            cue(c, x + cw - 32, y + ch - 30, 9, alpha=255)
        d = ImageDraw.Draw(c)
        label(d, x, y + ch + 12, name, 26)
    return c


# -- 4. credibility ----------------------------------------------------------
def s4():
    """The rule people have already heard from their optometrist. It is also
    what they type into the search box."""
    c, d = slide("Every 20 minutes, look 20 feet away, for 20 seconds",
                 "The rule eye-care professionals recommend, kept for you",
                 bg=INK, ink=WHITE, sub_ink=(168, 176, 188))
    f = font(200, True)
    parts = ("20", "20", "20")
    under = ("minutes", "feet away", "seconds")
    gap = 76
    widths = [d.textlength(p, font=f) for p in parts]
    x = (W - (sum(widths) + gap * 2)) / 2
    for i, (p, wd) in enumerate(zip(parts, widths)):
        d.text((x, 330), p, font=f, fill=LIME if i == 1 else WHITE)
        fu = font(30, True)
        d.text((x + (wd - d.textlength(under[i], font=fu)) / 2, 572), under[i],
               font=fu, fill=(168, 176, 188))
        if i < 2:
            cx = x + wd + gap / 2
            d.ellipse((cx - 7, 448, cx + 7, 462), fill=(92, 100, 112))
        x += wd + gap
    return c


# -- 5. trust ----------------------------------------------------------------
def s5():
    """Every line here is checkable in the source, which is the only reason
    to make a claim this flat."""
    c, d = slide("Nothing leaves your device",
                 "It has no way to send anything anywhere, and nothing to send")
    y = BODY_Y + 6
    for text in ("No account, no sign-in",
                 "No ads, no analytics, no tracking",
                 "No network connection of any kind",
                 "Nothing on any page is ever read",
                 "Showing the cue on pages is opt-in"):
        card(d, (80, y, 1200, y + 76))
        cy = y + 38
        d.ellipse((116, cy - 14, 144, cy + 14), fill=LIME)
        # Drawn, not typed: Segoe UI Bold has no check mark, and the missing
        # glyph comes out as a box.
        d.line([(123, cy), (128, cy + 6), (137, cy - 6)], fill=INK, width=3,
               joint="curve")
        label(d, 176, y + 22, text, 28, False)
        y += 92
    return c


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, img.width, img.height))


NAMES = ("two-reminders", "seen-and-heard", "four-styles", "20-20-20", "private")
for i, fn in enumerate((s1, s2, s3, s4, s5), start=1):
    save(fn(), "s%d-%s.png" % (i, NAMES[i - 1]))
print("\nUpload these five as the screenshots, in this order.")
