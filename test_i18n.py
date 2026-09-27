"""The gate every new language has to pass.

    py test_i18n.py

Three checks, and between them they are what makes adding a tenth language
as safe as adding the second:

  1. COMPLETENESS.  Every T("...") key exists in every table, and no table
     holds a key that is no longer a string in the source. A key that is
     wrong by one character silently shows English forever, and nothing else
     would ever notice.

  2. FIT.  Every translated string is measured, in the font it is actually
     drawn in, against the width of the control it goes in. This is the one
     that matters: German, French and Russian run about 120% of English, and
     a string that is 4px too long is not an error anywhere -- it is just
     quietly clipped on someone else's screen, in a language the author
     cannot read.

  3. TRUTH.  The languages the package manifest advertises are exactly the
     languages the app speaks.

The BUDGETS table below is the contract. Its numbers are derived from the
layout constants where the layout exposes them, and read off the geometry
where it does not; the comment on each row says which gap it is. Changing a
widget's position or width means changing its budget here too -- that is the
point, not an oversight.

Needs no display: Tk measures text from a withdrawn root. Where Tk cannot
start at all, check 2 is skipped loudly and the rest still run.
"""

import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import blink_i18n
import blink_reminder as br

SW = br.SettingsWindow
SN = br.StartupNotice

FAILURES = []


def fail(what, detail):
    FAILURES.append(what)
    print("  FAIL  %s\n          %s" % (what, detail))


# ---------------------------------------------------------------- 1. keys
# Every argument to T() that is a plain literal, and every string literal
# anywhere in either source file, read straight out of the syntax tree.

