"""
Blink Reminder
==============

A tray app that pulses a gentle overlay on every screen to remind you to blink.
Reminder intervals go down to a few seconds, which is the whole point of it.

Everything you are likely to want to change lives in DEFAULTS just below, or in
the Settings window reachable from the tray icon. Settings are saved to
    %APPDATA%\\BlinkReminder\\config.json
so editing this file is only needed for behaviour changes, not preferences.

Run the source with pythonw.exe so no console window appears. The packaged
build (see build.py) is a single exe and needs no Python installed at all.
"""

import base64
import ctypes
import io
import json
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import unicodedata
import wave
import winsound
import tkinter.font as tkfont
from array import array
from ctypes import wintypes
from tkinter import colorchooser, messagebox, ttk

from PIL import Image, ImageDraw

# --------------------------------------------------------------------------
# Language
#
# The tables live in blink_i18n.py; the machinery lives here. Keyed by the
# ENGLISH string, which buys two things: reading a widget still tells you
# what it says, and a string nobody has translated yet falls back to English
# rather than showing the user a bare identifier like "settings.save". There
# is no gettext, no .po file and no build step.
#
# Only what a user reads is translated. Log lines are deliberately NOT: they
# are for whoever is debugging, and a log written in ten languages is a log
# you cannot grep. DISPLAY_NAME is not translated either -- it is the
# product's name, it is what the Store reserved, and a name that changes by
# locale is a name nobody can search for.
# --------------------------------------------------------------------------

from blink_i18n import LANGUAGES, LANGUAGE_FONTS, RTL_LANGUAGES, STRINGS

# U+202B RIGHT-TO-LEFT EMBEDDING and U+202C POP DIRECTIONAL FORMATTING.
# Zero width, so they cost nothing in measurement or layout.
RLE, PDF = "‫", "‬"

# Resolved once, at startup, from config.json or from Windows. Module-level
# rather than threaded through every call because every string in the app
# wants it and none of them wants an extra argument.
_LANG = "en"


def T(text):
    """One user-facing string, in the language now in force.

    Falls back to the English key, so an untranslated string is readable
    English rather than a hole in the interface.

    Right-to-left languages come back wrapped, which declares the base
    direction of the run. Without it a label -- a left-to-right widget --
    lays Arabic out with a left-to-right base, and any Latin word or
    numeral inside lands in the wrong place. The wrap is two zero-width
    characters and changes nothing for every other language.
    """
    out = STRINGS.get(_LANG, {}).get(text, text)
    return RLE + out + PDF if _LANG in RTL_LANGUAGES else out


def translated(pairs):
    """A (label, value) table with its labels in the current language.

    The panel maps every picker's text to the value it stores through
    _text_of/_value_of, so translating the labels in one place and leaving the
    values alone is all localising a picker takes -- and config.json keeps
    holding "dot" and "bottom-right" whatever language the user reads.
    """
    return [(T(label), value) for label, value in pairs]


def language_code():
    return _LANG


def set_language(code):
    """Switch languages. Safe to call with anything, including None."""
    global _LANG
    _LANG = code if code in STRINGS else "en"
    _FAMILY_CACHE.clear()
    return _LANG


# Windows LANGID primary language IDs, for the languages where the primary
# ID is the whole answer. Chinese is deliberately absent: see below.
PRIMARY_LANGUAGES = {
    0x07: "de",   # German
    0x0A: "es",   # Spanish, every variety
    0x0C: "fr",   # French, every variety
    0x10: "it",   # Italian
    0x16: "pt",   # Portuguese, Brazil and Portugal alike
    0x11: "ja",   # Japanese
    0x12: "ko",   # Korean
    0x39: "hi",   # Hindi
    0x45: "bn",   # Bengali
    0x01: "ar",   # Arabic, every variety
    0x20: "ur",   # Urdu
    0x15: "pl",   # Polish
    0x19: "ru",   # Russian
    0x1E: "th",   # Thai
    0x1F: "tr",   # Turkish
    0x21: "id",   # Indonesian
    0x2A: "vi",   # Vietnamese
    0x05: "cs",   # Czech
    0x06: "da",   # Danish
    0x08: "el",   # Greek
    0x0B: "fi",   # Finnish
    0x0E: "hu",   # Hungarian
    0x13: "nl",   # Dutch
    0x14: "nb",   # Norwegian, both Bokmal and Nynorsk
    0x18: "ro",   # Romanian
    0x1D: "sv",   # Swedish
    0x22: "uk",   # Ukrainian
}

# Chinese sublanguages written in Traditional characters: Taiwan, Hong Kong,
# Macau, and 0x1F, the script-neutral "zh-Hant". Everything else under
# Chinese -- the mainland, Singapore, and bare 0x0004 -- is Simplified.
CHINESE_TRADITIONAL_SUBS = (1, 3, 5, 31)


def detect_language():
    """The language Windows itself is displayed in, if this app speaks it.

    GetUserDefaultUILanguage returns a LANGID: the low ten bits are the
    primary language and the rest the sublanguage. For most languages the
    primary ID is the whole answer, and the regional variety is not worth
    splitting -- one Spanish table serves Spain and Latin America, because
    nothing this app says differs between them.

    Chinese is the exception, and the sublanguage IS the question: Taiwan,
    Hong Kong and Macau are written in Traditional characters and the
    mainland and Singapore in Simplified. Showing the wrong script is worse
    than showing English, so this is the one place the sublanguage is read.
    """
    try:
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except Exception:
        return "en"
    primary, sub = langid & 0x3FF, langid >> 10
    if primary == 0x04:
        return ("zh-Hant" if sub in CHINESE_TRADITIONAL_SUBS else "zh-Hans")
    # Only a language this build actually has a table for. set_language
    # would fall back anyway, but returning a code we cannot honour would
    # make the log line lie about what the user is seeing.
    wanted = PRIMARY_LANGUAGES.get(primary, "en")
    return wanted if wanted in STRINGS else "en"


def text_cells(message):
    """Width of `message` in half-width character cells.

    Identical to len() for anything Latin, and twice that for CJK, where one
    character occupies the space of two. The overlay sizes its pane from this,
    so a four-character Chinese word is not given the room of a
    four-character English one and then cropped.
    """
    # Format characters -- the bidi marks T() adds, among others -- take no
    # room at all, so counting them would pad the pane by a character each.
    return sum(0 if unicodedata.category(ch) == "Cf"
               else 2 if unicodedata.east_asian_width(ch) in ("W", "F")
               else 1
               for ch in message)


# One entry per language, and cleared by set_language. Asking Tcl for the
# installed families is a round trip, and the overlay asks on every pulse.
_FAMILY_CACHE = {}


def overlay_family(widget):
    """The family the overlay draws its word in.

    Segoe UI for Latin, and the language's own family wherever Segoe UI has
    no glyphs to draw with. This is a plain tk Canvas rather than a themed
    widget, so it does not go through _resolve_fonts with the rest.
    """
    if _LANG not in _FAMILY_CACHE:
        have = set(tkfont.families(widget))
        _FAMILY_CACHE[_LANG] = next(
            (name for name in LANGUAGE_FONTS.get(_LANG, ()) if name in have),
            "Segoe UI")
    return _FAMILY_CACHE[_LANG]


# --------------------------------------------------------------------------
# Defaults. The Settings window writes over these and saves to config.json.
# --------------------------------------------------------------------------

# Three groups, and the grouping is the contract: one app-wide key, then one
# complete set of pulse settings per reminder. The blink's set is unprefixed
# because those names are the vocabulary Overlay itself consumes; the break's
# set is the same names under "break_". Nothing is shared between the two --
# every key below has exactly one owner, which is what stops a control on one
# card quietly changing the other reminder.
DEFAULTS = {
    # -- the app -----------------------------------------------------------
    "start_with_windows": True,   # on by default; the startup notice discloses it
    # "auto" means "ask Windows", and it is the value on a fresh install so
    # that a Chinese Windows shows a Chinese app without anyone being told to
    # go and find a setting. Picking a language in the panel writes the code
    # itself, which is what makes the choice stick on a machine whose UI
    # language later changes.
    "language": "auto",

    # -- the blink reminder ------------------------------------------------
    "interval_seconds": 45,   # how often to remind. Minimum is 3, not 300.
    "style": "dot",           # "dim" | "dot" | "text". The break owns dimming now:
                              # two full-screen washes would be indistinguishable.
    "opacity": 0.304,         # peak opacity of the overlay, 0.02 to 1.0
    "hold_ms": 550,           # how long the overlay sits at full opacity
    "fade_ms": 550,           # fade in and fade out time, 0 for an instant cut
    "blinks": 2,              # how many times to pulse per reminder
    "gap_ms": 120,            # pause between pulses
    # Lime. Chosen over the original warm amber for the same reason amber was
    # chosen over red -- it separates from the blue-greys most interfaces are
    # built from -- but it carries further at low opacity, which is what makes
    # a 30% wash readable at all. Note this no longer matches the app icon,
    # which is still amber.
    "colour": "#bde401",
    "message": "Blink",       # only used by the "text" style
    "corner": "center",       # placement for "dot" and "text". "center" is hardest to miss
    # Diameter as a PERCENTAGE of the screen's short side, so the reminder is
    # the same share of every display. 100 would be a dot as tall as the
    # screen. Stored as a share rather than a pixel count because a pixel
    # count cannot mean the same thing on a 1366x768 laptop and a 4K monitor.
    "dot_pct": 78,
    "font_size": 20,          # point size for the "text" style
    "margin": 48,             # distance from the screen edge for dot and text
    "all_monitors": True,     # show the reminder on every monitor, not just the primary
    "sound_enabled": False,
    "sound_name": "ding.wav",
    "sound_volume": 0.6,      # 0.2 to 1.0, see SOUND_TARGET_PEAK

    # -- the break reminder ------------------------------------------------
    # A second, independent nudge on the wall clock rather than on an interval
    # from launch, so it lands at :00 and :30 whenever the app happened to
    # start. Its look settings deliberately default to the blink's values, so a
    # fresh install behaves exactly as the old shared-settings build did; the
    # difference is that they are now editable rather than inherited.
    "break_enabled": True,
    "break_minutes": 30,          # 30 -> :00 and :30 of every hour
    "break_style": "dim",         # the whole screen, so it cannot be missed
    "break_opacity": 0.35,        # a tint over the screen, not a blackout
    "break_hold_ms": 1400,        # longer than a blink: this one wants noticing
    "break_fade_ms": 800,
    "break_blinks": 1,            # one long look away, not a flicker
    "break_gap_ms": 120,
    # The blink colour, not a darkening wash. The earlier near-black navy went
    # invisible against a dark desktop -- measured, a #12233F wash at 50% moved
    # mean brightness by -1 -- and a bright tint is unmissable on any wallpaper,
    # light or dark, which a dark wash can never be.
    "break_colour": "#bde401",
    "break_message": "Look into the distance",
    "break_corner": "center",
    "break_dot_pct": 22,
    "break_font_size": 20,
    "break_margin": 48,
    "break_all_monitors": True,
    "break_sound_enabled": True,
    # Same sound as the blink. The two reminders already look different enough
    # -- a dot against a full-screen tint -- that a second timbre was one
    # distinction too many.
    "break_sound_name": "ding.wav",
    "break_sound_volume": 0.6,
}

# The sixteen keys Overlay.pulse() actually reads. Each reminder stores its own
# copy of all sixteen, so a pulse config is BUILT from one reminder's keys
# rather than copied from the app config -- inheritance is not something the
# translation layer can do accidentally any more.
PULSE_KEYS = ("style", "opacity", "hold_ms", "fade_ms", "blinks", "gap_ms",
              "colour", "message", "corner", "dot_pct", "font_size",
              "margin", "all_monitors", "sound_enabled", "sound_name",
              "sound_volume")

# Keys the break used to inherit from the blink by copying the whole config.
# On upgrade each is seeded from the value the break was actually running with,
# so nothing about the break changes until the user edits it.
BREAK_SEEDS = {
    "break_dot_pct": "dot_pct",
    "break_font_size": "font_size",
    "break_corner": "corner",
    "break_margin": "margin",
    "break_all_monitors": "all_monitors",
    "break_gap_ms": "gap_ms",
    "break_sound_name": "sound_name",
}


BREAK_MINUTES = [15, 20, 30, 60]

# Four sounds that are actually four sounds. The old list named three
# PlaySound aliases, and an alias is a pointer into the user's sound scheme
# rather than a sound: SystemAsterisk, SystemNotification and SystemExclamation
# all resolved to the same file here -- Windows Background.wav -- so every
# "choice" played the identical noise. Naming the .wav removes the indirection.
# These four ship with every Windows install and were checked to differ by
# content hash, not by filename.
SOUNDS = [("Ding", "ding.wav"),              # 0.40s, a single short tap
          ("Chord", "chord.wav"),            # 0.65s, a soft resolved chord
          ("Chime", "chimes.wav"),           # 1.23s, a falling run of bells
          ("Notify", "Windows Notify.wav")]  # 1.29s, the modern toast sound

# What a saved alias becomes on upgrade. Matched to the label the alias used to
# wear rather than to the file it really played, so someone who chose "Chime"
# keeps a chime -- and hears one for the first time.
LEGACY_SOUNDS = {
    "SystemAsterisk": "ding.wav",
    "SystemNotification": "chimes.wav",
    "SystemExclamation": "chord.wav",
    "SystemDefault": "ding.wav",
    "SystemHand": "chord.wav",
}

# Peak amplitude, as a fraction of full scale, that every sound is normalised
# to before the volume setting scales it. The four files are wildly uneven as
# shipped -- ding peaks at 2.0% of full scale and chord at 18.6%, nine times
# louder -- so without this the sound picker doubles as a volume control and
# the slider would mean something different for each choice.
SOUND_TARGET_PEAK = 0.30

# The quietest the slider goes. Not 0: silence is what the "Play a sound"
# toggle is for, and a slider that can mute a sound the toggle says is on is a
# support question waiting to happen.
SOUND_VOL_MIN = 0.2

# Rendered, volume-scaled wav bytes, keyed by (file, volume). Rescaling 114k
# samples costs about 20ms -- fine once, not fine on every pulse.
_sound_cache = {}


def _render_sound(name, volume):
    """A Media .wav, normalised then scaled to `volume`, as playable bytes.

    Returns None for anything unexpected about the file so the caller can fall
    back, rather than raising in the middle of a reminder.

    The curve is volume SQUARED, not volume. Loudness is logarithmic: a linear
    slider spends its top half in a range that all sounds much the same and its
    bottom half falling off a cliff. Squaring puts the audible change roughly
    where the thumb is.
    """
    path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Media", name)
    with wave.open(path, "rb") as src:
        channels, width = src.getnchannels(), src.getsampwidth()
        rate = src.getframerate()
        frames = src.readframes(src.getnframes())
    if width != 2:
        return None
    samples = array("h")
    samples.frombytes(frames)
    if not samples:
        return None
    peak = max(max(samples), -min(samples))
    if peak <= 0:
        return None

    gain = (SOUND_TARGET_PEAK * 32767.0 / peak) * (float(volume) ** 2)
    # audioop would have done this in C, but it was removed in Python 3.13.
    # int() truncates toward zero, which is the right rounding here: it can
    # only make a sample quieter, so it can never wrap a near-peak one.
    scaled = array("h", (max(-32767, min(32767, int(v * gain))) for v in samples))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(scaled.tobytes())
    return buf.getvalue()


def _sound_bytes(name, volume):
    """The cached render for one (sound, volume) pair, or None if unplayable."""
    key = (str(name), round(float(volume), 2))
    if key not in _sound_cache:
        # Only two entries ever matter -- the blink's and the break's -- but
        # auditioning sounds in Settings adds a few. Drop the lot rather than
        # grow without bound; each render is a couple of hundred KB.
        if len(_sound_cache) > 8:
            _sound_cache.clear()
        try:
            _sound_cache[key] = _render_sound(key[0], key[1])
        except Exception:
            log_error("render_sound")
            _sound_cache[key] = None
    return _sound_cache[key]


def _play_bytes(data):
    """Blocking playback, meant to be run on a thread of its own."""
    try:
        winsound.PlaySound(data, winsound.SND_MEMORY)
    except Exception:
        log_error("play_bytes")


def play_sound(name, volume=1.0):
    """Play one of SOUNDS at `volume`, without holding up the reminder.

    SND_MEMORY rather than SND_FILENAME because the bytes have been rescaled,
    and on a daemon thread because winsound refuses SND_MEMORY | SND_ASYNC
    outright ("Cannot play asynchronously from memory"). Measured: the call
    returns in about 11ms whatever the sound's length, and a sound still
    playing never holds up quitting.

    A missing or odd file falls back to the system beep. Better a wrong sound
    than a reminder that quietly stopped making any.
    """
    try:
        data = _sound_bytes(name, volume)
        if data is None:
            winsound.MessageBeep(winsound.MB_OK)
            return
        threading.Thread(target=_play_bytes, args=(data,), daemon=True,
                         name="blink-sound").start()
    except Exception:
        log_error("play_sound")


def blink_cfg(cfg):
    """The blink reminder expressed as a pulse config."""
    return limit_flash_rate({k: cfg[k] for k in PULSE_KEYS})


def break_cfg(cfg):
    """The break reminder expressed as a pulse config.

    Built key by key from the break's own settings rather than copied from the
    app config and patched. The old version copied everything and overrode
    eight keys, so size, position, monitor coverage, gap, sound choice and
    pulse count silently came from the blink -- and break_message and the
    break's own timings had no control anywhere, because nobody noticed they
    were already stored. Building the dict makes that class of bug impossible:
    a key the break does not own cannot reach the pulse at all.
    """
    return limit_flash_rate({k: cfg["break_" + k] for k in PULSE_KEYS})


def seconds_to_next_break(minutes):
    """Seconds until the next boundary, counted from midnight.

    Computed fresh from the clock every time rather than by adding an interval,
    so it stays aligned across drift, sleep and a laptop shut overnight.

    Anchored to midnight rather than to the hour. For every interval actually
    offered this is identical to hour-anchoring, since each divides 60 -- but
    it also stays evenly spaced for one that does not, so adding an option to
    BREAK_MINUTES cannot quietly produce irregular gaps.
    """
    step = max(1, int(minutes))
    now = time.localtime()
    past = ((now.tm_hour * 60 + now.tm_min) % step) * 60 + now.tm_sec
    return step * 60 - past

# WCAG 2.3.1 (Level A) is "no more than three flashes in any one second", so a
# repeating pulse must not cycle faster than one third of a second. The shipped
# defaults are an order of magnitude under that -- one blink is ~0.4s of pulse
# every few minutes -- but hold, fade and gap could each be set to zero while
# pulses had no ceiling at all, which is three valid-looking numbers that build
# a strobe. Store Policy 11.3.2 forbids products that "result in discomfort".
MIN_PULSE_CYCLE_MS = 350
MAX_BLINKS = 10


def limit_flash_rate(cfg):
    """Keep a repeating pulse under the photosensitivity threshold.

    One cycle is fade in, hold, fade out, then the gap before the next, so it
    is 2*fade + hold + gap. Where that is too short the GAP is lengthened
    rather than the hold or the fade: the user's tuning of how the reminder
    LOOKS survives untouched, and only how often it repeats is limited.

    A single pulse cannot flash at any rate, so it is exempt.

    Applied where every pulse config is built rather than in the spinboxes,
    which means a hand-edited config.json cannot get round it either.
    """
    cfg["blinks"] = max(1, min(MAX_BLINKS, int(cfg["blinks"])))
    if cfg["blinks"] > 1:
        cycle = (2 * int(cfg["fade_ms"]) + int(cfg["hold_ms"])
                 + int(cfg["gap_ms"]))
        if cycle < MIN_PULSE_CYCLE_MS:
            cfg["gap_ms"] = int(cfg["gap_ms"]) + (MIN_PULSE_CYCLE_MS - cycle)
    return cfg


MIN_INTERVAL = 3  # seconds. Lower this if you really want to.
# A blink that lands inside a break must not simply be thrown away, so it is
# pushed out by this much and tried again, the way break_fire pushes the
# blink timer out. Short enough to still read as the blink you were owed.
BLINK_RETRY_MS = 1500

# Nobody can picture what 660ms hold plus 620ms fade feels like, so the panel
# offers these three and keeps the raw numbers under Advanced. Timings the user
# tuned by hand match no preset and simply show as "Custom".
FEELS = {
    "Gentle": {"hold_ms": 800, "fade_ms": 700, "blinks": 1},
    "Standard": {"hold_ms": 400, "fade_ms": 300, "blinks": 2},
    "Sharp": {"hold_ms": 150, "fade_ms": 60, "blinks": 3},
}
CUSTOM = "Custom"


def feel_pairs():
    """The flash-style picker as (label, canonical name).

    FEELS stays keyed in English because those keys are what feel_of returns
    and what _feel_changed looks the timings up by. Only the labels move.
    """
    return [(T(name), name) for name in list(FEELS) + [CUSTOM]]


def describe_interval(seconds):
    """"every 45 seconds" / "every 20 minutes" - whichever a person would say."""
    seconds = max(1, int(seconds))
    if seconds >= 120 and seconds % 60 == 0:
        minutes = seconds // 60
        return (T("every minute") if minutes == 1
                else T("every %d minutes") % minutes)
    return (T("every second") if seconds == 1
            else T("every %d seconds") % seconds)


def feel_of(cfg, prefix=""):
    """Which preset these timings match, or Custom if they were hand-tuned.

    The prefix picks the reminder: "" reads hold_ms/fade_ms/blinks, "break_"
    reads the break's twins. One table serves both windows, so the break's
    factory timing simply reads as Custom -- which is true. It is hand-tuned
    against these presets rather than one of them.
    """
    for name, vals in FEELS.items():
        if all(int(cfg.get(prefix + k, -1)) == v for k, v in vals.items()):
            return name
    return CUSTOM

# Two names, and the split matters. APP_NAME is an identifier: it is the
# folder settings and logs live in, so changing it would orphan every existing
# user's configuration. DISPLAY_NAME is what people read, and it is free to
# change -- which it has now done three times: once when the Store told us
# "Blink Reminder" was taken, once to put "Eye" in the name, and again to
# lead with "Dry Eyes", the single highest-intent phrase in the category.
APP_NAME = "BlinkReminder"
DISPLAY_NAME = "Dry Eyes Blink Reminder Lite"

# Display names this app has shipped under before. Anything it left behind
# under an old name has to be cleaned up, because nothing else will ever do it
# and the user has no idea the file is there. See sync_startup.
LEGACY_DISPLAY_NAMES = ("Blink Reminder", "Blink & Rest Reminder",
                        "Blink - Eye Rest Reminder")
# Windows groups taskbar buttons by this string and takes the group's icon from
# it. Without one, a Python-hosted app inherits the interpreter's identity and
# shows up as Python; a reversed-DNS-ish string of our own keeps the app's own
# icon and its own taskbar group.
APP_USER_MODEL_ID = "Kenny.BlinkReminder"

# The app's mark, in a 256-unit space. THE only copy: build.py bakes this same
# function into the .ico and build_msix into the Store tiles, so the icon on the
# exe, on every window, in the tray and on the Store listing cannot drift apart.
# It used to be drawn in three places with three sets of proportions.
#
# A dot inside a ring, not an eye. An eye is the stock symbol for this whole
# category -- and specifically the silhouette of the Store app this project
# began as a reaction to, which is a borrowed shape to wear when your artwork
# is generated anyway. This mark is the app's own behaviour instead: the dot it
# pulses, and the ring that is the pulse. It is also exactly what the corner
# indicator looks like, so the tray icon is the thing the user already sees.
# Two tones, and the second is not decoration. An app icon is shown on a title
# bar, a taskbar, an Alt-Tab card and a file-explorer row -- some light, some
# dark, and the app does not get to choose. One flat colour cannot clear 3:1
# (WCAG 1.4.11, non-text) on both: the old teal managed 5.02 on light and only
# 2.98 on DARK, which is why the icon disappeared into a dark title bar, and
# every amber warm enough to fix that inverts the problem.
#
# So the mark carries its own contrast. The warm core is what you see on a dark
# ground (6.64:1); the deep rim is what you see on a light one (6.60:1).
# Whichever way round the background goes, one of the two stands out.
ICON_AMBER = (216, 154, 32, 255)    # core and inner ring -- reads on dark
ICON_RIM = (122, 78, 0, 255)        # outer ring -- reads on light


