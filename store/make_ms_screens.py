"""The Microsoft Store screenshots, drawn at 1920x1080.

    py store/make_ms_screens.py

The same five arguments the Chrome slides make, plus the one the desktop app
can make and the extension cannot: the cue appears on every monitor. Drawn
natively at this size rather than scaled up from the 1280x800 set, because
upscaled type is soft type and the Store shows these large.

Accents follow the author's picks from the Chrome set: lime for the opening,
cool for the cue, warm for the styles, lime again for the rule and the
privacy list.

Writes store/ms/m1-*.png .. m6-*.png.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "ms")
sys.path.insert(0, REPO)

from PIL import Image, ImageDraw                       # noqa: E402
from make_chrome_assets import font, fit, LIME, INK    # noqa: E402

W, H = 1920, 1080
PAPER = (247, 248, 250)
WHITE = (255, 255, 255)
MUTED = (104, 112, 124)
RULE = (222, 227, 234)
COOL = (1, 167, 228)
WARM = (228, 152, 1)
M = 120                                   # the side margin everything sits in
HEAD_Y, SUB_Y, BODY_Y = 96, 234, 356

ACCENT = LIME


def slide(head, sub, bg=PAPER, ink=INK, sub_ink=MUTED):
    c = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(c)
    d.text((M, HEAD_Y), head, font=fit(d, head, True, 104, W - M * 2), fill=ink)
    d.text((M, SUB_Y), sub, font=fit(d, sub, False, 48, W - M * 2), fill=sub_ink)
    return c, d


def card(d, box, radius=20, fill=WHITE, outline=RULE):
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)


def lines(d, x, y, width, rows=6, step=42, colour=(214, 219, 226)):
    for i, frac in enumerate((0.96, 0.88, 1.0, 0.82, 0.93, 0.7)[:rows]):
        d.rounded_rectangle((x, y + i * step, x + int(width * frac),
                             y + i * step + 15), 7, fill=colour)


def cue(c, cx, cy, r, alpha=190, glow=0, colour=None):
    colour = colour or ACCENT
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    if glow:
        for i in range(glow, 0, -1):
            g.ellipse((cx - r - i * 6, cy - r - i * 6, cx + r + i * 6, cy + r + i * 6),
                      fill=colour + (int(6 * (1 - i / float(glow)) ** 2),))
    g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colour + (alpha,))
    c.alpha_composite(layer)


def wash(c, box, radius=20, alpha=102, colour=None):
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=(colour or ACCENT) + (alpha,))
    c.alpha_composite(layer)


def label(d, x, y, text, size=52, bold=True, colour=INK):
    d.text((x, y), text, font=font(size, bold), fill=colour)


def pill(d, box, text, fill=INK, ink=WHITE, size=38):
    d.rounded_rectangle(box, (box[3] - box[1]) // 2, fill=fill)
    f = font(size, True)
    tw = d.textlength(text, font=f)
    d.text((box[0] + ((box[2] - box[0]) - tw) / 2,
            box[1] + ((box[3] - box[1]) - size * 1.35) / 2), text, font=f, fill=ink)


# -- 1. what it is -----------------------------------------------------------
def m1(word=False):
    """`word` puts "Blink" inside the lime disc, in ink.

    Strictly the app draws either a disc or a word, not a word inside a
    disc, so this one is a label rather than a screenshot. It is here
    because a bare lime circle does not say what it is for, and the slide
    has to work on someone who has never heard of any of this."""
    c, d = slide("BLINK & BREAK REMINDERS", "One app, two kinds of rest")
    pw, ph = 800, 400
    for i, (x, title, rate) in enumerate(((M, "Blink cue", "every 30 seconds"),
                                          (W - M - pw, "Eye break", "every 20 minutes"))):
        box = (x, BODY_Y, x + pw, BODY_Y + ph)
        card(d, box)
        lines(d, x + 56, BODY_Y + 64, 660, rows=6, step=50)
        if i == 0:
            cx, cy, r = x + 440, BODY_Y + 190, 86
            cue(c, cx, cy, r)
            if word:
                e = ImageDraw.Draw(c)
                f = fit(e, "Blink", True, 56, int(r * 1.55))
                bb = e.textbbox((0, 0), "Blink", font=f)
                e.text((cx - (bb[2] - bb[0]) / 2 - bb[0],
                        cy - (bb[3] - bb[1]) / 2 - bb[1]), "Blink",
                       font=f, fill=INK)
                d = e
        else:
            wash(c, box)
            e = ImageDraw.Draw(c)
            f = font(78, True)
            t = "Look away"
            e.text((x + (pw - e.textlength(t, font=f)) / 2, BODY_Y + 158), t,
                   font=f, fill=(44, 52, 16))
        d = ImageDraw.Draw(c)
        label(d, x, BODY_Y + ph + 34, title, 58)
        pill(d, (x, BODY_Y + ph + 118, x + 400, BODY_Y + ph + 190), rate)
    return c


# -- 2. it works -------------------------------------------------------------
def m2():
    c, d = slide("SEE IT & HEAR IT", "So a quiet reminder is not a missed one")
    card(d, (M, BODY_Y, M + 1000, BODY_Y + 540))
    lines(d, M + 60, BODY_Y + 60, 840, rows=6, step=74)
    cue(c, M + 500, BODY_Y + 270, 142, glow=14)
    d = ImageDraw.Draw(c)
    for i, r in enumerate((196, 262, 328)):
        d.arc((M + 500 - r, BODY_Y + 270 - r, M + 500 + r, BODY_Y + 270 + r),
              -50, 50, fill=tuple(int(v * 0.79) for v in ACCENT),
              width=max(4, 11 - i * 3))
    x = M + 1110
    label(d, x, BODY_Y + 110, "Seen", 76)
    label(d, x, BODY_Y + 200, "Soft, and gone\nin a second.", 44, False, MUTED)
    label(d, x, BODY_Y + 340, "Heard", 76)
    label(d, x, BODY_Y + 430, "A quiet chime,\nor none at all.", 44, False, MUTED)
    return c


# -- 3. it will not annoy you ------------------------------------------------
def m3():
    c, d = slide("FOUR STYLES. ALL ADJUSTABLE.", "Make it fit the way you work")
    cw, ch = 800, 262
    for name, gx, gy in (("A dot", 0, 0), ("A word", 1, 0),
                         ("Dim screen", 0, 1), ("Corner dot", 1, 1)):
        x = M if gx == 0 else W - M - cw
        y = BODY_Y + gy * 346
        box = (x, y, x + cw, y + ch)
        card(d, box)
        lines(d, x + 40, y + 34, cw - 80, rows=4, step=48, colour=(224, 229, 235))
        mx, my = x + cw // 2, y + ch // 2
        if name == "A dot":
            cue(c, mx, my, 72)
        elif name == "A word":
            f = font(76, True)
            layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).text(
                (mx - d.textlength("Blink", font=f) / 2, my - 52), "Blink",
                font=f, fill=ACCENT + (230,))
            c.alpha_composite(layer)
        elif name == "Dim screen":
            wash(c, box)
        else:
            cue(c, x + cw - 48, y + ch - 44, 14, alpha=255)
        d = ImageDraw.Draw(c)
        label(d, x, y + ch + 18, name, 50)
    return c


# -- 4. credibility ----------------------------------------------------------
def m4():
    c, d = slide("THE 20-20-20 RULE",
                 "The rule eye-care professionals recommend",
                 bg=INK, ink=WHITE, sub_ink=(170, 178, 190))
    f = font(300, True)
    parts, under = ("20", "20", "20"), ("minutes", "feet away", "seconds")
    gap = 110
    widths = [d.textlength(p, font=f) for p in parts]
    x = (W - (sum(widths) + gap * 2)) / 2
    for i, (p, wd) in enumerate(zip(parts, widths)):
        d.text((x, 440), p, font=f, fill=LIME if i == 1 else WHITE)
        fu = font(56, True)
        d.text((x + (wd - d.textlength(under[i], font=fu)) / 2, 816), under[i],
               font=fu, fill=(170, 178, 190))
        if i < 2:
            cx = x + wd + gap / 2
            d.ellipse((cx - 11, 622, cx + 11, 644), fill=(94, 102, 114))
        x += wd + gap
    return c


# -- 5. the one the extension cannot make ------------------------------------
def m5():
    """Every monitor, sized correctly on each. The browser cannot do this,
    and it is the reason to install the desktop app at all."""
    c, d = slide("ON EVERY SCREEN", "Correctly sized on each, even at different scaling")
    # Three displays of different shapes, as a real desk has.
    # Laid out to the right margin, not from the left one: the third display
    # ran off the edge when its x was measured from M.
    plan = ((M, 560, 348), (740, 760, 440), (1540, 260, 200))
    base = BODY_Y + 460
    for x, w, h in plan:
        y = base - h
        card(d, (x, y, x + w, y + h), radius=14)
        lines(d, x + 30, y + 34, w - 60, rows=3, step=int(h * 0.17),
              colour=(226, 230, 236))
        cue(c, x + w - int(w * 0.22), y + int(h * 0.5), int(min(w, h) * 0.17))
        d = ImageDraw.Draw(c)
        # the stand, so it reads as a monitor and not a card
        d.rounded_rectangle((x + w / 2 - w * 0.06, base, x + w / 2 + w * 0.06,
                             base + h * 0.1), 6, fill=(208, 214, 222))
        d.rounded_rectangle((x + w / 2 - w * 0.17, base + h * 0.1,
                             x + w / 2 + w * 0.17, base + h * 0.14), 6,
                            fill=(208, 214, 222))
    label(d, M, base + 190, "A countdown to the next break sits in the corner "
                            "of every screen.", 44, False, MUTED)
    return c


# -- 6. trust ----------------------------------------------------------------
def m6():
    """The Windows list. Page access and page content are Chrome's problems;
    a camera is the one a desktop app has to answer for."""
    c, d = slide("NOTHING LEAVES YOUR DEVICE",
                 "No way to send anything anywhere, and nothing to send")
    y = BODY_Y
    for text in ("No account, no sign-in",
                 "No ads, no analytics",
                 "No network connection of any kind",
                 "No camera. It works on a timer, it does not watch you",
                 "No more than three flashes a second, enforced in code"):
        card(d, (M, y, W - M, y + 112))
        cy = y + 56
        d.ellipse((M + 54, cy - 26, M + 106, cy + 26), fill=LIME)
        d.line([(M + 67, cy + 1), (M + 77, cy + 12), (M + 94, cy - 13)],
               fill=INK, width=6, joint="curve")
        label(d, M + 150, y + 28, text, 50, False)
        y += 132
    return c


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    img.convert("RGB").save(os.path.join(OUT, name))
    print("  %s  %dx%d" % (name, img.width, img.height))


# Five drawn slides, then two real captures that are not made here: m6 and
# m7 in store/ms are photographs of the running app, kept from the previous
# listing. The every-screen slide m5 drew is not in the set -- the author
# cut it, and the argument it made survives in the description. Its code is
# left below unused rather than deleted, because the claim is still the best
# one the desktop has over the extension and may want a slide again.
NAMES = ("two-reminders", "seen-and-heard", "four-styles", "20-20-20", "private")
for i, fn, accent in ((1, m1, LIME), (2, m2, COOL), (3, m3, WARM),
                      (4, m4, LIME), (5, m6, LIME)):
    ACCENT = accent
    save(fn(), "m%d-%s.png" % (i, NAMES[i - 1]))

# The first slide again with the word inside the disc, written beside the
# plain one rather than over it, so the two can be looked at together.
ACCENT = LIME
save(m1(word=True), "m1-two-reminders-word.png")
print("\nFive slides, plus m1 with the word in the disc. m6 and m7 in "
      "store/ms are the real captures, and are not rebuilt by this script.")