def literals_and_keys():
    used, literals, dynamic = set(), set(), []
    for name in ("blink_reminder.py", "blink_i18n.py"):
        with io.open(os.path.join(HERE, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.add(node.value)
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "T":
                if (len(node.args) == 1
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)):
                    used.add(node.args[0].value)
                else:
                    dynamic.append("%s:%d" % (name, node.lineno))
    return used, literals, dynamic


def check_keys():
    print("\n1. completeness")
    used, literals, dynamic = literals_and_keys()
    print("     %d literal T() keys, %d reached indirectly (%s)"
          % (len(used), len(dynamic), ", ".join(dynamic)))
    for code, table in sorted(blink_i18n.STRINGS.items()):
        missing = sorted(used - set(table))
        if missing:
            fail("%s is missing %d translation(s)" % (code, len(missing)),
                 "\n          ".join(repr(k) for k in missing))
        orphan = sorted(k for k in table if k not in literals)
        if orphan:
            fail("%s translates %d string(s) the source no longer has"
                 % (code, len(orphan)),
                 "\n          ".join(repr(k) for k in orphan))
        if not missing and not orphan:
            print("     %-8s %3d strings, complete and with no orphans"
                  % (code, len(table)))
    for label, code in blink_i18n.LANGUAGES:
        if code != "en" and code not in blink_i18n.STRINGS:
            fail("LANGUAGES offers %r (%s) with no table" % (label, code), code)


# ----------------------------------------------------------------- 2. fit
# (english, font, pixels, where the number comes from). The font keys are the
# ones _resolve_fonts returns, matched to the style each widget is given.

CARD = 268            # a 300-wide card, inset 16 either side
SWITCH = 44           # the pill a Switch.TCheckbutton keeps on its right
BTN_PAD = 32          # Pri.bg / Sec.bg element padding, 16 each side
GHOST_PAD = 16 + 14 + 8      # Ghost.bg padding, the arrow, and its gap
SEG_PAD = 8           # Seg.bg padding, 4 each side


def seg(track, n):
    """One segment of an n-way picker on a track this wide."""
    return (track - 6) // n - SEG_PAD


BUDGETS = [
    # -- the panel's header and footer ---------------------------------
    ("A gentle nudge on every screen.", "t2", 440, "header, left of nothing"),
    ("Start with Windows", "t4", SW.STARTUP_SWITCH_W - SWITCH, "switch row"),
    ("Startup: managed by Windows", "t4",
     SW.STARTUP_BUTTON_W - BTN_PAD, "wide Secondary button"),
    ("Startup: turned off in Task Manager", "t4",
     SW.STARTUP_BUTTON_W - BTN_PAD, "wide Secondary button"),
    ("Buy me a coffee", "t4b",
     SW.WIN_W - 20 - (20 + SW.STARTUP_BUTTON_W) - 20, "link, right of the switch"),
    ("Preview blink", "t4", SW.BTN_PREVIEW_W - BTN_PAD, "footer"),
    ("Preview break", "t4", SW.BTN_PREVIEW_W - BTN_PAD, "footer"),
    ("Cancel", "t4", SW.BTN_FOOTER_W - BTN_PAD, "footer"),
    ("Save", "t4b", SW.BTN_FOOTER_W - BTN_PAD, "footer"),
    ("Save the changes you made?", "t4", 320, "a message box sizes itself"),

    # -- the two cards -------------------------------------------------
    ("Blink", "t3l", 120, "card title, break tag sits after it"),
    ("Break", "t3l", 120, "card title, break tag sits after it"),
    ("Look at trees!", "t5", 150, "after the Break title"),
    ("Remind me every", "t4", CARD, "own row"),
    ("Remind me to look away", "t4", CARD - SWITCH, "switch row"),
    ("min", "t5", 300 - 220, "hint at x=220, card edge at 300"),
    ("seconds", "t4", seg(156, 2), "unit picker"),
    ("minutes", "t4", seg(156, 2), "unit picker"),
    ("A dot", "t4b", seg(268, 3), "style picker"),
    ("A word", "t4b", seg(268, 3), "style picker"),
    ("Dim screen", "t4b", seg(268, 3), "style picker"),
    ("Strength", "t4", 90 - 16, "label, slider starts at x=90"),
    ("Colour", "t4", 120 - 16, "label, chip starts at x=120"),
    ("Change...", "t4", 132 - BTN_PAD, "colour button"),
    ("Play a sound", "t4", CARD - SWITCH, "switch row"),
    ("  Advanced settings", "t3", CARD - GHOST_PAD, "ghost button"),

    # -- the advanced windows ------------------------------------------
    ("Blink timing and sound", "t3l", CARD, "card title"),
    ("Blink look", "t3l", CARD, "card title"),
    ("Break timing and sound", "t3l", CARD, "card title"),
    ("Break look", "t3l", CARD, "card title"),
    ("Flash style", "t4", CARD, "own row"),
    ("Gentle", "t4s", seg(268, 4), "feel picker"),
    ("Standard", "t4s", seg(268, 4), "feel picker"),
    ("Sharp", "t4s", seg(268, 4), "feel picker"),
    ("Custom", "t4s", seg(268, 4), "feel picker"),
    ("Hold (s)", "t2", 92, "caption, three on a 92 pitch"),
    ("Fade (s)", "t2", 92, "caption, three on a 92 pitch"),
    ("Pulses", "t2", 84, "caption, last of three, card edge at 284"),
    ("Gap between pulses", "t4", 200 - 16 - 8, "label, spinbox at x=200"),
    ("Sound", "t4", CARD, "own row"),
    ("Ding", "t4s", seg(268, 4), "sound picker"),
    ("Chord", "t4s", seg(268, 4), "sound picker"),
    ("Chime", "t4s", seg(268, 4), "sound picker"),
    ("Notify", "t4s", seg(268, 4), "sound picker"),
    ("Volume", "t4", CARD, "own row, since S9"),
    ("Test", "t4", 88 - BTN_PAD, "button on the volume row"),
    ("Dot size", "t4", 172 - 16 - 8, "label, spinbox at x=172"),
    ("Word to show", "t4", 168 - 16 - 8, "label, entry at x=168"),
    ("Word size", "t4", 172 - 16 - 8, "label, spinbox at x=172"),
    ("Position", "t4", CARD, "own row"),
    ("Centre", "t5", 300 - 120 - 16, "caption beside the position grid"),
    ("Top left", "t5", 300 - 120 - 16, "caption beside the position grid"),
    ("Top right", "t5", 300 - 120 - 16, "caption beside the position grid"),
    ("Bottom left", "t5", 300 - 120 - 16, "caption beside the position grid"),
    ("Bottom right", "t5", 300 - 120 - 16, "caption beside the position grid"),
    ("Edge margin", "t4", 172 - 16 - 8, "label, spinbox at x=172"),
    ("Show on every monitor", "t4", CARD - SWITCH, "switch row"),
    ("Done", "t4b", 96 - BTN_PAD, "advanced footer"),

    # -- the startup notice --------------------------------------------
    ("Right-click the tray icon, by the clock, for settings.", "t4",
     SN.WIN_W - 2 * SN.PAD - 32, "the notice's one card"),
    ("Got it", "t4b", SN.BTN_W - BTN_PAD, "notice footer"),

    # -- the tray menu has no width of its own, but a runaway string
    #    would still look wrong next to the others.
    ("Blink now", "t4", 240, "tray menu"),
    ("Resume reminders", "t4", 240, "tray menu"),
    ("Snooze 30 minutes", "t4", 240, "tray menu"),
    ("Settings", "t4", 240, "tray menu"),
    ("Quit", "t4", 240, "tray menu"),
]

# Strings whose budget depends on a value only known at runtime.
def dynamic_budgets():
    return [
        # The title interpolates the product name, which is not translated.
        (br.T("%s is running") % br.DISPLAY_NAME, "t1",
         SN.WIN_W - 2 * SN.PAD, "notice title"),
        (br.T("It stays in the background and will nudge you to blink\n%s.")
         % br.describe_interval(45), "t2",
         SN.WIN_W - 2 * SN.PAD, "notice body"),
        # The support button is the notice's, not the panel's link.
        (br.T("Buy me a coffee"), "t4", SN.SUPPORT_W - BTN_PAD,
         "notice footer"),
        # The picker shows one language at a time, plus its chevron. Its own
        # endonym, never translated.
        (next(l for l, c in blink_i18n.LANGUAGES if c == br.language_code()),
         "t4", SW.LANG_W - BTN_PAD - 14 - 8, "language picker"),
        # Not translated, but it shares the header with the picker.
        (br.DISPLAY_NAME, "t1", SW.WIN_W - 20 - SW.LANG_W - 12 - 20,
         "panel title, left of the picker"),
    ]


def check_fit():
    print("\n2. fit")
    try:
        import tkinter as tk
        import tkinter.font as tkfont
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print("     SKIPPED, Tk would not start here: %s" % exc)
        return
    try:
        for _label, code in blink_i18n.LANGUAGES:
            br.set_language(code)
            br._THEME_METRICS.pop("lang", None)
            fonts = br._resolve_fonts(root)
            worst, over = (0, ""), 0
            rows = ([(br.T(k), f, px, why) for k, f, px, why in BUDGETS]
                    + dynamic_budgets())
            for text, fkey, avail, why in rows:
                font = tkfont.Font(root=root, font=fonts[fkey])
                need = max(font.measure(line) for line in text.split("\n"))
                if need > avail:
                    over += 1
                    fail("[%s] %r needs %dpx of %dpx" % (code, text, need, avail),
                         why)
                elif need / float(avail) > worst[0]:
                    worst = (need / float(avail), "%r (%d of %d, %s)"
                             % (text, need, avail, why))
            if not over:
                print("     %-8s %d strings fit; tightest is %s"
                      % (code, len(rows), worst[1]))
    finally:
        root.destroy()


# --------------------------------------------------------------- 3. truth

def check_manifest():
    print("\n3. truth")
    try:
        import build_msix
    except Exception as exc:
        print("     SKIPPED, build_msix would not import: %s" % exc)
        return
    declared = build_msix.supported_languages()
    expected = [build_msix.BASE_LANGUAGE] + sorted(blink_i18n.STRINGS)
    if declared != expected:
        fail("the manifest advertises the wrong languages",
             "declared %s, app speaks %s" % (declared, expected))
        return
    body = build_msix.render_manifest()
    for code in declared:
        if ('<Resource Language="%s" />' % code) not in body:
            fail("%s is missing from the rendered manifest" % code,
                 "supported_languages() and the template disagree")
    try:
        import xml.dom.minidom
        xml.dom.minidom.parseString(body)
    except Exception as exc:
        # A double hyphen in a comment gets you here, and makeappx's own
        # error for it names no useful line.
        fail("the manifest is not well-formed XML", exc)
    else:
        print("     manifest is well-formed and advertises: %s"
              % ", ".join(declared))


if __name__ == "__main__":
    check_keys()
    check_fit()
    check_manifest()
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)