def app_icon(size, mono=False):
    """The app's mark at any size, as a PIL image.

    mono draws it in flat white for the notification area, where the icon sits
    on a taskbar of unknown colour and a two-tone glyph turns to mud.

    Drawn at 4x and downscaled: at 16px a directly drawn ring lands on half a
    pixel and comes back as a grey smear.
    """
    from PIL import Image, ImageDraw

    k = 4
    box = size * k
    img = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = box / 256.0
    core = (255, 255, 255, 255) if mono else ICON_AMBER
    halo = (255, 255, 255, 150) if mono else ICON_RIM

    def ring(radius, width, colour):
        d.ellipse((128 * u - radius * u, 128 * u - radius * u,
                   128 * u + radius * u, 128 * u + radius * u),
                  outline=colour, width=max(1, int(round(width * u))))

    if size >= 32:
        d.ellipse((104 * u, 104 * u, 152 * u, 152 * u), fill=core)
        ring(46, 14, core)
        ring(76, 10, halo)
    else:
        # Below 32px there is room for two features, not three. Drawn bolder
        # rather than shrunk: thin strokes turn to grey mush at this size,
        # which is how a 16px icon ends up a smudge in the taskbar. A 16px
        # icon is a different drawing, not a smaller one.
        #
        # But it keeps BOTH tones, and that is the point: the tray is the one
        # place the icon definitely sits on a background the app did not pick.
        # An amber dot inside a deep ring reads on a dark taskbar (the dot) and
        # on a light one (the ring). Drawing this ring in the core colour, as
        # an earlier version did, made the whole mark vanish on a light
        # taskbar at exactly the size the user looks at most.
        d.ellipse((128 * u - 58 * u, 128 * u - 58 * u,
                   128 * u + 58 * u, 128 * u + 58 * u), fill=core)
        ring(100, 30, halo)
    return img.resize((size, size), Image.LANCZOS)


def set_window_icon(root):
    """Give every window this app opens its own icon instead of Tk's feather.

    Tk 8.6 decodes PNG natively, so the image goes in as base64 rather than
    through PIL.ImageTk -- one less thing for PyInstaller to find, and one less
    import at startup.

    iconphoto(True, ...) sets the DEFAULT for toplevels created later, which is
    what makes the settings panel, both advanced windows and the launch notice
    inherit it without any of them having to remember to ask.

    The images must outlive the call: Tk does not own them, and a collected
    PhotoImage leaves the window with no icon at all.
    """
    try:
        shots = []
        for size in (16, 32, 48, 64):
            buf = io.BytesIO()
            app_icon(size).save(buf, format="PNG")
            shots.append(tk.PhotoImage(
                master=root, data=base64.b64encode(buf.getvalue())))
        root.iconphoto(True, *shots)
        root._app_icons = shots
    except Exception:
        log_error("set_window_icon")


def set_taskbar_identity():
    """Claim our own taskbar group, so Windows shows our icon and our name.

    Unpackaged only. A packaged app has ALREADY been given an AUMID by Windows
    -- the package family name plus "!App" -- and Microsoft is explicit that
    you cannot define your own. Overwriting it does not fail; it just detaches
    the process from its own package identity, and the symptoms are quiet ones:
    the taskbar button stops grouping with the Start tile, and the jump list
    never appears. Exactly the class of bug that ships.
    """
    if PACKAGED:
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        pass


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "activity.log")
LOG_MAX_BYTES = 512 * 1024
HEARTBEAT_S = 60          # how often to prove the timer is still alive
STALL_TOLERANCE_S = 5     # drift worth writing down


def log_event(kind, detail=""):
    """Append one line to the activity log.

    The app runs under pythonw.exe, which has no console and therefore no
    stderr: without this file, a failure is completely invisible to the user
    and to anyone debugging it later. Logging must never itself break the app,
    so every error here is swallowed.
    """
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > LOG_MAX_BYTES:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write("%s  %-9s %s\n"
                     % (time.strftime("%Y-%m-%d %H:%M:%S"), kind, detail))
    except Exception:
        pass


def log_error(where, exc_text=None):
    """One line, not a stack dump, so the log stays readable."""
    text = exc_text if exc_text is not None else traceback.format_exc()
    log_event("ERROR", "%s: %s" % (where, " | ".join(
        line.strip() for line in text.strip().splitlines()[-3:])))

FROZEN = getattr(sys, "frozen", False)

# Set this to your Buy Me a Coffee handle -- the part after the slash, e.g.
# "ktaiw" for buymeacoffee.com/ktaiw. Left empty, the tray item and the notice
# link simply do not appear: better no link than a dead one.
SUPPORT_HANDLE = "kennytechy"
SUPPORT_URL = "https://buymeacoffee.com/" + SUPPORT_HANDLE if SUPPORT_HANDLE else ""

# Must match the TaskId in packaging/AppxManifest.xml. Nothing reads it yet --
# Windows owns the task -- but a mismatch is the kind of thing that is only
# ever noticed at submission time, so the two are kept side by side in a test.
STARTUP_TASK_ID = "BlinkReminderStartup"
STARTUP_SETTINGS_URI = "ms-settings:startupapps"

APPMODEL_ERROR_NO_PACKAGE = 15700


def package_family_name():
    """This app's MSIX package family name, or None when it is not packaged.

    The only reliable test. A Store build and a plain-exe build are the same
    binary, so nothing about sys.executable, the install path or sys.frozen
    tells them apart -- only Windows knows, and this is how it says so.

    Returns None on anything before Windows 8, where the export does not exist
    and nothing can be packaged anyway.
    """
    try:
        length = ctypes.c_uint32(0)
        fn = ctypes.windll.kernel32.GetCurrentPackageFamilyName
        # First call sizes the buffer and is EXPECTED to fail with
        # ERROR_INSUFFICIENT_BUFFER; only NO_PACKAGE means unpackaged.
        if fn(ctypes.byref(length), None) == APPMODEL_ERROR_NO_PACKAGE:
            return None
        buf = ctypes.create_unicode_buffer(length.value)
        if fn(ctypes.byref(length), buf) != 0:
            return None
        return buf.value or None
    except (AttributeError, OSError):
        return None


PACKAGE_FAMILY = package_family_name()
PACKAGED = PACKAGE_FAMILY is not None


# The only three things this app ever has cause to open. The allow-list is not
# paranoia about the two constants below -- it is that os.startfile hands
# anything it does not recognise to the shell, which answers with the "Pick an
# application" chooser. Measured: that dialog also BLOCKS the calling thread
# until it is dismissed, so one unrecognised string would freeze the tray and
# put a chooser on the user's screen, which from a background app reads as
# malware. Refusing is cheap; the chooser is not.
SAFE_SCHEMES = ("https://", "http://", "ms-settings:")


def open_link(target):
    """Open a URL, or a ms-settings: page, in whatever Windows uses for it.

    os.startfile rather than webbrowser: webbrowser only understands http(s)
    and would quietly do nothing with ms-settings:. Never raises and never
    blocks -- a dead link must not take the tray thread down with it.
    """
    if not str(target).startswith(SAFE_SCHEMES):
        log_event("link", "refused to open %r: unrecognised scheme" % (target,))
        return False
    try:
        os.startfile(target)
        return True
    except OSError:
        log_error("open_link %s" % target)
        return False


STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
STARTUP_LINK = os.path.join(STARTUP_DIR, DISPLAY_NAME + ".lnk")

def legacy_startup_links():
    """Shortcuts left behind by display names this app used to ship under.

    The shortcut is named after the DISPLAY name, so a rename does not move it
    -- it strands it. Without this the old "Blink Reminder.lnk" would sit there
    forever beside the new one and BOTH would fire at login, which is exactly
    the duplicate-autostart bug the packaged build already had to fix.

    Derived from STARTUP_LINK's own folder rather than kept as a constant, and
    that is not a style preference. The tests redirect STARTUP_LINK to a
    scratch directory so they never touch the real Startup folder; when this
    was a separate constant computed at import, it still pointed at the real
    folder, and a suite that believed itself sandboxed deleted the user's
    actual autostart shortcut. One knob now moves everything.
    """
    folder = os.path.dirname(STARTUP_LINK)
    return tuple(os.path.join(folder, old + ".lnk")
                 for old in LEGACY_DISPLAY_NAMES)


# Where Windows records "the user turned this Startup entry off". Verified on
# a live machine: byte 0 carries the flag and the ODD values are the disabled
# ones -- 02 for an enabled entry, 03 for one switched off in Task Manager.
STARTUP_APPROVED_KEY = (r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                        r"\StartupApproved\StartupFolder")


def startup_blocked_by_windows():
    """True if Windows has been told to skip our Startup shortcut.

    Turning an entry off in Task Manager > Startup apps does NOT delete the
    shortcut -- Windows leaves the file alone and records the decision here,
    then silently skips it at logon. This app only ever asked whether the file
    existed, so the switch in Settings would keep saying "on" while nothing
    started: the same shape of lie the packaged build had before it learned to
    admit that Windows owns startup.

    No key, no value, or anything unreadable all mean the same thing -- nobody
    has ever toggled it -- which means enabled.
    """
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            STARTUP_APPROVED_KEY) as key:
            data, _kind = winreg.QueryValueEx(
                key, os.path.basename(STARTUP_LINK))
        return bool(data[0] & 1)
    except (OSError, IndexError, TypeError):
        return False


def launch_target():
    """What the Startup shortcut should point at, as (exe, args, workdir).

    A one-file PyInstaller build unpacks itself into a temp directory that is
    deleted on exit, so __file__ points somewhere that will not exist by the
    time Windows next tries to start us. The exe is the only stable path.
    """
    if FROZEN:
        exe = os.path.abspath(sys.executable)
        return exe, "", os.path.dirname(exe)
    script = os.path.abspath(__file__)
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
    return pythonw, '"%s"' % script, os.path.dirname(script)

# --------------------------------------------------------------------------
# Win32 plumbing. This is what makes the overlay click-through and stops it
# stealing keyboard focus, which is the part a plain tkinter window gets wrong.
# --------------------------------------------------------------------------

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020   # clicks pass straight through
WS_EX_NOACTIVATE = 0x08000000    # never takes focus
WS_EX_TOOLWINDOW = 0x00000080    # keeps it out of Alt-Tab

SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SPI_GETWORKAREA = 0x0030
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79


def enable_dpi_awareness():
    """Without this the overlay is mis-sized and blurry on scaled displays."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            # Last resort in the chain. Nothing further to try, and refusing
            # to start over this is worse than running DPI-unaware -- but it
            # mis-sizes every reminder, so it is worth a line in the log.
            log_error("enable_dpi_awareness")


def virtual_screen():
    """Bounding box of every monitor combined."""
    return (
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL, wintypes.HANDLE, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM
)
MONITORINFOF_PRIMARY = 0x1
MDT_EFFECTIVE_DPI = 0
BASE_DPI = 96


def monitor_dpi(hmon):
    """Effective DPI of one monitor. 96 means 100% scaling."""
    try:
        x, y = wintypes.UINT(), wintypes.UINT()
        if ctypes.windll.shcore.GetDpiForMonitor(
            hmon, MDT_EFFECTIVE_DPI, ctypes.byref(x), ctypes.byref(y)
        ) == 0:
            return int(x.value) or BASE_DPI
    except Exception:
        # Falling back to BASE_DPI silently would size every reminder wrong.
        log_error("monitor_dpi")
    return BASE_DPI


def monitors():
    """Every monitor as (x, y, w, h, dpi, is_primary), ordered left to right.

    The virtual screen is only a bounding box, so it covers gaps between
    unevenly arranged displays. Placing one window per monitor instead means
    the reminder lands where a screen actually is, at the size that screen
    needs.
    """
    found = []

    def collect(hmon, hdc, lprect, lparam):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            r = info.rcMonitor
            found.append(
                (
                    r.left,
                    r.top,
                    r.right - r.left,
                    r.bottom - r.top,
                    monitor_dpi(hmon),
                    bool(info.dwFlags & MONITORINFOF_PRIMARY),
                )
            )
        return True

    callback = MONITORENUMPROC(collect)  # keep alive for the duration of the call
    try:
        user32.EnumDisplayMonitors(None, None, callback, 0)
    except Exception:
        # Without this the fallback below looks like a one-monitor desk.
        log_error("monitors: EnumDisplayMonitors")
    if not found:
        vx, vy, vw, vh = virtual_screen()
        found.append((vx, vy, vw, vh, BASE_DPI, True))
    found.sort(key=lambda m: (m[0], m[1]))
    return found


def primary_work_area():
    """Primary monitor minus the taskbar, in virtual-screen coordinates.

    monitors() reports whole monitors; the indicator has to sit above the
    taskbar, so it needs the work area specifically.
    """
    try:
        r = RECT()
        if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(r), 0):
            return r.left, r.top, r.right - r.left, r.bottom - r.top
    except Exception:
        pass
    for x, y, w, h, _dpi, primary in monitors():
        if primary:
            return x, y, w, h
    return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def monitor_areas():
    """Every monitor as (x, y, w, h, dpi, primary, wx, wy, ww, wh).

    The same enumeration as monitors(), carrying each screen's work area too.
    SPI_GETWORKAREA only ever reports the primary monitor, and the indicator
    has to clear the taskbar on whichever screen it sits on.
    """
    found = []

    def collect(hmon, hdc, lprect, lparam):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            r, wk = info.rcMonitor, info.rcWork
            found.append((r.left, r.top, r.right - r.left, r.bottom - r.top,
                          monitor_dpi(hmon),
                          bool(info.dwFlags & MONITORINFOF_PRIMARY),
                          wk.left, wk.top, wk.right - wk.left, wk.bottom - wk.top))
        return True

    callback = MONITORENUMPROC(collect)
    try:
        user32.EnumDisplayMonitors(None, None, callback, 0)
    except Exception:
        log_error("monitor_areas: EnumDisplayMonitors")
    if not found:
        vx, vy, vw, vh = virtual_screen()
        found.append((vx, vy, vw, vh, BASE_DPI, True, vx, vy, vw, vh))
    found.sort(key=lambda m: (m[0], m[1]))
    return found


# ctypes assumes a C int for anything it is not told about, and a window
# handle is a pointer. On 64-bit Windows an HWND still fits in 32 bits by
# contract, so truncation here is survivable -- but "survivable by contract"
# is not the same as declared, and the identical omission elsewhere in this
# project produced a crash that only appeared under load, because it depended
# on how large a handle the OS happened to hand out. Declared once, here, so
# every call below is passing a pointer rather than hoping.
user32.GetParent.argtypes = [wintypes.HWND]
user32.GetParent.restype = wintypes.HWND
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long


def make_click_through(widget):
    hwnd = user32.GetParent(widget.winfo_id()) or widget.winfo_id()
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(
        hwnd,
        GWL_EXSTYLE,
        style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
    )


def install_error_reporting(root):
    """Send every unhandled exception to the log, wherever it happened.

    The app runs under pythonw.exe, which has no stderr, and PyInstaller's
    --windowed build has none either. Tk swallows exceptions raised inside
    callbacks by design, threads swallow their own, and the result is an
    activity.log holding 29 byte-identical "WATCHDOG pulse never finished"
    lines with no cause attached to any of them. The backstop recovered the
    state and destroyed the evidence.

    Three hooks because there are three ways to raise here: inside a Tk
    callback (every timer, every button), on a worker thread (the sound
    threads), and on the main thread outside Tk.
    """
    def report(where, exc, value, tb):
        try:
            log_error(where, "".join(traceback.format_exception(exc, value, tb)))
        except Exception:
            pass

    root.report_callback_exception = lambda e, v, tb: report("tk callback", e, v, tb)

    def on_thread(args):
        name = getattr(args.thread, "name", "?")
        report("thread %s" % name, args.exc_type, args.exc_value,
               args.exc_traceback)

    threading.excepthook = on_thread
    sys.excepthook = lambda e, v, tb: report("unhandled", e, v, tb)


# Held for the life of the process. Never closed on purpose: the mutex IS the
# lock, and it must die with the process rather than with a local variable.
_INSTANCE_MUTEX = None

SINGLE_INSTANCE_MUTEX = "Local\\BlinkReminderSingleInstance"


def already_running():
    """Named mutex so launching twice does not stack two reminders.

    Local\\ rather than Global\\, which is what this used to be. The namespace
    wants to be the logon session, not the machine: under Global\\ a second
    user signed into the same PC -- or any remote session -- could not run the
    app at all, because the first user's mutex already existed. The collision
    this actually has to prevent is within one session, where a leftover
    Startup shortcut and the packaged StartupTask both fire at login.

    A NULL handle means the question could not be answered. That is reported as
    "not running": the cost is two instances, where the alternative is an app
    that silently refuses to start for a reason nobody can see.
    """
    global _INSTANCE_MUTEX
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
    err = kernel32.GetLastError()   # read immediately: any call clobbers it
    if not handle:
        log_event("start", "single-instance check failed (error %d); "
                           "starting anyway" % err)
        return False
    _INSTANCE_MUTEX = handle
    return err == 183  # ERROR_ALREADY_EXISTS


def announce_already_running():
    """Say so, instead of vanishing.

    A tray app that exits silently when launched twice is indistinguishable
    from one that crashed on startup -- and it is exactly what a Store reviewer
    sees if they install while an older copy is still in the tray. It was also
    what an existing user would get on the day they moved from the loose exe to
    the Store build: click, nothing, no window, no log line.

    A dialog rather than anything cleverer because it needs nothing from the
    copy that is already running.
    """
    try:
        root = tk.Tk()
        root.withdraw()
        set_window_icon(root)
        messagebox.showinfo(
            DISPLAY_NAME,
            T("%s is already running.\n\n"
              "Look for its icon in the system tray, next to the clock -- you "
              "may need to click the ^ arrow to see it. Right-click the icon "
              "for Settings.") % DISPLAY_NAME,
            parent=root)
        root.destroy()
    except Exception:
        log_error("announce_already_running")


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------


def migrate_dot_units(cfg, saved):
    """dot_size was a pixel count; dot_pct is a share of the screen's short side.

    A rename rather than a reinterpretation of the same key, because the two
    units overlap in exactly the range real configs live in: the old default
    was 72 PIXELS, and 72 read as a PERCENT is a dot filling nearly three
    quarters of the screen. Nothing in a bare number says which it is, so the
    key has to say instead.

    Converted values are written back into `saved` as well as `cfg`. `saved`
    is "what the user actually chose, as opposed to what defaulted", and the
    BREAK_SEEDS loop below keys off it -- without this, a converted
    break_dot_pct would be immediately overwritten by the blink's value.
    """
    for old, new in (("dot_size", "dot_pct"),
                     ("break_dot_size", "break_dot_pct")):
        if new in saved or old not in saved:
            continue
        try:
            px = int(saved[old])
        except (TypeError, ValueError):
            continue
        pct = int(round(px / float(REFERENCE_SHORT_SIDE) * 100))
        cfg[new] = saved[new] = max(1, min(100, pct))
    return cfg


def migrate_config(cfg, saved):
    """Seed the break's own keys from whatever it used to inherit.

    Presence-based rather than versioned: a version key would be a 35th setting
    that the panel would also have to round-trip, and checking presence is
    idempotent anyway -- after the first Save every key is on disk and this
    does nothing forever after.

    The point is that an upgrade must not change how anyone's break looks. Each
    new key is seeded with the value break_cfg was already handing the overlay,
    which for seven of them is the blink's value and for break_blinks is the
    literal 1 the old break_cfg hardcoded. Seeding break_blinks from
    cfg["blinks"] instead would quietly turn one long look-away into two.
    """
    # Only when there IS something to migrate. With no config file at all,
    # `saved` is empty, every seed fires, and each one overwrites a default
    # with the blink's value -- which silently undid the break's own default
    # sound on every fresh install, the one case this function has no business
    # touching. An upgrade path that also runs on first run is not a migration.
    # Units first: BREAK_SEEDS below keys off `saved`, which this updates.
    migrate_dot_units(cfg, saved)
    if saved:
        for new_key, src_key in BREAK_SEEDS.items():
            if new_key not in saved:
                cfg[new_key] = cfg[src_key]
        if "break_blinks" not in saved:
            cfg["break_blinks"] = 1
    # After the seeding, so a break that inherited its alias gets migrated too.
    # Idempotent: a filename is not a key in LEGACY_SOUNDS.
    for key in ("sound_name", "break_sound_name"):
        cfg[key] = LEGACY_SOUNDS.get(cfg.get(key), cfg.get(key))
    return cfg


def apply_language(cfg):
    """Put the language named in `cfg` into force, resolving "auto".

    Called from load_config and again from main() before the single-instance
    check, because the "already running" dialog is shown by a copy of the app
    that never gets as far as building a config.

    "auto" is resolved but NOT written back. Keeping it means a user who never
    touched the picker follows Windows if they later switch its UI language,
    which is what "auto" says on the tin; writing the resolved code in would
    pin them to whatever Windows happened to be set to on first run.
    """
    wanted = cfg.get("language", "auto")
    set_language(detect_language() if wanted == "auto" else wanted)
    return _LANG


def load_config():
    cfg, saved = dict(DEFAULTS), {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Migration keys off what was actually on disk, so `saved` has to be a
        # real mapping. The check also stops a JSON array of pairs injecting
        # keys through dict.update, and a bare string raising TypeError.
        if isinstance(data, dict):
            saved = data
            cfg.update(saved)
    except (OSError, ValueError, TypeError):
        pass
    apply_language(cfg)
    # The two words the overlay can show are user DATA, not interface text: the
    # user is free to type anything there, and once they have, it is theirs.
    # So they are localised only where the user has never chosen -- which on a
    # Chinese install means the "A word" style says 眨眼 out of the box instead
    # of an English word nobody picked.
    for key in ("message", "break_message"):
        if key not in saved:
            cfg[key] = T(DEFAULTS[key])
    migrate_config(cfg, saved)
    cfg["interval_seconds"] = max(MIN_INTERVAL, int(cfg["interval_seconds"]))
    return cfg


def save_config(cfg):
    """Write to a temp file and rename over the old one.

    Opening the real file "w" truncates it before a single byte is written, so
    anything that interrupts the dump leaves a half-file that load_config can
    only answer by falling back to DEFAULTS. That was always rude; now that the
    break's eight new keys cannot be reconstructed from an older UI, it would
    lose settings the user has no other way to get back.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, CONFIG_PATH)


def set_startup(enabled):
    """Create or remove the Startup shortcut. Only called on a real change.

    Returns True if it did the work, False if Windows owns the decision.

    In an MSIX build it owns nothing. A packaged app cannot write to the user's
    Startup folder -- the write is redirected into the package's private store,
    where Windows never looks -- so the old code succeeded, logged nothing, and
    left a tickbox that lied. Packaged, startup is DECLARED in the manifest
    (uap5:StartupTask, Enabled="true") and from then on belongs to the user via
    Task Manager. There IS a WinRT API -- StartupTask.RequestEnableAsync --
    and for a packaged desktop app it re-enables a task without prompting; the
    one state it cannot recover from is DisabledByUser, where the user has said
    no in Task Manager and Windows holds them to it. Reaching WinRT from here
    would mean COM plumbing for a switch the user can already flick in two
    clicks, so the honest thing is still to do nothing and point at the page
    that owns the decision.
    """
    if PACKAGED:
        log_event("startup", "packaged build: Windows owns the startup task %r"
                  % STARTUP_TASK_ID)
        return False
    if not enabled:
        try:
            os.remove(STARTUP_LINK)
        except OSError:
            pass
        return
    exe, args, cwd = launch_target()
    os.makedirs(os.path.dirname(STARTUP_LINK), exist_ok=True)
    quote = lambda s: s.replace("'", "''")
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{link}');"
        "$s.TargetPath='{exe}';"
        "$s.Arguments='{args}';"
        "$s.WorkingDirectory='{cwd}';"
        "$s.WindowStyle=7;"
        "$s.Description='{desc}';"
        "$s.Save()"
    ).format(
        link=quote(STARTUP_LINK),
        exe=quote(exe),
        args=quote(args),
        cwd=quote(cwd),
        desc=DISPLAY_NAME,
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        check=False,
    )
    return True


def sync_startup(enabled):
    """Reconcile the Startup folder with the setting, doing nothing if it agrees.

    The old code rewrote the shortcut on every launch, spawning PowerShell each
    time the app started. This also repairs the link if something removed it.

    There is nothing to reconcile in a packaged build -- the manifest already
    said so at install time, and the user's answer since then lives in a place
    this app is not allowed to write -- EXCEPT for one thing: the shortcut an
    earlier unpackaged copy of this app left in the Startup folder. Nothing
    else will ever remove it, and while it is there the stale .lnk and the
    manifest's StartupTask both fire at login, with only the single-instance
    mutex standing between the user and two sets of overlays.

    Done here rather than in set_startup because this runs on every launch,
    and set_startup only runs when the switch is actually changed -- which in
    a packaged build is never, since the switch is a link to Windows settings.
    """
    if PACKAGED:
        # Deletes under AppData fall through to the real file, so this reaches
        # the shortcut the unpackaged build actually wrote. Idempotent: after
        # the first launch there is nothing left to remove. Old names included,
        # since a packaged install may be replacing any earlier loose build.
        for stale in legacy_startup_links():
            try:
                os.remove(stale)
            except OSError:
                pass
        try:
            os.remove(STARTUP_LINK)
            log_event("startup", "removed the unpackaged build's leftover "
                                 "Startup shortcut; Windows owns startup now")
        except OSError:
            pass
        return
    # Whatever this app called itself last time, only this app will ever clean
    # it up. Unconditional: it has to happen whether the switch is on or off,
    # and whether or not anything needed repairing today.
    for stale in legacy_startup_links():
        if os.path.exists(stale):
            try:
                os.remove(stale)
                log_event("startup", "removed a shortcut from the app's old "
                                     "name: %s" % os.path.basename(stale))
            except OSError:
                log_error("remove legacy startup link")

    if enabled and startup_blocked_by_windows():
        # Worth a line in the log, because this is the one way the app can be
        # set to start with Windows, have a perfectly good shortcut, and still
        # not come back after a reboot. Nothing to repair: the shortcut is
        # fine, and overriding the user's Task Manager choice is exactly what
        # that switch exists to prevent.
        log_event("startup", "the shortcut is present but Windows is set to "
                             "skip it (Task Manager > Startup apps)")
    if os.path.exists(STARTUP_LINK) != bool(enabled):
        set_startup(enabled)
        return
    if enabled and startup_link_is_stale():
        # Existence was the only thing checked here, so a shortcut left
        # pointing at somewhere the exe USED to live was never repaired:
        # every later launch saw a file, agreed with the setting, and
        # returned. The symptom is the worst kind -- the switch says on, the
        # shortcut is there, and the app silently does not come back after a
        # reboot, or comes back as an older copy from a stale path. The
        # README's advice to untick and retick the box was a workaround for
        # this.
        log_event("startup", "the Startup shortcut pointed somewhere else; "
                             "repointed it at %s" % launch_target()[0])
        set_startup(True)


def startup_link_is_stale():
    """True if the Startup shortcut does not point at this exe.

    Read from the .lnk's own bytes rather than through WScript.Shell: this
    runs on every launch, and the whole reason sync_startup checks before
    acting is that the old code spawned PowerShell each time the app
    started. A shortcut stores its target as text, so the question is
    whether this exe's path is in there -- in UTF-16, which is where a
    modern .lnk keeps it, or in the local code page for an older one.

    Answers False on any doubt. Rewriting a shortcut that was fine costs a
    subprocess; failing to rewrite one that is stale costs nothing today,
    so the safe direction when the file cannot be read is to leave it be.
    """
    try:
        with open(STARTUP_LINK, "rb") as fh:
            blob = fh.read()
        target = os.path.abspath(launch_target()[0])
        if target.encode("utf-16-le") in blob:
            return False
        try:
            return target.encode("mbcs") not in blob
        except UnicodeEncodeError:
            return True          # a path the old encoding cannot express
    except OSError:
        return False


# --------------------------------------------------------------------------
# The overlay
# --------------------------------------------------------------------------


class _ClickThroughWindow:
    """A borderless, always-on-top, click-through Toplevel with a canvas.

    Every window this app puts on screen -- the reminder panes, the corner
    indicator dots, the countdown pill -- is this same object. It used to be
    two independent classes with eleven identical lines of constructor
    between them, which is how they came to disagree about the one thing
    that matters here: the order of styling and mapping. See style_once.
    """

    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.canvas = tk.Canvas(self.win, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self._styled = False

    def style_once(self):
        """Apply the win32 extended styles. Safe before the window is mapped.

        This used to say the styles "only work once mapped", and show() was
        therefore called first. Measured, on a real HWND: applying them while
        the window is still withdrawn sets all four, and all four survive the
        deiconify. The old claim was not merely redundant, it was the bug --
        a pane that maps before it is WS_EX_NOACTIVATE takes the foreground,
        so the first blink of every session ate whatever was being typed.

        The indicator and the countdown were still doing it the wrong way
        round long after the panes were fixed, because they were a separate
        class that never got the correction. Both orders live in one place
        now, so there is only one of them to be right.
        """
        if not self._styled:
            self.win.update_idletasks()
            make_click_through(self.win)
            self._styled = True

    def alpha(self, value):
        self.win.attributes("-alpha", max(0.0, min(1.0, value)))

    def move(self, w, h, x, y):
        self.win.geometry("%dx%d+%d+%d" % (w, h, x, y))

    def _map(self):
        """Style, then map. Never the other way round."""
        self.style_once()
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        try:
            self.win.attributes("-alpha", 0.0)
            self.win.withdraw()
        except tk.TclError:
            pass


class _Pane(_ClickThroughWindow):
    """One click-through window covering a single monitor."""

    def show(self):
        self._map()


class Overlay:
    """One pane per monitor, all pulsed together when a reminder fires."""

    def __init__(self, root):
        self.root = root
        self.cfg = None
        self.busy = False
        self.watchdog = None
        self.panes = []    # every pane ever created, reused across pulses
        self.active = []   # the subset showing for the current pulse
        self.indicator = None   # set by App; hidden for the length of a pulse
        # Generation, the same shape RunningIndicator uses for self.flight.
        # A pulse runs as a chain of after() callbacks whose ids are never
        # kept, so interrupt() could abandon a pulse without stopping its
        # chain: the orphan kept reading self.cfg and self.active and strobed
        # the pulse that replaced it. Every link checks this instead.
        self.pulse_id = 0

    def _panes_for(self, count):
        """Grow the pool to `count` panes and park any spares out of sight."""
        while len(self.panes) < count:
            self.panes.append(_Pane(self.root))
        for spare in self.panes[count:]:
            spare.hide()
        return self.panes[:count]

    # -- geometry -----------------------------------------------------------

    def _draw(self, pane, cfg, mon, base_dpi):
        """Size, position and paint one pane for the monitor it sits on.

        The arithmetic lives in reminder_rect, which the indicator's flight
        target also uses, so the thing that is painted and the thing that is
        flown to cannot disagree.
        """
        style = cfg["style"]
        x, y, w, h = reminder_rect(mon, cfg, base_dpi)

        if style == "dim":
            pane.win.attributes("-transparentcolor", "")
            pane.win.geometry("%dx%d+%d+%d" % (w, h, x, y))
            pane.canvas.configure(bg=cfg["colour"], width=w, height=h)
            pane.canvas.delete("all")
            return

        # The key colour is punched out to transparent, so it must not collide
        # with whatever the user picked for the dot itself.
        key = "#010101" if cfg["colour"].lower() != "#010101" else "#020202"

        pane.win.geometry("%dx%d+%d+%d" % (w, h, x, y))
        pane.canvas.configure(bg=key, width=w, height=h)
        pane.win.attributes("-transparentcolor", key)
        pane.canvas.delete("all")

        if style == "dot":
            pane.canvas.create_oval(2, 2, w - 2, h - 2, fill=cfg["colour"], outline="")
        else:
            pane.canvas.create_text(
                w // 2,
                h // 2,
                text=cfg["message"],
                fill=cfg["colour"],
                font=(overlay_family(pane.canvas), int(cfg["font_size"]),
                      "normal"),
            )

    # -- the pulse ----------------------------------------------------------

    def interrupt(self):
        """Abandon the current pulse so a more important one can take over.

        Used when a break lands on top of a blink: the break is the one the
        user actually needs to see, and two pulses cannot share the screen.
        """
        if self.busy:
            self._release(None)

    def _expected_ms(self, cfg):
        """Longest a healthy pulse can legitimately take, plus slack."""
        per = int(cfg["fade_ms"]) * 2 + int(cfg["hold_ms"]) + int(cfg["gap_ms"])
        # INDICATOR_FLY_MS is spent before the first pane is even drawn.
        return per * max(1, int(cfg["blinks"])) + INDICATOR_FLY_MS + 3000

    def _release(self, why):
        """Unstick the overlay. Reaching this by watchdog means a pulse died
        part-way through and every later reminder would have been dropped."""
        # Bump first: whatever is still scheduled belongs to the pulse that is
        # ending, and must not touch the panes once they are hidden.
        self.pulse_id += 1
        if self.watchdog is not None:
            try:
                self.root.after_cancel(self.watchdog)
            except Exception:
                pass  # already fired or already cancelled; nothing to undo
            self.watchdog = None
        for pane in self.active:
            try:
                pane.hide()
            except Exception:
                pass
        self.active = []
        self.busy = False
        if self.indicator is not None:
            # Reached on the normal path AND by the watchdog, so a pulse that
            # dies part-way can never leave the screen showing nothing.
            self.indicator.fly_out(self.cfg)
        if why:
            log_event("WATCHDOG", why)

    def pulse(self, cfg):
        if self.busy:
            # Before the watchdog existed this was permanent and silent.
            log_event("skipped", "overlay still busy from the previous pulse")
            return
        self.busy = True
        self.cfg = cfg
        self.pulse_id += 1
        mine = self.pulse_id
        if cfg.get("sound_enabled"):
            # Here rather than in fire(), so Preview and the tray's Blink now
            # sound exactly like the real thing.
            play_sound(cfg.get("sound_name", DEFAULTS["sound_name"]),
                       cfg.get("sound_volume", DEFAULTS["sound_volume"]))

        # busy is cleared at the far end of a chain of after-callbacks. If any
        # link raises, that end is never reached, so this is the backstop.
        self.watchdog = self.root.after(
            self._expected_ms(cfg),
            lambda: self._release("pulse never finished; overlay force-released"))

        # The indicator flies to the reminder and hides as it lands, so the two
        # are never on screen together. No indicator means no flight to wait on.
        if self.indicator is not None:
            self.indicator.fly_in(
                cfg, lambda: self._on_gen(mine, lambda: self._show_reminder(cfg)))
        else:
            self._show_reminder(cfg)

    def _on_gen(self, mine, step):
        """Run `step` only if the pulse that scheduled it is still the live one.

        This is the check the whole generation scheme exists for, and for a
        while it was not here: the method took `mine`, ignored it, and called
        step() unconditionally, while three comments elsewhere -- including
        this class's own docstring and _release's -- stated that every link
        checked it. Every caller was already threading the right value through.
        """
        if mine == self.pulse_id:
            step()

    def _show_reminder(self, cfg):
        screens = monitors()
        base_dpi = next((m[4] for m in screens if m[5]), BASE_DPI)
        if not cfg["all_monitors"]:
            screens = [m for m in screens if m[5]] or screens[:1]

        self.active = self._panes_for(len(screens))
        for pane, mon in zip(self.active, screens):
            self._draw(pane, cfg, mon, base_dpi)
            pane.show()
        self._run(int(cfg["blinks"]))

    def _alpha(self, value):
        for pane in self.active:
            pane.alpha(value)

    def _run(self, remaining):
        if remaining <= 0:
            self._release(None)
            return
        self._fade(0.0, float(self.cfg["opacity"]), lambda: self._hold(remaining))

    def _hold(self, remaining):
        mine = self.pulse_id
        self.root.after(
            int(self.cfg["hold_ms"]),
            lambda: self._on_gen(mine, lambda: self._fade(
                float(self.cfg["opacity"]), 0.0, lambda: self._gap(remaining))),
        )

    def _gap(self, remaining):
        if remaining - 1 <= 0:
            self._run(0)
            return
        mine = self.pulse_id
        self.root.after(int(self.cfg["gap_ms"]),
                        lambda: self._on_gen(mine, lambda: self._run(remaining - 1)))

    def _fade(self, start, end, done):
        duration = int(self.cfg["fade_ms"])
        mine = self.pulse_id
        if duration <= 0:
            self._alpha(end)
            done()
            return
        # Driven by the clock, not by counting frames. after(16) is a floor and
        # each step also repaints every pane, so a step count made a 0.55s fade
        # run nearer 0.7s -- every duration in the panel was quietly a lie.
        started = time.monotonic()
        span = duration / 1000.0

        def step():
            # The same generation check as _on_gen, inline because this one
            # reschedules ITSELF every 16ms: without it an abandoned fade keeps
            # writing alpha over whatever pulse replaced it, for the rest of its
            # duration. `mine` was already captured above and already unused.
            if mine != self.pulse_id:
                return
            t = (time.monotonic() - started) / span
            if t >= 1.0:
                self._alpha(end)
                done()
                return
            self._alpha(start + (end - start) * t)
            self.root.after(16, step)

        step()


# --------------------------------------------------------------------------
# Running indicator
# --------------------------------------------------------------------------

INDICATOR_SIZE = 9          # logical px across, before DPI scaling
# A scrollbar lives in this exact corner, so the horizontal inset has to clear
# one (~17 logical px) rather than just look tidy. The vertical inset does not.
INDICATOR_MARGIN_X = 34     # logical px in from the right edge
INDICATOR_MARGIN_Y = 12     # logical px up from the taskbar
INDICATOR_ALPHA = 0.55      # present enough to find, faint enough to forget
INDICATOR_FLY_MS = 380      # corner -> reminder, long enough to register
INDICATOR_RECHECK_MS = 20000

COUNTDOWN_W, COUNTDOWN_H = 52, 20   # logical px
COUNTDOWN_GAP = 8                   # logical px between pill and dot
COUNTDOWN_ALPHA = 0.62
COUNTDOWN_BG = "#0E1420"
COUNTDOWN_FG = "#E6EBF2"


# The screen the OLD pixel-valued dot_size was authored against, kept solely
# so migrate_dot_units can convert a saved pixel count into the percentage
# that replaced it. Nothing in the live geometry reads it.
#
# reminder_rect scales a dot against the screen's SHORT side, not its height:
# on a portrait monitor (1440x3440) a height-based 78% asks for a 2675px dot
# on a 1440px-wide screen, which the clamp would flatten into a full-width
# bar. On every landscape screen the short side IS the height, so the two
# only differ where the height-based answer is wrong.
REFERENCE_SHORT_SIDE = 1080


def reminder_rect(mon, cfg, base_dpi=None):
    """Where a reminder lands on one monitor, as (x, y, w, h).

    The only copy of this arithmetic. There were two: Overlay._draw, which
    paints the reminder, and reminder_centre_on, which the corner dot flies to
    -- the second carrying a comment reading "must match Overlay._draw
    exactly". It already did not. One guarded the DPI baseline with
    `base_dpi or BASE_DPI` and the other with `base or 1`, so on a machine
    whose primary monitor reported a DPI of 0 they disagreed. Only one of the
    two draws anything, so a drift produces no error and no glitch -- just a
    dot that flies to the wrong place. A comment is not an enforcement
    mechanism; a shared function is.

    base_dpi is the primary screen's DPI, looked up if not supplied. It scales
    the MARGIN, which is a physical distance from a bezel and should not grow
    with resolution. The DOT is scaled differently -- it is a percentage of the
    screen's short side -- because what matters for a reminder is how much of
    the view it takes up, not how many millimetres across it is. Scaling the
    dot by DPI too would count the same thing twice.
    """
    mx, my, mw, mh, dpi = mon[0], mon[1], mon[2], mon[3], mon[4]
    if cfg["style"] == "dim":
        return mx, my, mw, mh

    if base_dpi is None:
        base_dpi = next((m[4] for m in monitors() if m[5]), BASE_DPI)
    scale = float(dpi) / float(base_dpi or BASE_DPI)

    if cfg["style"] == "dot":
        w = h = max(4, int(round(int(cfg["dot_pct"]) / 100.0 * min(mw, mh))))
    else:
        fs = int(cfg["font_size"])
        # Cells, not characters. One Chinese character occupies the width of
        # two Latin ones, so counting characters gave 看向遠方 the pane of a
        # four-letter word and cut its ends off.
        w = max(120, fs * (text_cells(cfg["message"]) + 2))
        h = fs * 3

    # Both words are user-editable, and "Look into the distance" at 60pt asks
    # for ~1440px. A pane wider than the screen is not a big reminder, it is a
    # reminder with its ends cut off.
    w, h = min(w, mw), min(h, mh)

    margin = int(round(int(cfg["margin"]) * scale))
    corner = cfg["corner"]
    if corner == "center":
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
    else:
        x = mx + margin if "left" in corner else mx + mw - w - margin
        y = my + margin if "top" in corner else my + mh - h - margin
    return x, y, w, h


def reminder_centre_on(mon, cfg):
    """The centre of where the reminder will appear on one specific monitor.

    Each screen's dot flies to its own screen's reminder, so on a multi-monitor
    desk the dots converge locally instead of all streaming to one screen, and
    they land correctly when Position is a corner rather than Centre.
    """
    x, y, w, h = reminder_rect(mon, cfg)
    return x + w // 2, y + h // 2


def _corner_slot(m):
    """(dot size, dot x, dot y, scale) for one monitor's bottom-right corner."""
    scale = float(m[4]) / float(BASE_DPI or 1)
    size = max(4, int(round(INDICATOR_SIZE * scale)))
    wx, wy, ww, wh = m[6], m[7], m[8], m[9]
    x = wx + ww - size - int(round(INDICATOR_MARGIN_X * scale))
    y = wy + wh - size - int(round(INDICATOR_MARGIN_Y * scale))
    return size, x, y, scale


class _Overlayette(_ClickThroughWindow):
    """The small always-on windows: indicator dots and the countdown pill.

    Only difference from a pane is that these are shown at a chosen opacity
    rather than faded by a pulse.
    """

    def show(self, alpha):
        # Was deiconify-then-style, the ordering _ClickThroughWindow.style_once
        # documents as the focus-theft bug. These windows appear at startup,
        # so getting it wrong stole the foreground once per session.
        self._map()
        self.win.attributes("-alpha", alpha)


class _Pip(_Overlayette):
    """One indicator dot, on one monitor."""

    def __init__(self, root):
        _Overlayette.__init__(self, root)
        self.painted = None

    def paint(self, colour, size):
        if self.painted == (size, colour):
            return
        self.painted = (size, colour)
        key = "#010101" if colour.lower() != "#010101" else "#020202"
        self.canvas.configure(bg=key, width=size, height=size)
        self.win.attributes("-transparentcolor", key)
        self.canvas.delete("all")
        self.canvas.create_oval(0, 0, size - 1, size - 1, fill=colour, outline="")


class RunningIndicator:
    """A small dot above the taskbar of every screen, meaning "this is running".

    Between reminders a tray-only app gives no sign it is alive, which is
    exactly the doubt that started this. The dots answer it continuously and
    are deliberately exclusive with the reminder: hidden for the length of a
    pulse, restored the moment it releases.

    One dot per monitor, and each flies to its own screen's reminder. A dot on
    a screen that is not about to show a reminder simply stays put, so no
    screen is ever left showing neither.

    Drawn with a plain Tk oval rather than a Pillow sprite on purpose. The
    transparent-colour key cannot represent partial alpha, so an antialiased
    edge would key out as a dark fringe; an aliased oval has no blended pixels
    and keys cleanly. At this size the jaggedness is invisible.
    """

    def __init__(self, root):
        self.root = root
        self.cfg = None
        self.pips = []
        self.layout = []
        self.flight = 0        # generation, so a new flight abandons the old
        self.flying = False
        self.parked = False
        self.on_leave = None   # the dots have set off
        self.on_park = None    # the dots are home again
        self.root.after(INDICATOR_RECHECK_MS, self._recheck)

    # -- geometry -----------------------------------------------------------

    def _relayout(self):
        self.layout = [(m,) + _corner_slot(m) for m in monitor_areas()]
        return self.layout

    def _ensure(self, n):
        while len(self.pips) < n:
            self.pips.append(_Pip(self.root))
        for spare in self.pips[n:]:
            spare.hide()
        return self.pips[:n]

    def _movers(self, cfg):
        """Dots on screens that are about to show the reminder."""
        out = []
        for pip, (m, size, x, y, _s) in zip(self.pips, self.layout):
            if not (cfg["all_monitors"] or m[5]):
                continue
            cx, cy = reminder_centre_on(m, cfg)
            out.append((pip, size, x, y, cx - size // 2, cy - size // 2))
        return out

    def _recheck(self):
        """Docking, rotating or resizing a screen moves the corner, and while
        paused no pulse would ever repaint it."""
        try:
            if self.cfg is not None and self.parked and not self.flying:
                self.show()
        except Exception:
            # Runs every 20s. If it starts failing the dots quietly stop
            # coming back, which looks like the app having died.
            log_error("indicator recheck")
        self.root.after(INDICATOR_RECHECK_MS, self._recheck)

    # -- visibility ---------------------------------------------------------

    def apply(self, cfg):
        self.cfg = cfg
        if self.parked and not self.flying:
            self.show()

    def show(self):
        if self.cfg is None:
            return
        try:
            layout = self._relayout()
            for pip, (m, size, x, y, _s) in zip(self._ensure(len(layout)), layout):
                pip.paint(self.cfg["colour"], size)
                pip.move(size, size, x, y)
                pip.show(INDICATOR_ALPHA)
            self.parked = True
            if self.on_park:
                self.on_park()
        except tk.TclError:
            pass

    def hide(self):
        for pip in self.pips:
            pip.hide()
        self.parked = False

    # -- flight -------------------------------------------------------------

    def _animate(self, legs, mine, on_done, on_abandon=None):
        """Move every leg together. Driven by the clock, not a step count:
        after(16) is a floor and each step moves real windows, so counting
        frames stretched a 380ms flight to 560ms.

        A superseded flight stops moving, but it must still hand control back:
        on_abandon is how. Without it, `return` here silently dropped whatever
        the flight was supposed to trigger on arrival -- and for fly_in that is
        Overlay._show_reminder, so a superseded fly-in meant the reminder never
        appeared at all and the overlay stayed busy until the watchdog. It was
        only ever survivable because every path that supersedes a fly-in also
        happened to call Overlay._release, which is an invariant nobody stated
        and nothing enforced.
        """
        started = time.monotonic()
        span = INDICATOR_FLY_MS / 1000.0

        def step():
            if mine != self.flight:
                if on_abandon is not None:
                    on_abandon()
                return
            # on_done is called from exactly one place. Calling it inside the
            # try meant a TclError raised BY on_done landed in the except arm
            # and called it a second time -- which re-entered the overlay and
            # started a second pulse chain on the same panes.
            finished = False
            try:
                t = (time.monotonic() - started) / span
                if t >= 1.0:
                    finished = True
                else:
                    eased = 1.0 - (1.0 - t) ** 3   # quick away, gentle arrival
                    for pip, size, ax, ay, bx, by in legs:
                        pip.move(size, size,
                                 int(round(ax + (bx - ax) * eased)),
                                 int(round(ay + (by - ay) * eased)))
            except tk.TclError:
                finished = True
            if finished:
                self.flying = False
                on_done()
                return
            self.root.after(16, step)

        step()

    def fly_in(self, cfg, done):
        """Glide to the reminder and hand over as the dots land."""
        if self.cfg is None or not self.parked:
            done()
            return
        self._relayout()
        # _movers zips pips against the layout, so a layout longer than the
        # pool silently drops the trailing screens. fly_out already did this.
        self._ensure(len(self.layout))
        legs = self._movers(cfg)
        if not legs:
            done()
            return
        self.parked = False
        if self.on_leave:
            self.on_leave()
        self.flight += 1
        self.flying = True

        def landed():
            for pip, _s, _ax, _ay, _bx, _by in legs:
                pip.hide()
            done()

        # done() on landing OR on abandonment, so it is called exactly once
        # either way. Safe because the overlay guards it with _on_gen: if the
        # pulse that asked for this flight has been superseded, done() runs and
        # correctly does nothing. If it has NOT, the reminder still appears.
        self._animate(legs, self.flight, landed, on_abandon=done)

    def fly_out(self, cfg):
        """Fly home from the reminder, mirroring the way in.

        Teleporting back reads as a second, unrelated dot appearing; travelling
        back reads as the same one returning, which is the whole illusion.
        """
        if self.cfg is None:
            return
        if cfg is None:
            self.show()
            return
        try:
            self._relayout()
            self._ensure(len(self.layout))
            legs = []
            for pip, size, hx, hy, sx, sy in self._movers(cfg):
                # The colour of the reminder being left, not the parked dot's:
                # a dot flying home from a BREAK used to turn amber in mid-air.
                pip.paint(cfg["colour"], size)
                pip.move(size, size, sx, sy)
                pip.show(INDICATOR_ALPHA)
                legs.append((pip, size, sx, sy, hx, hy))
        except tk.TclError:
            return
        if not legs:
            self.show()
            return
        self.flight += 1
        self.flying = True
        self._animate(legs, self.flight, self.show)


class CountdownLabel:
    """Time until the next break, parked just above each indicator dot.

    Its own windows rather than part of the dots', because the dots fly to the
    reminder and the countdown must not travel with them.

    The pill is built from hard-edged shapes so the transparent-colour key has
    no antialiased pixels to fringe. The text is antialiased against the pill
    itself, where the key never reaches it -- which is why the pill exists at
    all rather than bare text over the desktop.
    """

    def __init__(self, root):
        self.root = root
        self.tiles = []
        self.text = None
        self.suppressed = False

    def _ensure(self, n):
        while len(self.tiles) < n:
            self.tiles.append(_Overlayette(self.root))
        for spare in self.tiles[n:]:
            spare.hide()
        return self.tiles[:n]

    def _paint(self, tile, w, h, scale, text):
        key = "#010101"
        tile.canvas.configure(bg=key, width=w, height=h)
        tile.win.attributes("-transparentcolor", key)
        tile.canvas.delete("all")
        r = h // 2
        tile.canvas.create_oval(0, 0, h - 1, h - 1, fill=COUNTDOWN_BG, outline="")
        tile.canvas.create_oval(w - h, 0, w - 1, h - 1, fill=COUNTDOWN_BG, outline="")
        tile.canvas.create_rectangle(r, 0, w - r - 1, h - 1,
                                     fill=COUNTDOWN_BG, outline="")
        # Negative size means pixels, so the pill stays the same physical size
        # on a screen at different scaling instead of being re-scaled twice.
        tile.canvas.create_text(w // 2, h // 2, text=text, fill=COUNTDOWN_FG,
                                font=("Segoe UI", -max(9, int(round(12 * scale)))))

    def set_text(self, text):
        """None hides it -- there is nothing to count down to."""
        self.text = text
        if text is None:
            self.hide()
            return
        if self.suppressed:
            return
        self.render()

    def render(self):
        if self.text is None or self.suppressed:
            return
        try:
            slots = []
            for m in monitor_areas():
                size, dx, dy, scale = _corner_slot(m)
                w = int(round(COUNTDOWN_W * scale))
                h = int(round(COUNTDOWN_H * scale))
                x = dx + size // 2 - w // 2
                y = dy - int(round(COUNTDOWN_GAP * scale)) - h
                slots.append((w, h, x, y, scale))
            for tile, (w, h, x, y, scale) in zip(self._ensure(len(slots)), slots):
                self._paint(tile, w, h, scale, self.text)
                tile.move(w, h, x, y)
                tile.show(COUNTDOWN_ALPHA)
        except tk.TclError:
            pass

    def suppress(self):
        """Hidden while a reminder is on screen, like the dots themselves."""
        self.suppressed = True
        self.hide()

    def resume(self):
        self.suppressed = False
        self.render()

    def hide(self):
        for tile in self.tiles:
            tile.hide()


# --------------------------------------------------------------------------
# Settings window: theme
#
# The panel is a ttk theme parented on "clam", with every visual part supplied
# as a ttk *image element* that Pillow renders at runtime at the display's
# measured DPI. Nothing extra is packaged and nothing is downloaded: this is
# Tcl running inside the interpreter the app already owns, so the exe does not
# grow and there is no second event loop to fight the tray thread.
#
# Two themes are built, blink-light and blink-dark. Which one is used is read
# from the Windows app-theme setting each time the window opens.
# --------------------------------------------------------------------------

PALETTES = {
    "light": {
        "ground": "#F4F5F7", "surface": "#FFFFFF", "inset": "#EDEEF2",
        "hover": "#FAFAFB", "pressed": "#F0F1F4",
        "border": "#E2E4EA", "border_strong": "#CDD1DA", "border_hover": "#B9BFC9",
        "underline": "#8A8F98",
        "text": "#1A1D23", "muted": "#6B7280", "text_disabled": "#A6ACB8",
        "surface_disabled": "#F7F8FA", "border_disabled": "#EAECF0",
        "accent": "#0F6CBD", "accent_hover": "#115EA3", "accent_pressed": "#0C4A78",
        "accent_subtle": "#EBF3FC", "on_accent": "#FFFFFF",
        "knob_off": "#5D6169", "knob_off_hover": "#3D4148",
        "cell_idle": "#C9CDD6", "cell_hover": "#9AA1AE",
        # The support link: a dark yellow leaning orange, deliberately NOT the
        # blue accent, so the one optional thing on the strip does not look
        # like another piece of chrome. Measured against this ground at
        # 4.63:1, which clears WCAG AA for body text; DarkGoldenrod (#B8860B)
        # is the obvious choice and manages only 2.98:1 on white, so it is out.
        "support": "#9A6300", "support_hover": "#7D5000",
        "chip_ring": (0, 0, 0, 31),          # black at 12%
        "chip": "#FFFFFF",                   # selected segment, raised off the track
        "btn_disabled": "#E2E4EA",
        "dark_titlebar": 0,
    },
    "dark": {
        "ground": "#202020", "surface": "#2B2B2B", "inset": "#333333",
        "hover": "#323232", "pressed": "#383838",
        "border": "#3A3A3A", "border_strong": "#4A4A4A", "border_hover": "#5A5A5A",
        "underline": "#9A9A9A",
        "text": "#F2F3F5", "muted": "#A0A6B0", "text_disabled": "#6A7078",
        "surface_disabled": "#292929", "border_disabled": "#343434",
        "accent": "#479EF5", "accent_hover": "#62ABF5", "accent_pressed": "#2886DE",
        "accent_subtle": "#16324D",
        # Near-black, not white: white on #479EF5 is 2.8:1 and fails, and this
        # is what Windows 11's own dark accent buttons do.
        "on_accent": "#101215",
        "knob_off": "#CFCFCF", "knob_off_hover": "#E8E8E8",
        "cell_idle": "#5A5A5A", "cell_hover": "#7A7A7A",
        # The same idea lifted for a dark ground: #9A6300 manages only
        # 1.7:1 on #202020 and would read as mud. 7.28:1 here.
        "support": "#E0A22E", "support_hover": "#EBB047",
        "chip_ring": (255, 255, 255, 46),    # white at 18%
        "chip": "#3F3F3F",                   # selected segment, raised off the track
        "btn_disabled": "#333333",
        "dark_titlebar": 1,
    },
}

FONT_STACKS = {
    "display": ("Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI", "Tahoma"),
    "text": ("Segoe UI Variable Text", "Segoe UI", "Tahoma"),
    "small": ("Segoe UI Variable Small", "Segoe UI", "Tahoma"),
}

SS = 4  # supersample factor: draw at 4x, downsample, so corners antialias

# ttk stretches a 9-sliced image element by TILING its middle strips, not by
# scaling them, so a 4px-wide middle costs thousands of image draws per repaint
# and made the first paint of five cards take nearly two seconds. Every
# stretchable sprite is therefore cut with a middle at least this wide, which
# leaves one or two tiles instead.
STRETCH = 120

# ttk does not own the PhotoImages it draws with. If Python collects one, the
# element renders as nothing at all -- no error, just a blank widget -- so
# every image both themes ever make is kept here for the life of the process.
_THEME_IMAGES = []
_THEME_METRICS = {}   # filled on first theme build: scale, s(), fonts


def app_theme_mode():
    """Windows app-theme setting as "dark" or "light".

    Read on open rather than followed live: the ~40 sprites per theme are baked
    at build time, so repainting on a WM_SETTINGCHANGE would mean regenerating
    all of them under an open window. Flipping the Windows theme while the
    panel is up leaves it as it opened; the next open picks the change up.
    """
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
        ) as key:
            return "light" if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] else "dark"
    except Exception:
        return "light"


def _mix(top, bottom, alpha):
    """Flatten `top` at `alpha` over `bottom`. Tk has no translucent text."""
    a, b = top.lstrip("#"), bottom.lstrip("#")
    out = []
    for i in (0, 2, 4):
        out.append(int(round(int(a[i:i + 2], 16) * alpha
                            + int(b[i:i + 2], 16) * (1 - alpha))))
    return "#%02X%02X%02X" % tuple(out)


def _rgba(colour, alpha):
    """#RRGGBB plus a 0..1 alpha, as the tuple Pillow wants."""
    c = colour.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(round(alpha * 255)))


def _photo(master, im, keep=True):
    """Pillow image -> tk.PhotoImage, via base64 PNG.

    Deliberately not PIL's Tk bridge: that would need a --hidden-import for
    PIL._imagingtk in build.py and would then fail only inside the frozen exe,
    never from source.
    """
    buf = io.BytesIO()
    im.save(buf, "PNG")
    photo = tk.PhotoImage(master=master, data=base64.b64encode(buf.getvalue()))
    if keep:
        _THEME_IMAGES.append(photo)
    return photo


def _sprite(master, w, h, paint, alpha=1.0, keep=True):
    """Render one image element. `paint(draw, W, H, k)` works in 4x space."""
    w, h = max(1, int(w)), max(1, int(h))
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    paint(ImageDraw.Draw(im), w * SS, h * SS, SS)
    if alpha < 1.0:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return _photo(master, im.resize((w, h), Image.LANCZOS), keep)


def _rrect(master, w, h, r, fill=None, outline=None, width=1, ring=None,
           ring_w=0, keep=True):
    """Rounded rectangle, optionally with a focus ring at the outer edge."""
    def paint(d, W, H, k):
        pad = 0
        if ring is not None and ring_w:
            rw = max(1, int(round(ring_w * k)))
            d.rounded_rectangle([rw / 2.0, rw / 2.0, W - 1 - rw / 2.0, H - 1 - rw / 2.0],
                                radius=r * k + rw, outline=ring, width=rw)
            pad = rw + max(1, int(round(k)))
        lw = max(1, int(round(width * k)))
        inset = pad + (lw / 2.0 if outline else 0)
        if fill is None and outline is None:
            return
        d.rounded_rectangle([inset, inset, W - 1 - inset, H - 1 - inset],
                            radius=max(1.0, r * k), fill=fill, outline=outline, width=lw)
    return _sprite(master, w, h, paint, keep=keep)


def _field(master, w, h, r, fill, outline, edge, edge_w, line_w):
    """A Windows 11 TextBox: rounded box with a heavier bottom edge.

    That bottom edge turning accent on focus is the detail that makes an Entry
    read as native rather than as a generic rounded rectangle.
    """
    size = (w * SS, h * SS)
    base = Image.new("RGBA", size, (0, 0, 0, 0))
    lw = max(1, int(round(line_w * SS)))
    ImageDraw.Draw(base).rounded_rectangle(
        [lw / 2.0, lw / 2.0, size[0] - 1 - lw / 2.0, size[1] - 1 - lw / 2.0],
        radius=r * SS, fill=fill, outline=outline, width=lw)
    ew = max(1, int(round(edge_w * SS)))
    bar = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, size[1] - ew, size[0], size[1]], fill=edge)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=r * SS, fill=255)
    base = Image.alpha_composite(
        base, Image.composite(bar, Image.new("RGBA", size, (0, 0, 0, 0)), mask))
    return _photo(master, base.resize((w, h), Image.LANCZOS))


def _chevron(master, size, colour, down=True, thick=1.5):
    def paint(d, W, H, k):
        x0, x1, xm = W * 0.18, W * 0.82, W * 0.5
        y0, y1 = (H * 0.36, H * 0.64) if down else (H * 0.64, H * 0.36)
        d.line([(x0, y0), (xm, y1), (x1, y0)], fill=colour,
               width=max(1, int(round(thick * k))), joint="curve")
    return _sprite(master, size, size, paint)


def _arrow(master, size, colour, right=True, thick=1.5):
    """Disclosure chevron: points right when shut, down when open."""
    def paint(d, W, H, k):
        w = max(1, int(round(thick * k)))
        pts = ([(W * 0.36, H * 0.20), (W * 0.66, H * 0.5), (W * 0.36, H * 0.80)]
               if right else
               [(W * 0.20, H * 0.38), (W * 0.5, H * 0.66), (W * 0.80, H * 0.38)])
        d.line(pts, fill=colour, width=w, joint="curve")
    return _sprite(master, size, size, paint, keep=False)


def _picker_face(master, w, h, colour, thick=1.5):
    """A globe at the left and a chevron at the right, in one image.

    Drawn as a single sprite because a ttk button takes one image, and the
    two marks belong at opposite ends with the label between them. The
    button uses compound="center", so ttk draws the text over the middle of
    this and the transparent gap is where it lands.

    The globe is there because the picker has to be recognisable to someone
    who cannot read the language it is currently showing -- which is the
    whole population it exists for.
    """
    def paint(d, W, H, k):
        line = max(1, int(round(thick * k)))
        r = H * 0.44                       # globe radius, vertically centred
        cx, cy = r + line, H / 2.0
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=line)
        d.line([(cx - r, cy), (cx + r, cy)], fill=colour, width=line)
        # One meridian, drawn as a narrow ellipse: at this size a second one
        # turns the globe into a smudge.
        d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
                  outline=colour, width=line)
        # The chevron, right-aligned, same shape as _arrow's downward form.
        cw = H * 0.34
        rx = W - line - cw * 2
        d.line([(rx, cy - cw * 0.35), (rx + cw, cy + cw * 0.45),
                (rx + cw * 2, cy - cw * 0.35)],
               fill=colour, width=line, joint="curve")
    return _sprite(master, w, h, paint, keep=False)


def _switch(master, s, pal, on, hover=False, pressed=False, focus=False, alpha=1.0):
    """The Fluent pill toggle. The off-knob is a solid mid-grey on purpose: a
    pale one reads as disabled rather than as off."""
    def paint(d, W, H, k):
        pad, tw, th = s(4) * k, s(40) * k, s(20) * k
        x0, y0 = pad, pad
        x1, y1 = x0 + tw, y0 + th
        r = th / 2.0
        if on:
            d.rounded_rectangle([x0, y0, x1, y1], radius=r,
                                fill=pal["accent_hover"] if hover else pal["accent"])
            knob, kd = pal["on_accent"], s(14) * k
            cx = x1 - s(4) * k - kd / 2.0
        else:
            d.rounded_rectangle([x0, y0, x1, y1], radius=r,
                                fill=pal["hover"] if hover else pal["inset"],
                                outline=pal["underline"],
                                width=max(1, int(round(s(1) * k))))
            knob = pal["knob_off_hover"] if hover else pal["knob_off"]
            kd = s(12) * k
            cx = x0 + s(4) * k + kd / 2.0
        cy = (y0 + y1) / 2.0
        kw, kh = (s(16) * k, s(12) * k) if pressed else (kd, kd)
        d.rounded_rectangle([cx - kw / 2.0, cy - kh / 2.0, cx + kw / 2.0, cy + kh / 2.0],
                            radius=kh / 2.0, fill=knob)
        if focus:
            o = s(2) * k
            d.rounded_rectangle([x0 - o, y0 - o, x1 + o, y1 + o], radius=r + o,
                                outline=pal["accent"],
                                width=max(1, int(round(s(2) * k))))
    return _sprite(master, s(48), s(28), paint, alpha)


def _transparent(master, w, h):
    return _photo(master, Image.new("RGBA", (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0)))


def _resolve_fonts(root):
    have = set(tkfont.families(root))
    # The language's own families first. Segoe UI Variable has no CJK at all,
    # so on a Chinese UI every one of these three stacks has to be answered by
    # Microsoft JhengHei before it is answered by a Latin font that would draw
    # the whole panel as tofu boxes.
    first = LANGUAGE_FONTS.get(language_code(), ())

    def fam(kind):
        for name in first + FONT_STACKS[kind]:
            if name in have:
                return name
        return "Tahoma"

    disp, text, small = fam("display"), fam("text"), fam("small")
    # Sizes stay in POINTS. Tk already scales points against the reported DPI,
    # so multiplying a font size by the DPI scale would apply it twice.
    return {
        "t1": (disp, 15), "t2": (small, 10), "t3": (text, 10, "bold"),
        # A card title at 10 was smaller than the 11pt row labels beneath it,
        # so the cards read as lists rather than as titled sections.
        "t3l": (disp, 13, "bold"),
        "t4": (text, 11), "t4b": (text, 11, "bold"), "t5": (small, 9),
        # For the support link, which is bold so it reads as the one optional
        # thing on the strip rather than as another row label. Tk takes style
        # words in a font tuple, so the hover underline costs nothing and stays
        # in the theme rather than a widget poking at its own font.
        "t4u": (text, 11, "underline"),
        "t4bu": (text, 11, "bold", "underline"),
        "t4s": (text, 10), "t4sb": (text, 10, "bold"),
    }


def _theme_surfaces(root, st, pal, s, f):
    """Theme elements: flat frames and the rounded card background."""
    st.configure("TFrame", background=pal["surface"])
    st.configure("Ground.TFrame", background=pal["ground"])
    st.configure("Rule.TFrame", background=pal["border"])

    CR = s(8)
    st.element_create(
        "Card.bg", "image",
        _rrect(root, CR * 2 + s(STRETCH), CR * 2 + s(STRETCH), CR,
               fill=pal["surface"], outline=pal["border"], width=s(1)),
        border=CR, sticky="nsew")
    st.layout("Card.TFrame", [("Card.bg", {"sticky": "nsew"})])


def _theme_text(root, st, pal, s, f):
    """Theme elements: every label style."""
    t1, t2, t4, t4b, t5, t3l, t4bu = f["t1"], f["t2"], f["t4"], f["t4b"], f["t5"], f["t3l"], f["t4bu"]

    for name, font, fg, bg in (
        ("TLabel", t4, pal["text"], pal["surface"]),
        ("Title.TLabel", t1, pal["text"], pal["ground"]),
        ("Sub.TLabel", t2, pal["muted"], pal["ground"]),
        ("CardTitle.TLabel", t3l, pal["text"], pal["surface"]),
        ("Row.TLabel", t4, pal["text"], pal["surface"]),
        ("Hint.TLabel", t5, pal["muted"], pal["surface"]),
        ("Cap.TLabel", t2, pal["muted"], pal["surface"]),
        ("Pct.TLabel", t4, pal["accent"], pal["surface"]),
        # On the ground, not a card: the only link in the app sits in the
        # window's footer band. Accent-coloured and underlined only on hover,
        # which is what a Fluent hyperlink does.
        ("Link.TLabel", t4b, pal["support"], pal["ground"]),
        ("LinkHover.TLabel", t4bu, pal["support_hover"], pal["ground"]),
    ):
        st.configure(name, font=font, foreground=fg, background=bg)
        st.map(name, foreground=[("disabled", pal["text_disabled"])])


def _theme_fields(root, st, pal, s, f):
    """Theme elements: Entry and Spinbox, which share one chrome."""
    FH, FR = s(32), s(6)
    fw = FR * 2 + s(STRETCH)

    def field(fill, outline, edge, edge_w=1.5):
        return _field(root, fw, FH, FR, fill, outline, edge, s(edge_w), s(1))

    st.element_create(
        "Fld.bg", "image",
        field(pal["surface"], pal["border_strong"], pal["underline"]),
        ("disabled", field(pal["surface_disabled"], pal["border_disabled"],
                           pal["border_disabled"])),
        ("focus", field(pal["surface"], pal["border_strong"], pal["accent"], 2)),
        ("hover", field(pal["hover"], pal["border_hover"], pal["underline"])),
        border=FR, sticky="nsew", padding=(s(10), s(4)))

    st.layout("TEntry", [("Fld.bg", {"sticky": "nsew", "children": [
        ("Entry.padding", {"sticky": "nsew", "children": [
            ("Entry.textarea", {"sticky": "nsew"})]})]})])
    st.configure("TEntry", foreground=pal["text"], fieldbackground=pal["surface"],
                 insertcolor=pal["text"], selectbackground=pal["accent"],
                 selectforeground=pal["on_accent"])
    st.map("TEntry", foreground=[("disabled", pal["text_disabled"])])

    # Two chevrons stack inside a 32-high field, so each gets 10 logical px.
    AR = s(10)
    rest = _rgba(pal["muted"], 0.55)
    up_n, dn_n = (_chevron(root, AR, rest, False, s(1.3)),
                  _chevron(root, AR, rest, True, s(1.3)))
    up_h, dn_h = (_chevron(root, AR, pal["muted"], False, s(1.3)),
                  _chevron(root, AR, pal["muted"], True, s(1.3)))
    up_a, dn_a = (_chevron(root, AR, pal["accent"], False, s(1.4)),
                  _chevron(root, AR, pal["accent"], True, s(1.4)))
    up_d, dn_d = (_chevron(root, AR, pal["text_disabled"], False, s(1.3)),
                  _chevron(root, AR, pal["text_disabled"], True, s(1.3)))
    st.element_create("Sp.up", "image", up_n, ("disabled", up_d), ("pressed", up_a),
                      ("active", up_h), ("hover", up_h),
                      sticky="e", padding=(0, 0, s(7), 0))
    st.element_create("Sp.down", "image", dn_n, ("disabled", dn_d), ("pressed", dn_a),
                      ("active", dn_h), ("hover", dn_h),
                      sticky="e", padding=(0, 0, s(7), 0))
    st.layout("TSpinbox", [("Fld.bg", {"sticky": "nsew", "children": [
        ("null", {"side": "right", "sticky": "ns", "children": [
            ("Sp.up", {"side": "top", "sticky": "e"}),
            ("Sp.down", {"side": "bottom", "sticky": "e"})]}),
        ("Spinbox.padding", {"sticky": "nsew", "children": [
            ("Spinbox.textarea", {"sticky": "nsew"})]})]})])
    st.configure("TSpinbox", foreground=pal["text"], fieldbackground=pal["surface"],
                 insertcolor=pal["text"], selectbackground=pal["accent"],
                 selectforeground=pal["on_accent"])
    st.map("TSpinbox", foreground=[("disabled", pal["text_disabled"])])


def _theme_buttons(root, st, pal, s, f):
    """Theme elements: primary, secondary and the link-ish ones."""
    t3, t4, t4b = f["t3"], f["t4"], f["t4b"]

    BH, BR = s(32), s(6)
    bw = BR * 2 + s(STRETCH)

    def btn(fill, outline=None, ring=False):
        return _rrect(root, bw, BH, BR, fill=fill, outline=outline, width=s(1),
                      ring=pal["accent"] if ring else None, ring_w=s(2) if ring else 0)

    st.element_create(
        "Pri.bg", "image", btn(pal["accent"]),
        ("disabled", btn(pal["btn_disabled"])),
        ("pressed", btn(pal["accent_pressed"])),
        ("focus", "active", btn(pal["accent_hover"], ring=True)),
        ("focus", btn(pal["accent"], ring=True)),
        ("active", btn(pal["accent_hover"])),
        border=BR, sticky="nsew", padding=(s(16), s(4)))
    st.layout("Primary.TButton", [("Pri.bg", {"sticky": "nsew", "children": [
        ("Button.padding", {"sticky": "nsew", "children": [
            ("Button.label", {"sticky": "nsew"})]})]})])
    st.configure("Primary.TButton", foreground=pal["on_accent"], anchor="center",
                 font=t4b)
    st.map("Primary.TButton", foreground=[("disabled", pal["text_disabled"])])

    st.element_create(
        "Sec.bg", "image", btn(pal["surface"], pal["border_strong"]),
        ("disabled", btn(pal["surface_disabled"], pal["border_disabled"])),
        ("pressed", btn(pal["pressed"], pal["border_hover"])),
        ("focus", "active", btn(pal["hover"], pal["border_hover"], ring=True)),
        ("focus", btn(pal["surface"], pal["border_strong"], ring=True)),
        ("active", btn(pal["hover"], pal["border_hover"])),
        border=BR, sticky="nsew", padding=(s(16), s(4)))
    st.layout("Secondary.TButton", [("Sec.bg", {"sticky": "nsew", "children": [
        ("Button.padding", {"sticky": "nsew", "children": [
            ("Button.label", {"sticky": "nsew"})]})]})])
    st.configure("Secondary.TButton", foreground=pal["text"], anchor="center", font=t4)
    st.map("Secondary.TButton", foreground=[("disabled", pal["text_disabled"])])

    # Ghost: the Advanced timing disclosure. No fill until you touch it.
    st.element_create(
        "Ghost.bg", "image", _transparent(root, bw, BH),
        ("pressed", btn(pal["pressed"])),
        ("focus", "active", btn(pal["inset"], ring=True)),
        ("focus", _rrect(root, bw, BH, BR, ring=pal["accent"], ring_w=s(2))),
        ("active", btn(pal["inset"])),
        border=BR, sticky="nsew", padding=(s(8), s(4)))
    st.layout("Ghost.TButton", [("Ghost.bg", {"sticky": "nsew", "children": [
        ("Button.padding", {"sticky": "nsew", "children": [
            ("Button.label", {"sticky": "w"})]})]})])
    st.configure("Ghost.TButton", foreground=pal["text"], anchor="w", font=t3,
                 background=pal["surface"])
    st.map("Ghost.TButton", foreground=[("disabled", pal["text_disabled"])])


def _theme_segmented(root, st, pal, s, f):
    """Theme elements: the two- and three-way pickers."""
    t4, t4b = f["t4"], f["t4b"]

    TR = s(8)
    tw, th = TR * 2 + s(STRETCH), TR * 2 + s(40)
    st.element_create(
        "Track.bg", "image",
        _rrect(root, tw, th, TR, fill=pal["inset"], outline=pal["border"], width=s(1)),
        border=TR, sticky="nsew")
    st.layout("Track.TFrame", [("Track.bg", {"sticky": "nsew"})])
    st.element_create(
        "TrackFocus.bg", "image",
        _rrect(root, tw, th, TR, fill=pal["inset"], outline=pal["border"], width=s(1),
               ring=pal["accent"], ring_w=s(2)),
        border=TR, sticky="nsew")
    st.layout("TrackFocus.TFrame", [("TrackFocus.bg", {"sticky": "nsew"})])

    SR = s(6)
    sw = SR * 2 + s(STRETCH)
    st.element_create(
        "Seg.bg", "image", _transparent(root, sw, s(26)),
        ("selected", _rrect(root, sw, s(26), SR, fill=pal["chip"],
                            outline=_mix(pal["border_strong"], pal["chip"], 0.6),
                            width=s(1))),
        border=SR, sticky="nsew", padding=(s(4), 0))
    for name, font, fg in (
        ("Seg.TRadiobutton", t4, pal["muted"]),
        ("SegOn.TRadiobutton", t4b, pal["text"]),
        ("SegSm.TRadiobutton", f["t4s"], pal["muted"]),
        ("SegSmOn.TRadiobutton", f["t4sb"], pal["text"]),
        # "Custom" is normally a result rather than a choice, so it sits back.
        ("SegDim.TRadiobutton", f["t4s"], _mix(pal["muted"], pal["inset"], 0.7)),
    ):
        st.layout(name, [("Seg.bg", {"sticky": "nsew", "children": [
            ("Radiobutton.padding", {"sticky": "nsew", "children": [
                ("Radiobutton.label", {"sticky": "nsew"})]})]})])
        st.configure(name, font=font, foreground=fg, anchor="center", padding=0,
                     background=pal["inset"], focuscolor=pal["inset"])
        st.map(name,
               foreground=[("disabled", pal["text_disabled"]),
                           ("selected", pal["text"]), ("active", pal["text"])],
               background=[("!disabled", pal["inset"])])


def _theme_grid(root, st, pal, s, f):
    """Theme elements: the position picker's miniature monitor."""
    PW, PH = s(88), s(58)

    def screen(ring=False):
        def paint(d, W, H, k):
            o = s(2) * k
            if ring:
                rw = max(1, int(round(s(2) * k)))
                d.rounded_rectangle([rw / 2.0, rw / 2.0, W - 1 - rw / 2.0,
                                     H - 1 - rw / 2.0],
                                    radius=s(8) * k, outline=pal["accent"], width=rw)
            lw = max(1, int(round(s(1) * k)))
            d.rounded_rectangle([o + lw / 2.0, o + lw / 2.0,
                                 W - 1 - o - lw / 2.0, H - 1 - o - lw / 2.0],
                                radius=s(6) * k, fill=pal["inset"],
                                outline=pal["border_strong"], width=lw)
        return _sprite(root, PW, PH, paint)

    st.element_create("Screen.bg", "image", screen(), border=s(12), sticky="nsew")
    st.layout("Screen.TFrame", [("Screen.bg", {"sticky": "nsew"})])
    st.element_create("ScreenFocus.bg", "image", screen(True), border=s(12),
                      sticky="nsew")
    st.layout("ScreenFocus.TFrame", [("ScreenFocus.bg", {"sticky": "nsew"})])

    CS = s(12)

    def cell(fill):
        return _rrect(root, CS, CS, s(3), fill=fill)

    st.element_create("Cell.bg", "image", cell(pal["cell_idle"]),
                      ("disabled", cell(pal["border_disabled"])),
                      ("selected", cell(pal["accent"])),
                      ("active", cell(pal["cell_hover"])),
                      sticky="nsew")
    st.layout("Cell.TRadiobutton", [("Cell.bg", {"sticky": "nsew"})])
    st.configure("Cell.TRadiobutton", background=pal["inset"], padding=0)
    st.map("Cell.TRadiobutton", background=[("!disabled", pal["inset"])])


def _theme_toggles(root, st, pal, s, f):
    """Theme elements: the on/off switches."""
    t4 = f["t4"]

    st.element_create(
        "Sw.ind", "image", _switch(root, s, pal, False),
        ("disabled", "selected", _switch(root, s, pal, True, alpha=0.4)),
        ("disabled", _switch(root, s, pal, False, alpha=0.4)),
        ("selected", "pressed", _switch(root, s, pal, True, pressed=True)),
        ("selected", "focus", "active",
         _switch(root, s, pal, True, hover=True, focus=True)),
        ("selected", "focus", _switch(root, s, pal, True, focus=True)),
        ("selected", "active", _switch(root, s, pal, True, hover=True)),
        ("selected", _switch(root, s, pal, True)),
        ("pressed", _switch(root, s, pal, False, pressed=True)),
        ("focus", "active", _switch(root, s, pal, False, hover=True, focus=True)),
        ("focus", _switch(root, s, pal, False, focus=True)),
        ("active", _switch(root, s, pal, False, hover=True)),
        sticky="e")
    # Two backgrounds, one switch: the card version sits on a card, the ground
    # version sits on the header band beside the page title. The sprite itself
    # is transparent outside the pill, so only the label's fill differs.
    for name, bg in (("Switch.TCheckbutton", pal["surface"]),
                     ("SwitchGround.TCheckbutton", pal["ground"])):
        st.layout(name, [
            ("Checkbutton.padding", {"sticky": "nsew", "children": [
                ("Checkbutton.label", {"side": "left", "sticky": "w"}),
                ("Sw.ind", {"side": "right", "sticky": "e"})]})])
        st.configure(name, background=bg, foreground=pal["text"], font=t4,
                     padding=0, focuscolor=bg)
        st.map(name, background=[("active", bg)],
               foreground=[("disabled", pal["text_disabled"])])


def _build_theme(root, st, pal, s):
    """Every element of one theme. Runs once per mode.

    Was 253 lines in a row. The sections below were already marked with
    banner comments and shared nothing but the fonts dict, so each is now
    its own function and this one is the running order.
    """
    f = _THEME_METRICS["fonts"]

    st.configure(".", background=pal["surface"], foreground=pal["text"],
                 font=f["t4"], borderwidth=0, relief="flat",
                 focuscolor=pal["accent"])

    _theme_surfaces(root, st, pal, s, f)
    _theme_text(root, st, pal, s, f)
    _theme_fields(root, st, pal, s, f)
    _theme_buttons(root, st, pal, s, f)
    _theme_segmented(root, st, pal, s, f)
    _theme_grid(root, st, pal, s, f)
    _theme_toggles(root, st, pal, s, f)


def ensure_theme(root, mode):
    """Build blink-<mode>-<language> once, then select it.

    theme_create raises TclError "Theme ... already exists" on a second call,
    so this guard is the only path allowed to build one.

    The language is in the theme's NAME because a theme bakes its fonts into
    forty image elements at build time. Switching to Chinese changes which
    family every one of those was drawn with, and a theme cannot be rebuilt
    under an open window -- so each language gets its own, built the first
    time it is asked for and kept.

    A ttk theme is global to the Tcl interpreter, so it restyles every ttk
    widget in the process. Today ttk lives only in SettingsWindow and the
    overlay is plain tk, so that is safe -- but any future ttk widget anywhere
    in this app inherits this look.
    """
    name = "blink-" + mode + "-" + language_code()
    st = ttk.Style(root)
    if not _THEME_METRICS:
        scale = root.winfo_fpixels("1i") / 96.0
        _THEME_METRICS["scale"] = scale
        _THEME_METRICS["s"] = lambda v: max(1, int(round(v * scale)))
    # Re-resolved when the language changes, and only then: the fonts are what
    # differ between two themes of the same mode.
    if _THEME_METRICS.get("lang") != language_code():
        _THEME_METRICS["lang"] = language_code()
        _THEME_METRICS["fonts"] = _resolve_fonts(root)
    if name not in st.theme_names():
        st.theme_use("clam")   # the one stock theme that gives up every element
        st.theme_create(name, parent="clam")
        st.theme_use(name)
        _build_theme(root, st, PALETTES[mode], _THEME_METRICS["s"])
    st.theme_use(name)
    return name


# --------------------------------------------------------------------------
# Settings window: the four controls ttk cannot draw
# --------------------------------------------------------------------------


class _StateAware:
    """Lets ttk's state= reach a custom widget's own enable/disable.

    These widgets are drawn by hand, so ttk has no idea how to grey them out;
    without this, `w.configure(state="disabled")` would either be ignored or
    raise, depending on the base class. The group-enabling code in
    SettingsWindow drives everything through state=, so each custom widget
    has to translate it into its own set_enabled.

    A mixin rather than a base class because the two widgets that need it
    descend from different Tk classes -- ttk.Frame and tk.Canvas -- and this
    was previously solved by pasting the same eight lines into both.
    """

    def configure(self, cnf=None, **kw):
        if "state" in kw:
            self.set_enabled(str(kw.pop("state")) != "disabled")
            if cnf is None and not kw:
                return None
        return super().configure(cnf, **kw)

    config = configure


class _Segmented(_StateAware, ttk.Frame):
    """A radio group that looks like a Windows 11 segmented control.

    This exists so the panel contains no ttk.Combobox. A Combobox drops a raw
    tk Listbox popdown that no ttk theme can reach, and it was the one widget
    that would still have looked ten years old.
    """

    # A ttk.Frame has no -state, so configure(state=...) used to raise TclError
    # and be swallowed: every "greyed" segmented control was still fully live
    # and fully black. Class level so the overrides below are safe to call
    # before __init__ has run.
    enabled = True

    def __init__(self, parent, s, values, variable, width, height,
                 command=None, small=False, dim=()):
        super().__init__(parent, style="Track.TFrame", takefocus=False)
        self.pw, self.ph = s(width), s(height)
        self.var, self.command = variable, command
        self.base = "SegSm.TRadiobutton" if small else "Seg.TRadiobutton"
        self.on = "SegSmOn.TRadiobutton" if small else "SegOn.TRadiobutton"
        self.dim = set(dim)
        self.values = list(values)
        self.buttons = []

        inset = s(3)
        span = self.pw - 2 * inset
        for i, value in enumerate(self.values):
            x0 = inset + round(span * i / len(self.values))
            x1 = inset + round(span * (i + 1) / len(self.values))
            rb = ttk.Radiobutton(self, text=value, value=value, variable=variable,
                                 style=self.base, command=self._clicked,
                                 takefocus=(i == 0))
            rb.place(x=x0, y=inset, width=x1 - x0, height=self.ph - 2 * inset)
            rb.bind("<FocusIn>", self._focus_in)
            rb.bind("<FocusOut>", self._focus_out)
            rb.bind("<Left>", lambda e: self._step(-1))
            rb.bind("<Right>", lambda e: self._step(1))
            rb.bind("<Home>", lambda e: self._goto(0))
            rb.bind("<End>", lambda e: self._goto(len(self.values) - 1))
            self.buttons.append(rb)
        variable.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    # -- enabling: a Frame has no -state, so the group forwards it ----------

    def set_enabled(self, on):
        """Grey every segment and stop responding. The panel's greying contract."""
        self.enabled = bool(on)
        state = "normal" if self.enabled else "disabled"
        for rb in self.buttons:
            rb.configure(state=state)

    def cget(self, key):
        # The tab ring and the tests ask widgets for their state; answer for
        # the group rather than raising, so a disabled group is skipped.
        if key == "state":
            return "normal" if self.enabled else "disabled"
        return super().cget(key)

    __getitem__ = cget

    # Only one button is a tab stop; the arrows move within the group, which is
    # how a real segmented control behaves.
    def _focus_in(self, _e):
        self.configure(style="TrackFocus.TFrame")

    def _focus_out(self, _e):
        self.configure(style="Track.TFrame")

    def focus_target(self):
        for rb, value in zip(self.buttons, self.values):
            if value == self.var.get():
                return rb
        return self.buttons[0]

    def _step(self, delta):
        if not self.enabled:
            return "break"
        try:
            i = self.values.index(self.var.get())
        except ValueError:
            i = 0
        return self._goto(max(0, min(len(self.values) - 1, i + delta)))

    def _goto(self, i):
        if not self.enabled:
            return "break"
        self.var.set(self.values[i])
        self._clicked()
        return "break"

    def _clicked(self):
        if not self.enabled:
            return
        self.refresh()
        if self.command:
            self.command()

    def refresh(self):
        if not self.winfo_exists():
            return
        current = self.var.get()
        for rb, value in zip(self.buttons, self.values):
            if value == current:
                style = self.on
            elif value in self.dim:
                style = "SegDim.TRadiobutton"
            else:
                style = self.base
            # style only; the disabled state flag set by set_enabled survives.
            rb.configure(style=style)
        # Keep the one tab stop on the selected segment, so tabbing in lands
        # where the eye already is.
        for i, rb in enumerate(self.buttons):
            rb.configure(takefocus=(self.values[i] == current))


class _PositionGrid(ttk.Frame):
    """A miniature screen with five hit targets, instead of a Position dropdown.

    Where the reminder lands is spatial information, so a picture of a screen
    says it faster than a list of words does -- and it removes the last
    Combobox from the panel.
    """

    # (label, column, row) on the 3x3 grid, in tab-ish reading order
    CELLS = [
        ("Top left", 0, 0), ("Top right", 2, 0), ("Centre", 1, 1),
        ("Bottom left", 0, 2), ("Bottom right", 2, 2),
    ]

    def __init__(self, parent, s, variable, command=None):
        super().__init__(parent, style="Screen.TFrame", takefocus=True)
        self.pw, self.ph = s(88), s(58)
        self.var, self.command = variable, command
        self.cells = {}
        xs = {0: s(10), 1: s(38), 2: s(66)}
        ys = {0: s(10), 1: s(23), 2: s(36)}
        for label, col, row in self.CELLS:
            rb = ttk.Radiobutton(self, value=label, variable=variable,
                                 style="Cell.TRadiobutton", takefocus=False,
                                 command=self._clicked)
            rb.place(x=xs[col], y=ys[row], width=s(12), height=s(12))
            rb.bind("<Button-1>", lambda e: self.focus_set(), add="+")
            self.cells[label] = (rb, col, row)
        self.bind("<FocusIn>", lambda e: self.configure(style="ScreenFocus.TFrame"))
        self.bind("<FocusOut>", lambda e: self.configure(style="Screen.TFrame"))
        for key, dx, dy in (("<Left>", -1, 0), ("<Right>", 1, 0),
                            ("<Up>", 0, -1), ("<Down>", 0, 1)):
            self.bind(key, lambda e, a=dx, b=dy: self._move(a, b))
        self.bind("<Button-1>", lambda e: self.focus_set())

    def widgets(self):
        return [rb for rb, _, _ in self.cells.values()]

    def _clicked(self):
        if self.command:
            self.command()

    def _move(self, dx, dy):
        """Nearest cell in that direction; the centre is reachable from any edge."""
        here = self.cells.get(self.var.get())
        if here is None:
            return "break"
        _, col, row = here
        best, score = None, None
        for label, (rb, c, r) in self.cells.items():
            if str(rb.cget("state")) == "disabled":
                continue
            step = (c - col) * dx + (r - row) * dy
            if step <= 0:
                continue
            drift = abs((c - col) * dy) + abs((r - row) * dx)
            rank = (drift, step)
            if score is None or rank < score:
                best, score = label, rank
        if best is not None:
            self.var.set(best)
            self._clicked()
        return "break"


class _Slider(_StateAware, tk.Canvas):
    """Filled-track slider with a Fluent thumb. ttk.Scale has no filled portion
    and no element to add one, so this is a Canvas.

    Exactly three thumb sprites and one ring sprite are rendered, once, and
    then moved with coords(). Re-rendering an image per pixel of drag is how
    the canvas prototype leaked several megabytes on a single sweep.
    """

    # A Canvas's own -state does nothing to widget-level bindings, so a
    # "disabled" slider still dragged and still painted its accent fill.
    enabled = True

    def __init__(self, parent, s, pal, variable, lo, hi, width, height, command):
        self.W, self.H = s(width), s(height)
        super().__init__(parent, width=self.W, height=self.H, bd=0,
                         highlightthickness=0, bg=pal["surface"],
                         cursor="hand2", takefocus=True)
        self.pal = pal
        self.var, self.lo, self.hi, self.command = variable, lo, hi, command
        self.pad = s(9)
        thick = s(4)
        cy = self.H / 2.0

        # These sprites live on the widget, not in the module keep-list: the
        # panel is rebuilt on every open and they must not accumulate.
        self.ring = _rrect(self, self.W, self.H, s(6),
                           ring=pal["accent"], ring_w=s(2), keep=False)
        self.thumbs = {
            "rest": self._thumb(s, pal, s(8)),
            "hover": self._thumb(s, pal, s(10)),
            "press": self._thumb(s, pal, s(7)),
            # The greyed thumb. Without it a disabled slider kept an accent
            # thumb on a grey track, which reads as half-broken rather than off.
            "off": self._thumb(s, pal, s(8), pal["text_disabled"]),
        }
        self.create_line(self.pad, cy, self.W - self.pad, cy, width=thick,
                         fill=pal["inset"], capstyle="round", tags="track")
        self.create_line(self.pad, cy, self.pad, cy, width=thick,
                         fill=pal["accent"], capstyle="round", tags="fill")
        self.create_image(0, 0, image=self.ring, anchor="nw", state="hidden",
                          tags="ring")
        self.create_image(self.pad, cy, image=self.thumbs["rest"], tags="thumb")

        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", lambda e: self._thumb_state("hover"))
        self.bind("<Leave>", lambda e: self._thumb_state("rest"))
        self.bind("<FocusIn>", lambda e: self.itemconfigure("ring", state="normal"))
        self.bind("<FocusOut>", lambda e: self.itemconfigure("ring", state="hidden"))
        for key, step in (("<Left>", -0.01), ("<Right>", 0.01),
                          ("<Shift-Left>", -0.05), ("<Shift-Right>", 0.05),
                          ("<Prior>", 0.10), ("<Next>", -0.10)):
            self.bind(key, lambda e, d=step: self._nudge(d))
        self.bind("<Home>", lambda e: self._set(self.lo))
        self.bind("<End>", lambda e: self._set(self.hi))
        self._hover = "rest"
        self.redraw()

    def _thumb(self, s, pal, core, accent=None):
        d = s(20)
        accent = accent or pal["accent"]

        def paint(dr, W, H, k):
            r = s(9) * k
            cx = cy = W / 2.0
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pal["surface"],
                       outline=accent, width=max(1, int(round(s(1.5) * k))))
            c = core * k / 2.0
            dr.ellipse([cx - c, cy - c, cx + c, cy + c], fill=accent)
        return _sprite(self, d, d, paint, keep=False)

    def _x(self, value):
        span = max(1, self.W - 2 * self.pad)
        frac = (float(value) - self.lo) / (self.hi - self.lo)
        return self.pad + max(0.0, min(1.0, frac)) * span

    def _thumb_state(self, name):
        if not self.enabled:
            return
        self._hover = name
        self.itemconfigure("thumb", image=self.thumbs[name])

    def _from_x(self, x):
        span = max(1, self.W - 2 * self.pad)
        frac = max(0.0, min(1.0, (x - self.pad) / span))
        return self.lo + frac * (self.hi - self.lo)

    # -- enabling ----------------------------------------------------------

    def set_enabled(self, on):
        self.enabled = bool(on)
        tk.Canvas.configure(self, cursor="hand2" if self.enabled else "",
                            takefocus=bool(self.enabled))
        self.itemconfigure("fill", fill=self.pal["accent"] if self.enabled
                           else self.pal["border_disabled"])
        self.itemconfigure("thumb",
                           image=self.thumbs["rest" if self.enabled else "off"])

    def cget(self, key):
        if key == "state":
            return "normal" if self.enabled else "disabled"
        return super().cget(key)

    __getitem__ = cget

    def _press(self, event):
        if not self.enabled:
            return
        self.focus_set()
        self._thumb_state("press")
        self._set(self._from_x(event.x))

    def _drag(self, event):
        if not self.enabled:
            return
        self._set(self._from_x(event.x))

    def _release(self, _event):
        if not self.enabled:
            return
        self._thumb_state("hover")

    def _nudge(self, delta):
        if not self.enabled:
            return "break"
        return self._set(self.var.get() + delta)

    def _set(self, value):
        if not self.enabled:
            return "break"
        value = round(max(self.lo, min(self.hi, float(value))), 3)
        if value != self.var.get():
            self.var.set(value)
        self.redraw()
        if self.command:
            self.command(value)
        return "break"

    def redraw(self):
        cy = self.H / 2.0
        x = self._x(self.var.get())
        self.coords("fill", self.pad, cy, x, cy)
        self.coords("thumb", x, cy)


class _Link(ttk.Label):
    """A text hyperlink. ttk has no such widget.

    A Button was the obvious alternative and is the wrong one: in a footer that
    already ends in Cancel and Save, a third button reads as a third thing you
    might need to press before you can leave. An optional ask should sit below
    the controls in visual weight, not beside them -- so this is text that
    behaves like a link, and the hierarchy stays honest.

    Focusable and operable from the keyboard, because a mouse-only control in
    a window whose every other control is in the tab ring is a dead end.
    """

    def __init__(self, parent, text, command):
        super().__init__(parent, text=text, style="Link.TLabel",
                         cursor="hand2", takefocus=True)
        self.command = command
        for event in ("<Button-1>", "<Return>", "<space>"):
            self.bind(event, self._fire)
        self.bind("<Enter>", lambda e: self._lit(True))
        self.bind("<Leave>", lambda e: self._lit(False))
        # Focus underlines too, so a keyboard user can see where they are: the
        # accent colour alone is not a focus indicator.
        self.bind("<FocusIn>", lambda e: self._lit(True))
        self.bind("<FocusOut>", lambda e: self._lit(False))

    def _lit(self, on):
        self.configure(style="LinkHover.TLabel" if on else "Link.TLabel")

    def _fire(self, _event=None):
        if self.command:
            self.command()
        return "break"


class _ColourChip(tk.Label):
    """The current colour as a rounded chip. tk.Label -bg is a hard rectangle,
    so the chip is a Pillow image; the inner ring is what keeps white and
    near-ground colours reading as a chip rather than as a hole."""

    # A Label's -state greys its text, and this one has none: the chip is an
    # image and the click is a binding, so both have to be handled by hand.
    enabled = True

    def __init__(self, parent, s, pal, colour, command):
        self.s, self.pal, self.command = s, pal, command
        super().__init__(parent, bd=0, highlightthickness=0, bg=pal["surface"],
                         cursor="hand2", takefocus=True)
        self.box = s(36)
        self._hover = False
        self._focus = False
        self.bind("<Button-1>", lambda e: self._invoke(True))
        self.bind("<Return>", lambda e: self._invoke(False))
        self.bind("<space>", lambda e: self._invoke(False))
        self.bind("<Enter>", lambda e: self._flag("_hover", True))
        self.bind("<Leave>", lambda e: self._flag("_hover", False))
        self.bind("<FocusIn>", lambda e: self._flag("_focus", True))
        self.bind("<FocusOut>", lambda e: self._flag("_focus", False))
        self.set(colour)

    def _invoke(self, take_focus):
        if not self.enabled:
            return
        if take_focus:
            self.focus_set()
        self.command()

    def set_enabled(self, on):
        self.enabled = bool(on)
        tk.Label.configure(self, state="normal" if self.enabled else "disabled",
                           cursor="hand2" if self.enabled else "",
                           takefocus=bool(self.enabled))
        self.set(self.colour)

    def _flag(self, name, value):
        setattr(self, name, value)
        self.set(self.colour)

    def set(self, colour):
        self.colour = colour
        s, pal = self.s, self.pal
        ring_w = s(2) if self._hover else s(1)
        focus = self._focus

        def paint(d, W, H, k):
            o = s(4) * k
            if focus:
                rw = max(1, int(round(s(2) * k)))
                d.rounded_rectangle([rw / 2.0, rw / 2.0, W - 1 - rw / 2.0,
                                     H - 1 - rw / 2.0],
                                    radius=s(9) * k, outline=pal["accent"], width=rw)
            lw = max(1, int(round(ring_w * k)))
            d.rounded_rectangle([o + lw / 2.0, o + lw / 2.0,
                                 W - 1 - o - lw / 2.0, H - 1 - o - lw / 2.0],
                                radius=s(6) * k, fill=colour,
                                outline=pal["chip_ring"], width=lw)
        # Faded rather than recoloured: the chip's job is to show the colour,
        # so a disabled one should still be recognisably that colour.
        self._img = _sprite(self, self.box, self.box, paint,
                            1.0 if self.enabled else 0.35, keep=False)
        self.configure(image=self._img)


class _Picker(ttk.Button):
    """A button showing the current choice, with the list behind a click.

    A segmented control shows every option at once. That is right for three
    and absurd for ten: the language slot is 160px, so ten segments would be
    sixteen pixels each. This shows exactly ONE thing -- the choice in force
    -- which is also the answer to "how many languages does a user see?".
    One. Theirs. The rest exist only if they go looking.

    Deliberately not a ttk.Combobox. That drops a raw tk Listbox popdown no
    ttk theme can reach, and it is the one widget in this panel that would
    still have looked ten years old. The list here is a Toplevel of the same
    Ghost buttons the Advanced door already uses, so it inherits the theme.
    """

    ROW_H = 32
    LIST_PAD = 6
    # Rows before the list grows a second column. Twenty languages in one
    # column is 652 logical pixels, which at 150% scaling is 978 real ones
    # and runs off the bottom of a 1080p screen; two columns is 332. Ten
    # also happens to be where this list divides into Roman-script names
    # and the rest, so the columns read as the two halves they are.
    MAX_ROWS = 10

    def __init__(self, parent, s, pal, pairs, variable, width, command=None):
        self.s, self.pal = s, pal
        self.pairs = list(pairs)
        self.var = variable
        self.on_pick = command
        self.popup = None
        self.width = width
        # keep=False, and the button holds the only reference: the panel is
        # opened and closed freely, and a kept sprite per open would pile up
        # in _THEME_IMAGES for the life of the process.
        self._face = _picker_face(parent, s(width - 32), s(20), pal["muted"],
                                  s(1.5))
        super().__init__(parent, image=self._face, compound="center",
                         style="Secondary.TButton", command=self.toggle)
        variable.trace_add("write", lambda *_a: self._sync())
        self._sync()

    def _sync(self):
        # The variable outlives the widget when the panel is rebuilt, so a
        # late write must not reach a destroyed button.
        if self.winfo_exists():
            self.configure(text=self.var.get())

    # -- the list -----------------------------------------------------------

    def toggle(self):
        if self.popup is not None and self.popup.winfo_exists():
            self.hide()
        else:
            self.show()

    def show(self):
        s, pal = self.s, self.pal
        self.update_idletasks()
        col_w = self.winfo_width() or s(self.width)
        edge = max(1, s(1))
        # Balanced columns: 20 languages become 2 x 10, not 10 and a lonely
        # 10th column. Filled top to bottom then left to right, so the
        # alphabetical order still reads down the page.
        cols = max(1, -(-len(self.pairs) // self.MAX_ROWS))
        rows = -(-len(self.pairs) // cols)
        w = col_w * cols
        h = rows * s(self.ROW_H) + 2 * s(self.LIST_PAD)

        top = tk.Toplevel(self)
        self.popup = top
        top.withdraw()
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        # The Toplevel's own background IS the border: an overrideredirect
        # window has no frame, and a themed card floating with no edge at all
        # reads as a rendering glitch rather than as a menu.
        top.configure(bg=pal["border_strong"])

        body = ttk.Frame(top, style="Card.TFrame")
        body.place(x=edge, y=edge, width=w - 2 * edge, height=h - 2 * edge)
        for i, (label, _value) in enumerate(self.pairs):
            ttk.Button(body, text=label, style="Ghost.TButton",
                       command=lambda t=label: self._choose(t)).place(
                x=s(4) + (i // rows) * col_w - edge,
                y=s(self.LIST_PAD) - edge + (i % rows) * s(self.ROW_H),
                width=col_w - s(8), height=s(self.ROW_H))

        # Right-aligned to the button rather than left, so a list wider than
        # the button grows back across the panel instead of off the screen.
        top.geometry("%dx%d+%d+%d"
                     % (w, h, self.winfo_rootx() + self.winfo_width() - w,
                        self.winfo_rooty() + self.winfo_height() + s(4)))
        top.deiconify()
        top.bind("<Escape>", lambda _e: self.hide())
        top.bind("<Button-1>", self._maybe_close)
        # The grab is what makes a click anywhere else close the list, which
        # is the one behaviour a menu cannot do without.
        top.grab_set()

    def _maybe_close(self, event):
        top = self.popup
        if top is None or not top.winfo_exists():
            return
        x, y = top.winfo_rootx(), top.winfo_rooty()
        inside = (x <= event.x_root < x + top.winfo_width()
                  and y <= event.y_root < y + top.winfo_height())
        if not inside:
            self.hide()

    def hide(self):
        top, self.popup = self.popup, None
        if top is not None and top.winfo_exists():
            try:
                top.grab_release()
            except tk.TclError:
                pass          # the grab was never taken; nothing to give back
            top.destroy()

    def _choose(self, label):
        # Shut first. `command` may rebuild the whole panel, this button
        # included, and it must not do that with a grab still outstanding.
        self.hide()
        if label == self.var.get():
            return
        self.var.set(label)
        if self.on_pick:
            self.on_pick()


# --------------------------------------------------------------------------
# Settings window
# --------------------------------------------------------------------------

MONITOR_DEFAULTTONEAREST = 2
DWMWA_USE_IMMERSIVE_DARK_MODE = 20


def cursor_work_area():
    """Work area of the monitor the mouse is on.

    The panel should open where the user is looking, not on whichever screen
    Windows calls primary, and it must not slide under the taskbar.
    """
    try:
        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        user32.MonitorFromPoint.restype = ctypes.c_void_p
        hmon = user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(ctypes.c_void_p(hmon), ctypes.byref(info)):
            r = info.rcWork
            return r.left, r.top, r.right - r.left, r.bottom - r.top
    except Exception:
        pass
    x, y, w, h, _dpi, _primary = monitors()[0]
    return x, y, w, h


def use_dark_titlebar(win):
    """A light Win32 caption on a #202020 body looks broken, so match it.

    Must run after update_idletasks or the HWND does not exist yet. Failure is
    cosmetic, so it is swallowed.
    """
    try:
        hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), 4)
    except Exception:
        pass


class SettingsWindow:
    """The settings panel.

    Presentation only. It reads and writes exactly the config keys the app
    stores, just in units people actually think in: seconds rather than
    milliseconds, a named feel rather than three numbers, a percentage rather
    than a bare float, a picture of a screen rather than a list of corners.

    Two columns, one per reminder, and each column's card ends with a door to
    that reminder's own advanced window. The two advanced windows are built by
    one method from one description, so a row means the same thing in both. No
    control anywhere in here writes a setting belonging to the other reminder:
    every variable is reached through self.V[which], and collect() writes each
    reminder's fifteen pulse keys in the same loop.

    Every geometry number in here is a LOGICAL pixel at 96dpi, put through
    self.s() before it touches a widget. Font sizes are in points and are never
    scaled -- Tk already scales points against the reported DPI.
    """

    STYLES = [("A dot", "dot"), ("A word", "text"), ("Dim screen", "dim")]
    POSITIONS = [
        ("Centre", "center"),
        ("Top left", "top-left"),
        ("Top right", "top-right"),
        ("Bottom left", "bottom-left"),
        ("Bottom right", "bottom-right"),
    ]
    UNITS = [("seconds", 1), ("minutes", 60)]

    # One grid for every card. Rows are 32 high on a 48 pitch; a row whose
    # control needs its own label above it takes a taller slot. The only two
    # spacings in the panel are 20 between groups and 4 between a label and the
    # control it belongs to, which is what stops the columns reading as a pile
    # of arbitrary gaps.
    # Eight slots on a 48 pitch, starting at 44. Every card places into the
    # same slots -- a control taller than one slot simply spans two, which is
    # why the 58-high position grid takes S5 and S6 while the 34-high style
    # pickers take one. The advanced windows reuse these same slots, so their
    # rows line up with the panel's and with each other.
    S1, S2, S3, S4 = 44, 92, 140, 188
    S5, S6, S7, S8 = 236, 284, 332, 380
    # A ninth slot, used only by the advanced windows. The volume row used to
    # fit a label, a slider, a percentage and a Test button across 268px,
    # which works in English and in no other language measured: the label
    # alone wants 73 ("Громкость") of the 60 it had, and Test wants 46 of 32.
    # Giving the label its own line is the only arrangement with room for all
    # four, and it is what the Sound and Flash style rows above already do.
    S9 = 428
    CARD_PAD = 20                  # below the last row of any card

    # Both cards run S1..S7, the last row being the door to that reminder's own
    # advanced window: 332 + 32 + CARD_PAD is exactly 384.
    CARD_BLINK_H = CARD_BREAK_H = 384
    COL_H = 384
    # Header, the app-wide strip, the footer rule, the buttons and padding.
    # 44 more than it was: the strip below the cards is a new 32-high row plus
    # its gap, and it is what the header used to carry in its top-right corner.
    CHROME_H = 190
    WIN_W = 660                    # 20 + 300 + 20 + 300 + 20

    # The footer's four buttons, sized for the longest LANGUAGE rather than
    # for English. Measured against plausible German, French and Russian, all
    # of which run about 120% of English: "Aperçu clignement" wants 132px and
    # the old 124-wide button offered 92. The footer had 160px of unused
    # gutter between the preview pair and Cancel/Save, so widening them costs
    # nothing and it is the one change that stops every European language
    # rediscovering the same four buttons.
    # 168 and 124 leave a 16px gutter between the two groups, which is the
    # least the footer can give and still fit both the longest preview
    # label ("Aperçu clignement", 132px) and the longest Save ("Αποθήκευση",
    # 91px). Greek is what pushed the pair from 112 to 124.
    BTN_PREVIEW_W = 168
    BTN_FOOTER_W = 124
    # The Startup row is a switch when this app decides, and a wider button
    # when Windows does -- "Autozapusk: otklyuchyon v Dispetchere zadach" is
    # 311px, and a switch's label never gets near that.
    STARTUP_SWITCH_W = 268
    STARTUP_BUTTON_W = 360
    # The language picker in the header. The button shows ONE language, so
    # the widest endonym in the list sets the width -- currently "Bahasa
    # Indonesia" at 115px, which needed 176 rather than the old 160 once
    # the globe and the chevron have taken their share.
    LANG_W = 176

    # One advanced window per reminder, identical geometry. Two cards side by
    # side because one column of the same content is ~728 logical and does not
    # fit -- the same reason Advanced is a child window at all, one level down.
    ADV_W, ADV_H = 648, 560        # 16 + 300 + 16 + 300 + 16 wide
    # Both cards run S1..S9 and so are the same height: 428 + 32 + CARD_PAD.
    # The left card needed the ninth slot for the volume row; the right one
    # follows it so the two still end on the same line, and the gap it opens
    # above "Show on every monitor" reads as the break it already was --
    # placement settings above, monitor coverage below.
    ADV_LEFT_H = ADV_RIGHT_H = 480

    # (window title, timing card, look card) -- the only text that differs
    # between the two advanced windows. Everything else is built by one method,
    # so they are row-for-row identical by construction rather than by care.
    ADV_TITLES = {
        "blink": ("Advanced settings - Blink", "Blink timing and sound",
                  "Blink look"),
        "break": ("Advanced settings - Break", "Break timing and sound",
                  "Break look"),
    }

    WHICH = ("blink", "break")
    PREFIX = {"blink": "", "break": "break_"}
    CFG_OF = {"blink": blink_cfg, "break": break_cfg}

    # The five look controls on each card, under the flat attribute names the
    # rest of the class already uses. Irregular on purpose -- pct/break_pct but
    # btn_colour/btn_break_colour -- because those names predate the split and
    # renaming them would be churn. self.W[which] is the real home; these are
    # aliases onto it, the same arrangement _alias_blink_adv already uses.
    CARD_ATTRS = {
        "blink": {"style": "seg_style", "slider": "slider", "pct": "pct",
                  "chip": "chip", "colour_btn": "btn_colour",
                  "sound": "tog_sound", "door": "adv_btn_blink"},
        "break": {"style": "seg_break_style", "slider": "break_slider",
                  "pct": "break_pct", "chip": "break_chip",
                  "colour_btn": "btn_break_colour", "sound": "tog_break_sound",
                  "door": "adv_btn_break"},
    }

    def __init__(self, app):
        self.app = app
        self.win = None
        # Built only if a support handle is configured, and _place_chrome runs
        # before the panel is first built, so it needs a value from the start.
        self.link_support = None
        # One debounce slot per reminder. A single slot meant editing the break
        # cancelled a pending blink preview and left a dead after-id behind.
        self.preview_jobs = {"blink": None, "break": None}
        self.V = {}                                   # variables, by reminder
        self.W = {"blink": {}, "break": {}}           # card widgets, by reminder
        # Set only while the panel is being rebuilt in a new language, so the
        # rebuild starts from what was on screen rather than from what is saved.
        self._pending = None
        self.adv = {"blink": {"win": None}, "break": {"win": None}}
        # Flat aliases onto the BLINK window's widgets. Nothing in the app
        # reads them; they exist because the advanced window used to be a
        # single window and the tests still address it that way.
        self._alias_blink_adv(None)

    @property
    def win_h(self):
        return self.COL_H + self.CHROME_H

    def _place_chrome(self, win_h):
        """The rule and buttons hang off the bottom edge rather than sitting at
        fixed offsets, so they follow the window if its height ever changes."""
        s = self.s
        self.outer.place_configure(width=s(self.WIN_W), height=s(win_h))
        self.rule.place_configure(x=s(20), y=s(win_h - 53),
                                  width=s(self.WIN_W - 40), height=max(1, s(1)))
        # The app-wide strip: everything that belongs to the whole app rather
        # than to this window or to either reminder. Above the rule, so the
        # rule still separates "settings" from "what to do with them".
        strip = s(win_h - 95)
        self.tog_startup.place_configure(x=s(20), y=strip,
                                         width=s(self.startup_w), height=s(32))
        if self.link_support is not None:
            # Right-aligned by anchor rather than a computed x, so it stays on
            # the margin whatever the text measures at this DPI.
            self.link_support.place_configure(x=s(self.WIN_W - 20),
                                              y=strip + s(16), anchor="e")

        by = s(win_h - 40)
        pw, fw = self.BTN_PREVIEW_W, self.BTN_FOOTER_W
        self.btn_preview.place_configure(x=s(20), y=by, width=s(pw), height=s(32))
        self.btn_preview_break.place_configure(x=s(20 + pw + 8), y=by,
                                               width=s(pw), height=s(32))
        for btn, bx in ((self.btn_cancel, self.WIN_W - 20 - 2 * fw - 12),
                        (self.btn_save, self.WIN_W - 20 - fw)):
            btn.place_configure(x=s(bx), y=by, width=s(fw), height=s(32))

    def _alias_blink_adv(self, slot):
        """Point the old flat attribute names at the blink window's widgets."""
        slot = slot or {}
        self.adv_win = slot.get("win")
        self.seg_feel = slot.get("seg_feel")
        self.adv_boxes = slot.get("boxes", [])
        self.tog_all = slot.get("tog_all")
        self.seg_sound = slot.get("seg_sound")
        self.sl_volume = slot.get("sl_vol")
        self.btn_sound_test = slot.get("btn_test")

    def _open_advanced(self, which="blink"):
        """One reminder's advanced settings, in their own window.

        Two windows, one per reminder, because there is no longer any such
        thing as a shared setting to put in a third place. They may both be
        open at once -- collect() reads variables, not widgets, so it works
        with neither, either or both -- which is what lets you hold the blink's
        settings and the break's side by side and compare them.

        A window rather than a drawer for the same reason as before: the panel
        can be at most ~638 logical px tall on this display once the caption is
        counted, and these contents need 512 on their own.
        """
        w = (self.adv.get(which) or {}).get("win")
        if w is not None and w.winfo_exists():
            w.deiconify()
            w.lift()
            w.focus_force()
            return
        self._build_adv_window(which)

    def _build_adv_window(self, which):
        """Both advanced windows, from one description.

        `which` picks the variables, the group names and the two card titles;
        nothing else differs. That is deliberate: the guarantee the user asked
        for is that the break's settings mean the same thing as the blink's,
        and the cheapest way to guarantee it is to build them from one method.
        """
        s, pal, fonts = self.s, self.pal, _THEME_METRICS["fonts"]
        V = self.V[which]
        title, left_title, right_title = (T(t) for t in self.ADV_TITLES[which])
        grp = which + "_"

        def preview(*_):
            self._preview(which)

        w = tk.Toplevel(self.win)
        slot = {"win": w}
        self.adv[which] = slot
        w.title(title)
        w.resizable(False, False)
        w.transient(self.win)
        w.configure(bg=pal["ground"])
        w.protocol("WM_DELETE_WINDOW", lambda: self._close_advanced(which))
        w.bind("<Escape>", lambda e: self._close_advanced(which))
        w.bind("<Return>", lambda e: self._close_advanced(which))

        win_w, win_h = s(self.ADV_W), s(self.ADV_H)
        # Offset the second window so two open ones do not sit exactly on top
        # of each other, which would look like one window that failed to open.
        other = "break" if which == "blink" else "blink"
        ow = (self.adv.get(other) or {}).get("win")
        off = s(28) if (ow is not None and ow.winfo_exists()) else 0
        px = self.win.winfo_rootx() + (self.win.winfo_width() - win_w) // 2 + off
        py = self.win.winfo_rooty() + s(60) + off
        w.geometry("%dx%d+%d+%d" % (win_w, win_h, px, py))

        outer = ttk.Frame(w, style="Ground.TFrame")
        outer.place(x=0, y=0, width=win_w, height=win_h)

        # ---- left card: timing and sound ---------------------------------
        left = self._card(outer, 16, 16, 300, self.ADV_LEFT_H, left_title)

        self._label(left, T("Flash style"), 16, self.S1, anchor="nw")
        seg_feel = _Segmented(left, s, [t for t, _ in feel_pairs()], V["feel"],
                              268, 32, command=lambda: self._feel_changed(which),
                              small=True, dim=(T(CUSTOM),))
        seg_feel.place(x=s(16), y=s(self.S2), width=seg_feel.pw, height=seg_feel.ph)

        boxes = []
        specs = ((T("Hold (s)"), V["hold"], 0.05, 5.0, 0.05, "%.2f"),
                 (T("Fade (s)"), V["fade"], 0.05, 5.0, 0.05, "%.2f"),
                 (T("Pulses"), V["blinks"], 1, 10, 1, None))
        for i, (text, var, lo, hi, step, fmt) in enumerate(specs):
            x = 16 + i * 92
            self._label(left, text, x, self.S3, style="Cap.TLabel", anchor="nw")
            kw = {"format": fmt} if fmt else {}
            box = ttk.Spinbox(left, from_=lo, to=hi, increment=step,
                              textvariable=var, font=fonts["t4"],
                              command=lambda: self._went_custom(which), **kw)
            box.place(x=s(x), y=s(self.S4), width=s(84), height=s(32))
            box.bind("<FocusOut>", lambda e: self._went_custom(which))
            boxes.append(box)

        # Only meaningful once Pulses can exceed 1, which for the break is the
        # first time ever -- break_cfg used to hardcode a single pulse.
        self._label(left, T("Gap between pulses"), 16, self.S5 + 16)
        sp_gap = ttk.Spinbox(left, from_=0.0, to=2.0, increment=0.05,
                             format="%.2f", textvariable=V["gap"],
                             font=fonts["t4"], command=preview)
        sp_gap.place(x=s(200), y=s(self.S5), width=s(84), height=s(32))
        sp_gap.bind("<FocusOut>", preview)

        self._label(left, T("Sound"), 16, self.S6, anchor="nw")
        # Full width: four sounds in the 196 the three aliases used to share
        # left 49px a segment, which "Notify" does not fit into.
        seg_sound = _Segmented(left, s, [t for t, _ in translated(SOUNDS)],
                               V["sound_name"], 268, 32, small=True,
                               command=preview)
        seg_sound.place(x=s(16), y=s(self.S7), width=seg_sound.pw,
                        height=seg_sound.ph)

        # Volume and Test share a row deliberately: the slider is the setting,
        # the button is how you hear it. The slider is also the one control in
        # this window that does NOT fire a preview -- a break preview dims every
        # screen for a second and a half, which is far too much to inflict on
        # someone nudging an audio level.
        self._label(left, T("Volume"), 16, self.S8, anchor="nw")
        sl_vol = _Slider(left, s, self.pal, V["volume"], SOUND_VOL_MIN, 1.0,
                         96, 24, command=lambda _v: self._show_volume(which))
        sl_vol.place(x=s(16), y=s(self.S9 + 4))
        pct_vol = ttk.Label(left, text="", style="Pct.TLabel", anchor="e")
        pct_vol.place(x=s(176), y=s(self.S9 + 16), anchor="e")
        # A file can be missing and a device can be muted, and neither is
        # visible. This plays THIS reminder's sound at THIS reminder's volume.
        btn_test = ttk.Button(
            left, text=T("Test"), style="Secondary.TButton",
            command=lambda: play_sound(
                self._value_of(translated(SOUNDS), V["sound_name"].get()),
                V["volume"].get()))
        btn_test.place(x=s(196), y=s(self.S9), width=s(88), height=s(32))

        # ---- right card: look --------------------------------------------
        right = self._card(outer, 332, 16, 300, self.ADV_RIGHT_H, right_title)

        self._label(right, T("Dot size"), 16, self.S1 + 16, group=grp + "dot")
        # 1..100, the whole range the value can hold. The old spinbox was
        # capped at 400 while a live config held 840, so opening this panel
        # silently clamped a setting the user had chosen -- the one thing a
        # settings window must never do.
        sp_dot = ttk.Spinbox(right, from_=1, to=100, increment=1,
                             textvariable=V["dot"], font=fonts["t4"],
                             command=preview)
        sp_dot.place(x=s(172), y=s(self.S1), width=s(88), height=s(32))
        self.groups.setdefault(grp + "dot", []).append(sp_dot)
        # Just "%": the hint column is the 34px between the spinbox and the
        # card edge, and "% of screen" was cropped to "% of s". Widening it
        # would push the spinbox out of line with every other row.
        self._label(right, "%", 266, self.S1 + 16, style="Hint.TLabel",
                    group=grp + "dot")

        # The entry starts at 168, not 112: "Anzuzeigendes Wort" is 137px and
        # the label used to have 96. A word is one word in any language, so
        # the entry can afford the 56 the label needed.
        self._label(right, T("Word to show"), 16, self.S2 + 16,
                    group=grp + "text")
        en_word = ttk.Entry(right, textvariable=V["message"], font=fonts["t4"])
        en_word.place(x=s(168), y=s(self.S2), width=s(116), height=s(32))
        en_word.bind("<KeyRelease>", preview)
        self.groups.setdefault(grp + "text", []).append(en_word)

        self._label(right, T("Word size"), 16, self.S3 + 16, group=grp + "text")
        sp_font = ttk.Spinbox(right, from_=8, to=200, increment=1,
                              textvariable=V["font"], font=fonts["t4"],
                              command=preview)
        sp_font.place(x=s(172), y=s(self.S3), width=s(88), height=s(32))
        self.groups.setdefault(grp + "text", []).append(sp_font)
        self._label(right, "pt", 266, self.S3 + 16, style="Hint.TLabel",
                    group=grp + "text")

        self._label(right, T("Position"), 16, self.S4, anchor="nw",
                    group=grp + "place")
        grid_pos = _PositionGrid(right, s, V["corner"],
                                 command=lambda: self._position_changed(which))
        grid_pos.place(x=s(16), y=s(self.S5), width=grid_pos.pw,
                       height=grid_pos.ph)
        self.groups.setdefault(grp + "place", []).extend(grid_pos.widgets())
        caption = self._label(right, V["corner"].get(), 120, self.S5 + 29,
                              style="Hint.TLabel", group=grp + "place")

        # Its own group, not "place": the margin is what "distance from the
        # edge" means, so it is dead when the reminder is centred -- a narrower
        # condition than the rest of the position row.
        self._label(right, T("Edge margin"), 16, self.S7 + 16,
                    group=grp + "margin")
        sp_margin = ttk.Spinbox(right, from_=0, to=500, increment=1,
                                textvariable=V["margin"], font=fonts["t4"],
                                command=preview)
        sp_margin.place(x=s(172), y=s(self.S7), width=s(88), height=s(32))
        self.groups.setdefault(grp + "margin", []).append(sp_margin)
        self._label(right, "px", 266, self.S7 + 16, style="Hint.TLabel",
                    group=grp + "margin")

        tog_all = ttk.Checkbutton(right, text=T("Show on every monitor"),
                                  variable=V["all"], style="Switch.TCheckbutton",
                                  command=preview)
        tog_all.place(x=s(16), y=s(self.S9), width=s(268), height=s(32))

        done = ttk.Button(outer, text=T("Done"), style="Primary.TButton",
                          command=lambda: self._close_advanced(which))
        done.place(x=win_w - s(16) - s(96), y=s(self.ADV_H - 48),
                   width=s(96), height=s(32))

        slot.update(seg_feel=seg_feel, boxes=boxes, sp_gap=sp_gap,
                    seg_sound=seg_sound, sl_vol=sl_vol, pct_vol=pct_vol,
                    btn_test=btn_test, sp_dot=sp_dot,
                    en_word=en_word, sp_font=sp_font, grid_pos=grid_pos,
                    caption=caption, sp_margin=sp_margin, tog_all=tog_all,
                    done=done)
        # Only reachable once the label is in `slot`, so after the update.
        self._show_volume(which)
        if which == "blink":
            self._alias_blink_adv(slot)

        # Freshly created widgets have to land in the right state, or a window
        # opened while the style says "dim" comes up fully live.
        self._sync_enabled()

        w.update_idletasks()
        if pal["dark_titlebar"]:
            use_dark_titlebar(w)
        w.lift()
        w.focus_force()
        done.focus_set()

    def _close_advanced(self, which=None):
        """Close one advanced window, or both when called with nothing."""
        for name in (self.WHICH if which is None else (which,)):
            slot = self.adv.get(name) or {}
            win = slot.get("win")
            self.adv[name] = {"win": None}
            if name == "blink":
                self._alias_blink_adv(None)
            # The greying groups pointed at widgets inside that window, so they
            # go with it. _sync_enabled would otherwise poke dead widgets.
            for suffix in ("dot", "text", "place", "margin"):
                self.groups.pop(name + "_" + suffix, None)
            if win is not None:
                try:
                    win.destroy()
                except tk.TclError:
                    pass
        # The variables the window edited stay on the panel, which is what
        # collect() reads, so nothing typed in there is lost by closing it.
        if self.win is not None and self.win.winfo_exists():
            self.win.focus_force()

    # -- label/value mapping ------------------------------------------------

    @staticmethod
    def _text_of(pairs, value):
        for text, val in pairs:
            if val == value:
                return text
        # collect() writes the picker's text straight back, so an unrecognised
        # value is permanently rewritten to the first option on the next Save.
        # Say so in the log rather than losing it in silence.
        log_event("config", "unknown setting %r shown as %r" % (value, pairs[0][0]))
        return pairs[0][0]

    @staticmethod
    def _value_of(pairs, text):
        for t, val in pairs:
            if t == text:
                return val
        return pairs[0][1]

    def _int(self, var, fallback):
        """Spinboxes can be left empty or half-typed, so never trust .get()."""
        try:
            return int(float(var.get()))
        except (tk.TclError, ValueError):
            return fallback

    # -- building the panel -------------------------------------------------

    def _card(self, parent, x, y, w, h, title=None):
        """One rounded surface on the tinted ground. No shadow: a hairline on a
        tinted ground is how Windows 11 Settings itself layers a panel."""
        s = self.s
        card = ttk.Frame(parent, style="Card.TFrame")
        card.place(x=s(x), y=s(y), width=s(w), height=s(h))
        if title:
            ttk.Label(card, text=title, style="CardTitle.TLabel").place(
                x=s(16), y=s(13))
        return card

    def _label(self, parent, text, x, y, style="Row.TLabel", anchor="w", group=None):
        lab = ttk.Label(parent, text=text, style=style)
        lab.place(x=self.s(x), y=self.s(y), anchor=anchor)
        if group:
            self.groups.setdefault(group, []).append(lab)
        return lab

    def _build_vars(self, cfg):
        """One tk variable per stored key, indexed by the reminder that owns it.

        self.V[which][name] is the source of truth; the flat v_* attributes are
        the same objects under the names the rest of the class already uses.
        Both sets are built here rather than inside a card so that collect()
        returns every key whether or not a window has ever been opened.
        """
        self.V = {}
        for which in self.WHICH:
            p = self.PREFIX[which]
            variables = {
                "style": tk.StringVar(
                    value=self._text_of(translated(self.STYLES),
                                        cfg[p + "style"])),
                "opacity": tk.DoubleVar(value=cfg[p + "opacity"]),
                "colour": tk.StringVar(value=cfg[p + "colour"]),
                "sound": tk.BooleanVar(value=bool(cfg[p + "sound_enabled"])),
                "feel": tk.StringVar(value=T(feel_of(cfg, p))),
                # Seconds in the panel, milliseconds on disk. Nobody thinks in
                # milliseconds and nobody wants a float in a config file.
                "hold": tk.DoubleVar(
                    value=round(int(cfg[p + "hold_ms"]) / 1000.0, 2)),
                "fade": tk.DoubleVar(
                    value=round(int(cfg[p + "fade_ms"]) / 1000.0, 2)),
                "gap": tk.DoubleVar(
                    value=round(int(cfg[p + "gap_ms"]) / 1000.0, 2)),
                "blinks": tk.IntVar(value=int(cfg[p + "blinks"])),
                "message": tk.StringVar(value=cfg[p + "message"]),
                "dot": tk.IntVar(value=int(cfg[p + "dot_pct"])),
                "font": tk.IntVar(value=int(cfg[p + "font_size"])),
                "corner": tk.StringVar(
                    value=self._text_of(translated(self.POSITIONS),
                                        cfg[p + "corner"])),
                "margin": tk.IntVar(value=int(cfg[p + "margin"])),
                "all": tk.BooleanVar(value=bool(cfg[p + "all_monitors"])),
                "sound_name": tk.StringVar(
                    value=self._text_of(translated(SOUNDS),
                                        cfg[p + "sound_name"])),
                "volume": tk.DoubleVar(value=float(cfg[p + "sound_volume"])),
            }
            # The volume row follows the variable, not the drag. Traced here,
            # where the variable is made, rather than in the window that draws
            # it: that window is opened and closed freely and would stack one
            # trace per open, while these variables are rebuilt once per panel.
            variables["volume"].trace_add(
                "write", lambda *_a, w=which: self._show_volume(w))

            self.V[which] = variables
            flat = "v_" if which == "blink" else "v_break_"
            for name, var in variables.items():
                setattr(self, flat + name, var)

        self.v_startup = tk.BooleanVar(value=bool(cfg["start_with_windows"]))
        # The language IN FORCE, not the string on disk. On a fresh install
        # that string is "auto", and a picker showing "auto" tells the user
        # nothing about what they are looking at.
        self.v_lang = tk.StringVar(
            value=self._text_of(LANGUAGES, language_code()))

    def open(self):
        if self.win is not None and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        # _pending is a collect() result handed over by _language_changed, and
        # it holds exactly the keys DEFAULTS does, so everything below reads it
        # the same way it reads a saved config.
        cfg, self._pending = (self._pending or self.app.cfg), None
        # Exactly the keys collect() returns. dict(cfg) also carried whatever
        # else the file happened to hold, so cancel() claimed you had made
        # edits whenever config.json had one key the panel does not own.
        self.opened_with = {k: cfg[k] for k in DEFAULTS if k in cfg}
        root = self.app.root

        mode = app_theme_mode()
        ensure_theme(root, mode)
        self.pal = pal = PALETTES[mode]
        self.s = s = _THEME_METRICS["s"]
        self.groups = {}
        self._build_vars(cfg)

        self.win = tk.Toplevel(root)
        self.win.title(DISPLAY_NAME)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=pal["ground"])
        self.win.protocol("WM_DELETE_WINDOW", self.cancel)
        self.win.bind("<Return>", lambda e: self.save())
        self.win.bind("<Escape>", lambda e: self.cancel())

        win_w, win_h = s(self.WIN_W), s(self.win_h)
        mx, my, mw, mh = cursor_work_area()
        caption = s(34)
        x = mx + max(0, (mw - win_w) // 2)
        y = my + max(caption, (mh - win_h) // 2)
        y = min(y, my + max(caption, mh - win_h))
        self.win.geometry("%dx%d+%d+%d" % (win_w, win_h, x, y))

        self.outer = outer = ttk.Frame(self.win, style="Ground.TFrame")
        outer.place(x=0, y=0, width=win_w, height=win_h)

        ttk.Label(outer, text=DISPLAY_NAME, style="Title.TLabel").place(
            x=s(20), y=s(15))

        # The language picker, on the header's own line and right-aligned to
        # the same 20px margin as everything else. Up here rather than on the
        # strip below with "Start with Windows": that strip is for app-wide
        # SETTINGS, and this is the one control whose effect you can see the
        # instant you touch it, so it belongs where the eye starts.
        #
        # ONE language on screen -- the one in force -- and the rest behind a
        # click. There is no "Auto" entry: auto is the state a fresh install
        # is already in, and the picker simply shows what it resolved to.
        # 32 high like every other control, and its top edge on the title's,
        # which is the alignment the eye actually checks.
        self.lang_picker = _Picker(outer, s, pal, LANGUAGES, self.v_lang,
                                   self.LANG_W,
                                   command=self._language_changed)
        self.lang_picker.place(x=s(self.WIN_W - 20 - self.LANG_W), y=s(15),
                               width=s(self.LANG_W), height=s(32))
        # Short on purpose. It was shortened when the header carried a switch
        # on its right; the switch has since moved to its own strip at the
        # bottom, so the constraint is gone -- but a one-line subtitle was the
        # better writing anyway, so it stays short by choice now, not by force.
        ttk.Label(outer, text=T("A gentle nudge on every screen."),
                  style="Sub.TLabel").place(x=s(20), y=s(46))

        # The one app-wide setting. It lives on its own strip under both
        # cards rather than in either of them, which is exactly its scope --
        # and below them rather than in the header, where sitting beside the
        # title made it read as window chrome instead of as a setting.
        #
        # Two shapes, because there are two builds. Unpackaged, this app writes
        # the Startup shortcut itself and a switch is the truth. Packaged, the
        # answer lives in Windows and a switch would be a lie, so it becomes a
        # door to the page that actually decides. Same slot either way.
        # Three shapes, not two. A switch is only the truth when this app is
        # the thing that decides; when Windows has taken the decision -- either
        # because we are packaged, or because the user switched the entry off
        # in Task Manager -- it becomes a door to the page that really owns it.
        blocked = not PACKAGED and startup_blocked_by_windows()
        self.startup_w = (self.STARTUP_BUTTON_W if (PACKAGED or blocked)
                          else self.STARTUP_SWITCH_W)
        if PACKAGED or blocked:
            self.tog_startup = ttk.Button(
                outer,
                text=T("Startup: managed by Windows") if PACKAGED
                     else T("Startup: turned off in Task Manager"),
                style="Secondary.TButton",
                command=lambda: open_link(STARTUP_SETTINGS_URI))
        else:
            self.tog_startup = ttk.Checkbutton(
                outer, text=T("Start with Windows"), variable=self.v_startup,
                style="SwitchGround.TCheckbutton")
        # Both are positioned by _place_chrome, which hangs everything off the
        # bottom edge, so the strip follows the window if its height changes.

        # Beside it on the same strip. Absent entirely when no handle is
        # configured -- see SUPPORT_HANDLE.
        self.link_support = (
            _Link(outer, T("Buy me a coffee"), lambda: open_link(SUPPORT_URL))
            if SUPPORT_URL else None)

        colh = s(self.COL_H)
        left = ttk.Frame(outer, style="Ground.TFrame")
        left.place(x=s(20), y=s(79), width=s(300), height=colh)
        right = ttk.Frame(outer, style="Ground.TFrame")
        right.place(x=s(340), y=s(79), width=s(300), height=colh)

        # One card per reminder and nothing else. There is no third "shared"
        # column any more, because there is nothing left for it to hold: every
        # look setting now belongs to exactly one of these two.
        self._build_blink(left, cfg)
        self._build_break(right, cfg)

        self.rule = ttk.Frame(outer, style="Rule.TFrame")
        self.btn_preview = ttk.Button(outer, text=T("Preview blink"),
                                      style="Secondary.TButton",
                                      command=self.preview_now)
        self.btn_preview_break = ttk.Button(outer, text=T("Preview break"),
                                            style="Secondary.TButton",
                                            command=lambda: self.preview_now("break"))
        # Previewing a switched-off break was the one place the panel would
        # still show you something the app would never do.
        self.groups.setdefault("break", []).append(self.btn_preview_break)
        self.btn_cancel = ttk.Button(outer, text=T("Cancel"),
                                     style="Secondary.TButton",
                                     command=self.cancel)
        self.btn_save = ttk.Button(outer, text=T("Save"), style="Primary.TButton",
                                   command=self.save)
        self._place_chrome(self.win_h)

        self._wire_tabs()
        self._sync_enabled()
        for which in self.WHICH:
            self._show_pct(which)
        self.win.update_idletasks()
        if pal["dark_titlebar"]:
            use_dark_titlebar(self.win)
        self.win.lift()
        self.win.focus_force()
        self.sp_every.focus_set()

    # -- cards ---------------------------------------------------------------

    def _build_blink(self, col, cfg):
        """Blink: when it fires, what it looks like, and its own Advanced door."""
        s = self.s
        card = self._card(col, 0, 0, 300, self.CARD_BLINK_H, T("Blink"))

        secs = int(cfg["interval_seconds"])
        as_minutes = secs >= 120 and secs % 60 == 0
        self.v_every = tk.IntVar(value=secs // 60 if as_minutes else secs)
        self.v_unit = tk.StringVar(
            value=self._text_of(translated(self.UNITS), 60 if as_minutes else 1))

        # Centred in the 32-high slot so it lands on the same line as the Break
        # card's toggle, whose text sits in the middle of a 32-high control.
        self._label(card, T("Remind me every"), 16, self.S1 + 16)
        self.sp_every = ttk.Spinbox(card, from_=1, to=999, increment=1,
                                    textvariable=self.v_every,
                                    font=_THEME_METRICS["fonts"]["t4"])
        self.sp_every.place(x=s(16), y=s(self.S2), width=s(96), height=s(32))
        # Clamping still happens in collect(); this only stops the field
        # showing something collect() would silently override.
        self.sp_every.bind("<FocusOut>", lambda e: self._clamp_interval())

        self.seg_unit = _Segmented(card, s,
                                   [t for t, _ in translated(self.UNITS)],
                                   self.v_unit,
                                   156, 32, command=self._clamp_interval)
        self.seg_unit.place(x=s(120), y=s(self.S2), width=self.seg_unit.pw,
                            height=self.seg_unit.ph)

        self._build_look_rows("blink", card, cfg)

    def _build_look_rows(self, which, card, cfg):
        """Rows S3..S7 of a reminder's card: style, strength, colour, sound, door.

        One body for both reminders. Their top two rows genuinely differ -- the
        blink asks for an interval, the break for a wall-clock minute -- but
        from the style picker down they are the same five rows, and they used
        to be written out twice. That is how the break's style picker came to
        drive the blink's controls: not by a bad decision, but because one copy
        was edited and the other was not.

        The break's rows also join its greying group and the blink's do not,
        which is the only real difference and is what `group` carries.
        """
        s, p, V = self.s, self.PREFIX[which], self.V[which]
        group = "break" if which == "break" else None
        W = self.W[which] = {}

        def owned(widget):
            if group:
                self.groups.setdefault(group, []).append(widget)
            return widget

        W["style"] = owned(_Segmented(
            card, s, [t for t, _ in translated(self.STYLES)], V["style"],
            268, 34, command=lambda: self._style_changed(which)))
        W["style"].place(x=s(16), y=s(self.S3), width=W["style"].pw,
                         height=W["style"].ph)

        self._label(card, T("Strength"), 16, self.S4 + 16, group=group)
        # lambda, not the bound method: _Slider calls command(value), which
        # would otherwise land the float in the `which` parameter.
        W["slider"] = owned(_Slider(
            card, s, self.pal, V["opacity"], 0.02, 1.0, 146, 24,
            command=lambda _v: self._strength_moved(which)))
        W["slider"].place(x=s(90), y=s(self.S4 + 4))
        W["pct"] = owned(ttk.Label(card, text="", style="Pct.TLabel", anchor="e"))
        W["pct"].place(x=s(284), y=s(self.S4 + 16), anchor="e")

        self._label(card, T("Colour"), 16, self.S5 + 16, group=group)
        # Chip and button both moved left of where they were, to buy the
        # button 32 more pixels: "Изменить…" is 86px and the old 100-wide
        # button offered 68. The label keeps 104, which is twice what the
        # longest translation of "Colour" asks for.
        W["chip"] = owned(_ColourChip(card, s, self.pal, cfg[p + "colour"],
                                      lambda: self.pick_colour(which)))
        W["chip"].place(x=s(120), y=s(self.S5 + 16), anchor="w")
        W["colour_btn"] = owned(ttk.Button(
            card, text=T("Change..."), style="Secondary.TButton",
            command=lambda: self.pick_colour(which)))
        W["colour_btn"].place(x=s(152), y=s(self.S5), width=s(132), height=s(32))

        W["sound"] = owned(ttk.Checkbutton(
            card, text=T("Play a sound"), variable=V["sound"],
            style="Switch.TCheckbutton"))
        W["sound"].place(x=s(16), y=s(self.S6), width=s(268), height=s(32))

        # In the break's group, so switching the break off greys its door too:
        # the window it opens is entirely about a feature that is not running.
        W["door"] = owned(self._adv_door(card, which))

        for key, attr in self.CARD_ATTRS[which].items():
            setattr(self, attr, W[key])

    def _adv_door(self, card, which):
        """The way into one reminder's advanced settings, inside its own card.

        Inside the card rather than in a standalone card of its own: the old
        Advanced card sat under Break while every control it opened belonged to
        the blink, which is precisely the mistake this whole change is undoing.
        A door in the Blink card cannot be read as the break's.
        """
        s = self.s
        icon = _arrow(card, s(14), self.pal["muted"], True, s(1.5))
        # _arrow does not keep its image alive, so the button must.
        button = ttk.Button(card, text=T("  Advanced settings"), image=icon,
                            compound="left", style="Ghost.TButton",
                            command=lambda: self._open_advanced(which))
        button.image = icon
        button.place(x=s(16), y=s(self.S7), width=s(268), height=s(32))
        return button

    def _build_break(self, col, cfg):
        """The wall-clock screen flash, row-for-row against Blink."""
        s = self.s
        card = self._card(col, 0, 0, 300, self.CARD_BREAK_H, T("Break"))

        self.v_break_on = tk.BooleanVar(value=bool(cfg["break_enabled"]))
        self.tog_break = ttk.Checkbutton(card, text=T("Remind me to look away"),
                                         variable=self.v_break_on,
                                         style="Switch.TCheckbutton",
                                         command=self._sync_enabled)
        self.tog_break.place(x=s(16), y=s(self.S1), width=s(268), height=s(32))

        minutes = int(cfg["break_minutes"])
        if minutes not in BREAK_MINUTES:
            # Saved from an older option set: snap to the nearest on offer so
            # the control cannot sit with nothing selected.
            minutes = min(BREAK_MINUTES, key=lambda m: abs(m - minutes))
        self.v_break_min = tk.StringVar(value=str(minutes))
        self.seg_break_min = _Segmented(
            card, s, [str(m) for m in BREAK_MINUTES], self.v_break_min,
            196, 32, small=True)
        self.seg_break_min.place(x=s(16), y=s(self.S2),
                                 width=self.seg_break_min.pw,
                                 height=self.seg_break_min.ph)
        self.groups.setdefault("break", []).append(self.seg_break_min)
        self._label(card, T("min"), 220, self.S2 + 16, style="Hint.TLabel",
                    group="break")

        self._build_look_rows("break", card, cfg)

        # Sits on the title's own line, after it. Measured rather than guessed
        # at a fixed x, and baseline-aligned, so a smaller font still sits on
        # the same line as the title rather than floating above or below it.
        title_font = tkfont.Font(root=card, font=_THEME_METRICS["fonts"]["t3l"])
        self.break_tag = ttk.Label(card, text=T("Look at trees!"),
                                   style="Hint.TLabel")
        tag_font = tkfont.Font(root=card, font=_THEME_METRICS["fonts"]["t5"])
        self.break_tag.place(
            # Measured from the TRANSLATED title, or the tag lands on top of a
            # Chinese card title that is a third of the width of "Break".
            x=s(16) + title_font.measure(T("Break")) + s(12),
            # anchor sw pins the bottom edge, and the baseline sits one descent
            # above it, so the descent has to be added back to line them up.
            y=s(13) + title_font.metrics("ascent") + tag_font.metrics("descent"),
            anchor="sw")
        self.groups.setdefault("break", []).append(self.break_tag)

    # -- tab order -----------------------------------------------------------

    def _wire_tabs(self):
        """Tab follows the reading order of the panel, not the widget tree.

        The two columns are separate subtrees, so Tk's own traversal would run
        all the way down the left column before reaching the Break card. Each
        advanced window is its own Toplevel and keeps Tk's own traversal.
        """
        self.tab_ring = [
            # The header's own control, first, because it is first on screen
            self.lang_picker,
            # Blink, in the order the card reads, ending at its own door
            self.sp_every, self.seg_unit, self.seg_style, self.slider,
            self.chip, self.btn_colour, self.tog_sound, self.adv_btn_blink,
            # Break, the same order, ending at its own door
            self.tog_break, self.seg_break_min, self.seg_break_style,
            self.break_slider, self.break_chip, self.btn_break_colour,
            self.tog_break_sound, self.adv_btn_break,
            # The app-wide strip, then the footer -- the same order the eye
            # takes down the window, which is what tab order is for.
            self.tog_startup,
        ]
        if self.link_support is not None:
            self.tab_ring.append(self.link_support)
        self.tab_ring += [
            self.btn_preview, self.btn_preview_break,
            self.btn_cancel, self.btn_save,
        ]

        for i, item in enumerate(self.tab_ring):
            targets = item.buttons if isinstance(item, _Segmented) else [item]
            for widget in targets:
                widget.bind("<Tab>", lambda e, k=i: self._tab(k, 1))
                widget.bind("<Shift-Tab>", lambda e, k=i: self._tab(k, -1))
                widget.bind("<ISO_Left_Tab>", lambda e, k=i: self._tab(k, -1))

    def _tab(self, index, step):
        ring = self.tab_ring
        for hop in range(1, len(ring) + 1):
            item = ring[(index + step * hop) % len(ring)]
            if not item.winfo_ismapped():
                continue
            if isinstance(item, _Segmented):
                item.focus_target().focus_set()
                return "break"
            if isinstance(item, _PositionGrid):
                if all(str(w.cget("state")) == "disabled" for w in item.widgets()):
                    continue
                item.focus_set()
                return "break"
            try:
                if str(item.cget("state")) == "disabled":
                    continue
            except tk.TclError:
                pass
            item.focus_set()
            return "break"
        return "break"

    # -- enabling ------------------------------------------------------------

    @staticmethod
    def _enable(widget, on):
        """Grey one widget, whatever kind it is.

        _Segmented, _Slider and _ColourChip are hand-drawn and have no usable
        -state of their own, so they each expose set_enabled and it is
        preferred here. Without it, configure(state=...) raised TclError on the
        Frame, got swallowed, and the "greyed" control stayed fully live --
        which made every group in this panel decorative.
        """
        if widget is None:
            return
        try:
            setter = getattr(widget, "set_enabled", None)
            if callable(setter):
                setter(on)
                return
            widget.configure(state="normal" if on else "disabled")
        except tk.TclError:
            pass

    def _sync_enabled(self, *_):
        """Grey out whatever each reminder's own style ignores.

        Per reminder, which is the whole point of the split: the blink's style
        decides the blink's controls and the break's decides the break's. There
        is no longer a shared set of controls whose liveness one of the two
        styles has to decide on behalf of both.

        Safe with either advanced window shut: those groups only exist while
        their window does, and every lookup defaults to empty.
        """
        for which in self.WHICH:
            style = self._value_of(translated(self.STYLES),
                                   self.V[which]["style"].get())
            centred = self._value_of(
                translated(self.POSITIONS),
                self.V[which]["corner"].get()) == "center"
            placed = style in ("dot", "text")
            for suffix, on in (("dot", style == "dot"),
                               ("text", style == "text"),
                               ("place", placed),
                               ("margin", placed and not centred)):
                for w in self.groups.get(which + "_" + suffix, []):
                    self._enable(w, on)

        on = bool(self.v_break_on.get())
        for w in self.groups.get("break", []):
            self._enable(w, on)
        if not on and self.adv["break"]["win"] is not None:
            # A window full of settings for a switched-off feature is a lie.
            # Closing it says "this belongs to that switch" in one move, and
            # more honestly than greying fourteen widgets in a detached window.
            self._close_advanced("break")

    # -- reactions -----------------------------------------------------------

    def _clamp_interval(self):
        """Snap the field up to the minimum the app will actually accept.

        No preview from here: how often the reminder fires is not something a
        single pulse can show, and firing one every time focus leaves the field
        would be noise.
        """
        unit = self._value_of(translated(self.UNITS), self.v_unit.get())
        every = max(1, self._int(self.v_every, 1))
        if every * unit < MIN_INTERVAL:
            self.v_every.set(-(-MIN_INTERVAL // unit))

    def _language_changed(self):
        """Switch the whole panel over, there and then.

        A language picker whose effect you cannot see until you press Save and
        reopen the window is not a language picker. So this one commits at the
        moment it is touched -- and commits ONLY the language, written to disk
        on its own. Every other edit on screen is carried across into the
        rebuilt panel and the Cancel baseline is carried with it, so pressing
        Cancel afterwards still discards exactly what it would have discarded
        before, and nothing more.

        A rebuild rather than a sweep of configure(text=...) calls: the theme
        bakes its fonts into image elements, three cards measure their own
        labels to place things, and the tab ring is built from widgets. Half a
        translation is worse than none.
        """
        code = self._value_of(LANGUAGES, self.v_lang.get())
        if code == language_code():
            return
        edits, baseline = self.collect(), dict(self.opened_with)
        set_language(code)
        self.app.cfg["language"] = code
        save_config(self.app.cfg)
        log_event("config", "language set to %s" % code)
        self.close()
        self._pending = edits
        self.open()
        baseline["language"] = code
        self.opened_with = baseline

    def _style_changed(self, which="blink"):
        # A reminder's own style decides which of ITS look controls are live.
        # The break's used to decide none of them, because the blink's did.
        self._sync_enabled()
        self._preview(which)

    def _position_changed(self, which="blink"):
        caption = (self.adv.get(which) or {}).get("caption")
        if caption is not None:
            caption.configure(text=self.V[which]["corner"].get())
        # Centring makes the edge margin meaningless, so re-grey.
        self._sync_enabled()
        self._preview(which)

    def _show_volume(self, which):
        """Put one reminder's volume slider and its figure back in step.

        Looked up through self.adv rather than held as an attribute: there are
        two of each of these, and the window either lives in can be closed and
        rebuilt at any time. Redraws the thumb as well as the text, so this is
        correct when driven by a write trace and not only by a drag -- a value
        set any other way used to leave BOTH stale.
        """
        slot = getattr(self, "adv", None) or {}
        slot = slot.get(which) or {}
        sl = slot.get("sl_vol")
        if sl is not None and sl.winfo_exists():
            sl.redraw()
        lab = slot.get("pct_vol")
        if lab is not None and lab.winfo_exists():
            lab.configure(
                text="%d%%" % round(self.V[which]["volume"].get() * 100))

    def _show_pct(self, which="blink"):
        """The figure beside one reminder's strength slider.

        Looked up through self.W rather than held as an attribute, so it is
        simply absent before the card is built instead of raising.
        """
        lab = (self.W.get(which) or {}).get("pct")
        if lab is not None:
            lab.configure(
                text="%d%%" % round(self.V[which]["opacity"].get() * 100))

    def _strength_moved(self, which="blink"):
        self._show_pct(which)
        self._preview(which)

    def _feel_changed(self, which="blink"):
        """Picking a preset rewrites that reminder's advanced numbers to match."""
        V = self.V[which]
        name = self._value_of(feel_pairs(), V["feel"].get())
        if name in FEELS:
            vals = FEELS[name]
            V["hold"].set(round(vals["hold_ms"] / 1000.0, 2))
            V["fade"].set(round(vals["fade_ms"] / 1000.0, 2))
            V["blinks"].set(vals["blinks"])
        self._preview(which)

    def _went_custom(self, which="blink"):
        """Hand-editing the numbers means no preset describes them any more."""
        if self.win is None or not self.win.winfo_exists():
            return
        self.V[which]["feel"].set(T(feel_of(self.collect(), self.PREFIX[which])))
        self._preview(which)

    def _preview(self, which="blink"):
        """Show the change rather than describe it, debounced so dragging the
        slider does not fire a pulse per pixel.

        One debounce slot per reminder: tuning the break must not cancel a
        blink preview that has not fired yet, and must not leave a stale
        after-id in the other slot for close() to cancel.

        Always called through a lambda from a binding, never as command= on a
        <KeyRelease>, which would pass the event object in as `which`.
        """
        if self.win is None or not self.win.winfo_exists():
            return
        job = self.preview_jobs.get(which)
        if job is not None:
            self.app.root.after_cancel(job)
        self.preview_jobs[which] = self.app.root.after(
            600, lambda: self.preview_now(which))

    def preview_now(self, which="blink"):
        """One reminder, straight away.

        Interrupts whatever is on screen first. A preview is a direct answer to
        something the user just changed, so being silently swallowed by a pulse
        already running is the one thing it must never do.
        """
        self.preview_jobs[which] = None
        self.app.overlay.interrupt()
        self.app.overlay.pulse(self.CFG_OF[which](self.collect()))

    def pick_colour(self, which="blink"):
        V = self.V[which]
        chosen = colorchooser.askcolor(color=V["colour"].get(), parent=self.win)
        if chosen and chosen[1]:
            V["colour"].set(chosen[1])
            self.W[which]["chip"].set(chosen[1])
            self._preview(which)

    # -- reading the panel back ---------------------------------------------

    def _ms(self, var, fallback):
        """Seconds in the panel, milliseconds on disk.

        Spinboxes can be left empty or half-typed, so never trust .get().
        """
        try:
            return max(0, int(round(float(var.get()) * 1000)))
        except (tk.TclError, ValueError):
            return fallback

    def collect(self):
        """Every stored key, each read back from the control that owns it.

        The invariant worth keeping: there is no bare `prev[...]` echo in here.
        `prev` appears only as the fallback for a field that is mid-edit. A key
        that echoed the previous value would be a setting with no control --
        which is exactly how break_message, break_hold_ms and break_fade_ms
        came to be stored, written back on every Save, and editable by nobody.
        """
        prev = dict(DEFAULTS)
        prev.update(self.app.cfg)
        every = max(1, self._int(self.v_every, 1))
        unit = self._value_of(translated(self.UNITS), self.v_unit.get())

        out = {
            "start_with_windows": bool(self.v_startup.get()),
            # The CODE, never "auto": picking a language in here is an explicit
            # choice, and it has to survive the user later switching the
            # language Windows itself is displayed in.
            "language": self._value_of(LANGUAGES, self.v_lang.get()),
            "interval_seconds": max(MIN_INTERVAL, every * unit),
            "break_enabled": bool(self.v_break_on.get()),
            "break_minutes": self._int(self.v_break_min, prev["break_minutes"]),
        }
        # The sixteen pulse keys, twice: same controls, same clamps, one set
        # per reminder. Written as a loop so the two can never drift apart.
        for which in self.WHICH:
            p, V = self.PREFIX[which], self.V[which]
            try:
                opacity = round(float(V["opacity"].get()), 3)
            except (tk.TclError, ValueError):
                opacity = prev[p + "opacity"]
            out[p + "style"] = self._value_of(translated(self.STYLES),
                                              V["style"].get())
            out[p + "opacity"] = opacity
            out[p + "hold_ms"] = self._ms(V["hold"], prev[p + "hold_ms"])
            out[p + "fade_ms"] = self._ms(V["fade"], prev[p + "fade_ms"])
            out[p + "gap_ms"] = max(0, self._ms(V["gap"], prev[p + "gap_ms"]))
            out[p + "blinks"] = max(1, self._int(V["blinks"], prev[p + "blinks"]))
            out[p + "colour"] = V["colour"].get()
            out[p + "message"] = V["message"].get()
            out[p + "corner"] = self._value_of(translated(self.POSITIONS),
                                               V["corner"].get())
            out[p + "dot_pct"] = max(1, min(100, self._int(
                V["dot"], prev[p + "dot_pct"])))
            out[p + "font_size"] = max(8, self._int(V["font"], prev[p + "font_size"]))
            out[p + "margin"] = max(0, self._int(V["margin"], prev[p + "margin"]))
            out[p + "all_monitors"] = bool(V["all"].get())
            out[p + "sound_enabled"] = bool(V["sound"].get())
            out[p + "sound_name"] = self._value_of(translated(SOUNDS),
                                                  V["sound_name"].get())
            try:
                volume = round(float(V["volume"].get()), 2)
            except (tk.TclError, ValueError):
                volume = prev[p + "sound_volume"]
            out[p + "sound_volume"] = min(1.0, max(SOUND_VOL_MIN, volume))
        return out

    def save(self):
        self.app.apply(self.collect())
        self.close()

    def cancel(self):
        """Closing used to bin your edits without saying so."""
        if self.collect() != self.opened_with:
            keep = messagebox.askyesno(
                DISPLAY_NAME,
                T("Save the changes you made?"),
                parent=self.win,
            )
            if keep:
                self.save()
                return
        self.close()

    def close(self):
        self._close_advanced()
        for which in self.WHICH:
            job = self.preview_jobs.get(which)
            if job is not None:
                self.app.root.after_cancel(job)
            self.preview_jobs[which] = None
        if self.win is not None:
            self.win.destroy()
            self.win = None


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------


class StartupNotice:
    """The "it is running, you just cannot see it" window.

    A tray-only app that shows nothing on launch is indistinguishable from one
    that failed to launch, which is the first thing a new user gets wrong. This
    says so in plain words and then waits: it has no timeout, because a notice
    that disappears before it is read has not been read.

    Same theme as the settings panel, so the two read as one app.
    """

    # 480 rather than 404. Three of the four things in here overflowed the
    # narrower window in German and French -- the card's one line of advice
    # wants 393px, and "Spendier mir einen Kaffee" 181 of the 116 its button
    # had. A notice is shown once and read once, so it can afford the width.
    WIN_W, WIN_H = 480, 240
    PAD = 20
    BTN_W, SUPPORT_W = 116, 220

    def __init__(self, app):
        self.app = app
        self.win = None
        self.btn_support = None

    def show(self):
        if self.win is not None and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        root = self.app.root
        mode = app_theme_mode()
        ensure_theme(root, mode)
        pal = PALETTES[mode]
        s = _THEME_METRICS["s"]

        self.win = tk.Toplevel(root)
        self.win.title(DISPLAY_NAME)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=pal["ground"])
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.bind("<Return>", lambda e: self.close())
        self.win.bind("<Escape>", lambda e: self.close())

        win_w, win_h = s(self.WIN_W), s(self.WIN_H)
        mx, my, mw, mh = cursor_work_area()
        x = mx + max(0, (mw - win_w) // 2)
        y = my + max(s(34), (mh - win_h) // 3)   # upper third reads as a notice
        self.win.geometry("%dx%d+%d+%d" % (win_w, win_h, x, y))

        outer = ttk.Frame(self.win, style="Ground.TFrame")
        outer.place(x=0, y=0, width=win_w, height=win_h)

        # From DISPLAY_NAME, not a literal. It WAS a literal, and it still read
        # "Blink Reminder is running" three renames later -- the same bug the
        # tray tooltip had, in the one window a first-time user is shown.
        ttk.Label(outer, text=T("%s is running") % DISPLAY_NAME,
                  style="Title.TLabel").place(x=s(20), y=s(20))
        ttk.Label(outer, style="Sub.TLabel", justify="left",
                  text=T("It stays in the background and will nudge you to "
                         "blink\n%s.")
                       % describe_interval(self.app.cfg["interval_seconds"])).place(
            x=s(20), y=s(54))

        # Everything below hangs off PAD and the window width rather than off
        # literals, so the window can be widened for a longer language in one
        # place instead of five.
        inner = self.WIN_W - 2 * self.PAD
        card = ttk.Frame(outer, style="Card.TFrame")
        card.place(x=s(self.PAD), y=s(112), width=s(inner), height=s(52))
        ttk.Label(card,
                  text=T("Right-click the tray icon, by the clock, "
                         "for settings."),
                  style="Row.TLabel").place(x=s(16), y=s(16))

        ttk.Frame(outer, style="Rule.TFrame").place(
            x=s(self.PAD), y=s(184), width=s(inner), height=max(1, s(1)))

        # Opposite end of the footer from "Got it", so the eye reaches the
        # dismiss button first and the ask second. Absent when unconfigured.
        if SUPPORT_URL:
            self.btn_support = ttk.Button(
                outer, text=T("Buy me a coffee"), style="Secondary.TButton",
                command=lambda: open_link(SUPPORT_URL))
            self.btn_support.place(x=s(self.PAD), y=s(196),
                                   width=s(self.SUPPORT_W), height=s(32))

        self.btn = ttk.Button(outer, text=T("Got it"), style="Primary.TButton",
                              command=self.close)
        self.btn.place(x=s(self.WIN_W - self.PAD - self.BTN_W), y=s(196),
                       width=s(self.BTN_W), height=s(32))

        self.win.update_idletasks()
        if pal["dark_titlebar"]:
            use_dark_titlebar(self.win)
        self.win.lift()
        self.win.focus_force()
        self.btn.focus_set()

    def close(self):
        if self.win is not None:
            self.win.destroy()
            self.win = None


class App:
    def __init__(self, cfg=None):
        # main() has usually loaded it already, since loading is what settles
        # the language. The default keeps App() constructible on its own, which
        # is how every test in this project builds one.
        self.cfg = cfg if cfg is not None else load_config()
        self.paused = False
        self.timer = None
        self.break_timer = None
        self.snooze_job = None
        self.commands = queue.Queue()

        self.root = tk.Tk()
        self.root.withdraw()
        # First, so that anything raised by the lines below is still reported.
        install_error_reporting(self.root)
        # Before any Toplevel exists, so every window that opens later inherits
        # the icon rather than being fixed up one at a time.
        set_taskbar_identity()
        set_window_icon(self.root)
        self.overlay = Overlay(self.root)
        self.indicator = RunningIndicator(self.root)
        self.countdown = CountdownLabel(self.root)
        # The countdown hides with the dots: while a reminder is on screen it
        # would be counting down to something already happening.
        self.indicator.on_leave = self.countdown.suppress
        self.indicator.on_park = self.countdown.resume
        self.overlay.indicator = self.indicator
        self.indicator.apply(self.cfg)
        self.settings = SettingsWindow(self)
        self.notice = StartupNotice(self)

        sync_startup(self.cfg["start_with_windows"])
        self.icon = self.build_tray()
        threading.Thread(target=self.icon.run, daemon=True).start()

        self.last_fire = time.monotonic()
        self.last_beat = time.monotonic()
        # The language is in here because it is the first thing worth knowing
        # about a report of "the text is wrong": both what was asked for and
        # what that resolved to, since "auto" can resolve differently on two
        # machines with the same config file.
        log_event("start", "interval=%ss style=%s startup=%s lang=%s(%s)"
                  % (self.cfg["interval_seconds"], self.cfg["style"],
                     self.cfg["start_with_windows"],
                     self.cfg.get("language"), language_code()))

        self.root.after(120, self.drain)
        self.root.after(200, self.indicator.show)
        self.root.after(260, self.tick_countdown)
        # Deferred so the tray icon it points at already exists on screen.
        self.root.after(400, self.notice.show)
        self.root.after(HEARTBEAT_S * 1000, self.heartbeat)
        self.schedule()
        self.schedule_break()

    # -- tray ---------------------------------------------------------------

    def build_tray(self):
        import pystray

        # In colour, not the flat white the tray used to get. That white was
        # the right answer for a two-tone eye, which could turn to mud on an
        # unknown taskbar; this mark is one colour, and measured side by side
        # the teal is clearly legible on BOTH the dark and the light Windows 11
        # taskbar while white all but disappears on the light one.
        img = app_icon(64)

        def push(name):
            return lambda *_: self.commands.put(name)

        # Every label is a callable, not a string. pystray asks for the text
        # each time the menu is opened, so the one menu built at startup
        # follows a language change made in Settings -- where a fixed string
        # would have kept its launch-time language until the app restarted.
        items = [
            pystray.MenuItem(lambda _i: T("Blink now"), push("blink"),
                             default=True),
            # One item, not two. There used to be a "Paused" checkbox beside
            # this, which is the same idea with no end to it -- and snooze's own
            # docstring gives the reason that is wrong: "indefinite pause is how
            # people forget they turned it off". The label reads the state, so
            # the one item both starts a snooze and cancels one early.
            pystray.MenuItem(
                lambda _i: (T("Resume reminders") if self.paused
                            else T("Snooze 30 minutes")),
                push("snooze")),
            pystray.MenuItem(lambda _i: T("Settings"), push("settings")),
        ]
        # Built as a list rather than inline so the support item can be absent
        # entirely. An item that opens nothing is worse than no item.
        if SUPPORT_URL:
            items += [pystray.Menu.SEPARATOR,
                      pystray.MenuItem(lambda _i: T("Buy me a coffee"),
                                       push("support"))]
        items += [pystray.Menu.SEPARATOR,
                  pystray.MenuItem(lambda _i: T("Quit"), push("quit"))]
        # Tooltip comes from DISPLAY_NAME, not a literal. It was a literal, and
        # it still read "Blink Reminder" two renames later -- the one string a
        # user hovers over was the last one telling them the old name.
        return pystray.Icon(APP_NAME, img, DISPLAY_NAME,
                            pystray.Menu(*items))

    def drain(self):
        """Tray runs on another thread, so commands are marshalled here."""
        try:
            while True:
                cmd = self.commands.get_nowait()
                if cmd == "blink":
                    log_event("tray", "blink now")
                    self.overlay.pulse(blink_cfg(self.cfg))
                elif cmd == "snooze":
                    # The same item both ways round, so a snooze can be taken
                    # back without waiting out the half hour.
                    if self.paused:
                        log_event("tray", "resumed early")
                        self.wake()
                    else:
                        self.snooze(30)
                elif cmd == "settings":
                    self.settings.open()
                elif cmd == "support":
                    log_event("tray", "opened the support link")
                    open_link(SUPPORT_URL)
                elif cmd == "quit":
                    self.quit()
                    return
        except queue.Empty:
            pass
        except Exception:
            # Same trap as fire(): without this the tray stops responding.
            log_error("drain")
        self.root.after(120, self.drain)

    # -- timing -------------------------------------------------------------

    def tick_countdown(self):
        """Refresh the pill once a second. Cheap, and re-read from the clock
        each time so it cannot drift away from the real schedule."""
        try:
            if self.cfg.get("break_enabled") and not self.paused:
                left = seconds_to_next_break(self.cfg["break_minutes"])
                self.countdown.set_text("%d:%02d" % (left // 60, left % 60))
            else:
                self.countdown.set_text(None)
        except Exception:
            log_error("tick_countdown")
        finally:
            self.root.after(1000, self.tick_countdown)

    def schedule_break(self):
        """Aim at the next wall-clock boundary, recomputed every time."""
        if self.break_timer is not None:
            self.root.after_cancel(self.break_timer)
            self.break_timer = None
        if not self.cfg.get("break_enabled"):
            return
        wait = seconds_to_next_break(self.cfg["break_minutes"])
        self.break_timer = self.root.after(int(wait * 1000), self.break_fire)

    def break_fire(self):
        """Same finally-clause discipline as fire(): an exception here must not
        be able to end the break schedule for the life of the process."""
        self.break_timer = None
        try:
            if not self.paused:
                log_event("break", "every %d min, look away"
                          % self.cfg["break_minutes"])
                # A blink may be mid-pulse. The break wins, and the blink timer
                # is pushed out so one does not tread on the heels of the other.
                self.overlay.interrupt()
                self.overlay.pulse(break_cfg(self.cfg))
                self.schedule()
            else:
                log_event("break", "skipped, reminders paused")
        except Exception:
            log_error("break_fire")
        finally:
            self.schedule_break()

    def snooze(self, minutes):
        """Pause, but with an end to it. Indefinite pause is how people forget
        they turned it off."""
        self.paused = True
        self.cancel_snooze()
        self.snooze_job = self.root.after(int(minutes) * 60000, self.wake)
        self.schedule()

    def wake(self):
        """Resume, whether the snooze ran out or the user ended it early.

        Cancels its own timer, so resuming early cannot leave an after-job that
        fires at the original half-hour mark and silently restarts the blink
        clock from there.
        """
        self.cancel_snooze()
        self.paused = False
        self.schedule()

    def cancel_snooze(self):
        if self.snooze_job is not None:
            self.root.after_cancel(self.snooze_job)
            self.snooze_job = None

    def heartbeat(self):
        """A reminder every 45s cannot tell a stalled timer from a quiet one.
        This ticks regardless, so sleep and background throttling show up as a
        gap that is nobody's fault but Windows'."""
        now = time.monotonic()
        drift = now - self.last_beat - HEARTBEAT_S
        self.last_beat = now
        if drift > STALL_TOLERANCE_S:
            log_event("stalled", "timer paused ~%.0fs (sleep or throttling)"
                      % (HEARTBEAT_S + drift))
        self.root.after(HEARTBEAT_S * 1000, self.heartbeat)

    def schedule(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        if self.paused:
            return
        self.timer = self.root.after(self.cfg["interval_seconds"] * 1000, self.fire)

    def fire(self):
        """An exception here used to skip schedule() and end reminders for the
        life of the process, silently. The finally clause is the whole fix."""
        self.timer = None
        retry = False
        try:
            if not self.paused:
                if self.overlay.busy:
                    # A break is on screen and wins. That precedence is right,
                    # but throwing the blink away was not: it is pushed out and
                    # tried again, the way break_fire pushes this timer out.
                    retry = True
                    log_event("fire", "overlay busy; blink pushed out %dms"
                              % BLINK_RETRY_MS)
                else:
                    now = time.monotonic()
                    gap = now - self.last_fire
                    self.last_fire = now
                    log_event("fire", "gap=%.1fs expected=%ss"
                              % (gap, self.cfg["interval_seconds"]))
                    self.overlay.pulse(blink_cfg(self.cfg))
        except Exception:
            log_error("fire")
        finally:
            if retry:
                self.timer = self.root.after(BLINK_RETRY_MS, self.fire)
            else:
                self.schedule()

    def apply(self, cfg):
        startup_changed = cfg["start_with_windows"] != self.cfg["start_with_windows"]
        self.cfg = cfg
        save_config(cfg)
        self.indicator.apply(cfg)
        self.countdown.render()
        self.schedule_break()
        if startup_changed:
            set_startup(cfg["start_with_windows"])
        self.schedule()

    def quit(self):
        log_event("quit", "asked to quit from the tray")
        try:
            self.icon.stop()
        except Exception:
            pass  # shutting down anyway; a stuck tray icon outlives us
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    # Loaded before the single-instance check rather than inside App, because
    # loading it is what puts the user's language in force -- and the copy that
    # LOSES that check exits through announce_already_running, which has a
    # sentence to say to them, in their own language.
    cfg = load_config()
    if already_running():
        log_event("start", "another copy is already running; this one exited")
        announce_already_running()
        return
    enable_dpi_awareness()
    App(cfg).run()


if __name__ == "__main__":
    main()
