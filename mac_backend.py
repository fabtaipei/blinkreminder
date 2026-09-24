# -*- coding: utf-8 -*-
"""The macOS equivalent of the Win32 half of blink_reminder.py -- UNTESTED.

This file has never run. It was written on a Windows machine with no macOS
access; every claim below about how it behaves is a claim about the
Objective-C APIs it calls, not about what has actually been observed on
screen. Read macsmoke.py first -- it is the ten-second test that tells you
whether the one hard trick this file depends on actually works before you
trust anything else in here.

WHY A SEPARATE FILE, NOT A BRANCH INSIDE blink_reminder.py

The Windows Overlay pulls off its click-through, never-focus-stealing panes
with a Tk Canvas plus `-transparentcolor` (colour-keyed transparency) and raw
Win32 (SetWindowLongW, WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE).
`-transparentcolor` is itself a Windows-only Tk attribute -- it does not
exist on macOS Tk at all, so this was never a matter of swapping out the
ctypes calls underneath the same Canvas code. macOS needs its own window and
its own drawing, from a different toolkit (AppKit/Cocoa via PyObjC), not a
platform branch inside the Tk implementation. This file is that toolkit, kept
separate so the Windows app -- and its passing test suite -- is untouched by
any of it.

THE ONE HARD TRICK, AND WHAT GROUNDS IT

A window that customers must be able to click through, that never takes
keyboard focus, and that stays visible across every Space: on macOS this is
   window.setIgnoresMouseEvents_(True)
   window.setCollectionBehavior_(CanJoinAllSpaces | Stationary | IgnoresCycle)
   window.setLevel_(NSFloatingWindowLevel)
   NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
plus a panel styled NSWindowStyleMaskNonactivatingPanel so it never becomes
the key window in the first place. Each of `ignoresMouseEvents`,
`collectionBehavior` and `setActivationPolicy_` is Apple's own documented
AppKit API, and a working combination of them (confirmed by a real project
reading its own window's flags back after calling them:
collectionBehavior=337, level set, ignoresMouseEvents=True) is described in
yuki-f-saka/live-football-transcriber PR #22. That PR used
NSScreenSaverWindowLevel to paint over other apps' fullscreen video, which
this app deliberately does not attempt -- the Windows build already treats
"does not fight a fullscreen game" as a feature (medium integrity, on
purpose; see certification-notes.md), so this uses the gentler
NSFloatingWindowLevel instead.

WHAT IS AND ISN'T PROVEN

Proven, in the sense of "a working example exists that reads its own flags
back correctly": ignoresMouseEvents + collectionBehavior + a floating level
on an NSWindow, together, hold.

NOT proven, because nothing here has been run: whether an NSPanel with
NSWindowStyleMaskNonactivatingPanel behaves identically for this purpose
(it should -- it is the documented style bit for exactly this case -- but
"should" is not "does"); the NSScreen coordinate flip below; NSSound
playback from a PyInstaller-bundled path; and SMAppService registration
against a PyInstaller .app bundle specifically.

If any of it is wrong, macsmoke.py is where that shows up first, cheaply,
before it is wired into the rest of the app.
"""
import math
import os
import sys

if sys.platform != "darwin":
    raise ImportError("mac_backend is macOS-only; blink_reminder.py must not "
                      "import it on any other platform")

import objc
from AppKit import (
    NSApp, NSApplication, NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered, NSBezierPath, NSColor, NSFloatingWindowLevel,
    NSFont, NSPanel, NSScreen, NSString, NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorIgnoresCycle,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless, NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSMakeRect, NSObject

try:
    from ServiceManagement import SMAppService
    _HAVE_SM_APP_SERVICE = True
except ImportError:
    # SMAppService needs macOS 13+. Older systems fall back to a LaunchAgent
    # plist -- see set_startup() below. Not the common case by 2026, but a
    # port that hard-crashes on an older OS is worse than one that degrades.
    _HAVE_SM_APP_SERVICE = False

try:
    from AppKit import NSSound
except ImportError:
    NSSound = None


LOGIN_ITEM_ID = "com.kennytechy.dryeyesblinkreminderlite"
LAUNCH_AGENT_PLIST = os.path.expanduser(
    "~/Library/LaunchAgents/%s.plist" % LOGIN_ITEM_ID)

_OVERLAY_COLLECTION = (
    NSWindowCollectionBehaviorCanJoinAllSpaces
    | NSWindowCollectionBehaviorStationary
    | NSWindowCollectionBehaviorIgnoresCycle
)


def _ensure_nsapp():
    """A PyInstaller --windowed .app already has an NSApplication; a bare
    script run via `python3 mac_backend.py` for a quick manual check does
    not, and every AppKit call here needs one to exist first."""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    return app


def monitor_areas():
    """Every screen as (x, y, w, h, dpi, primary, wx, wy, ww, wh).

    Same shape as the Windows monitor_areas() in blink_reminder.py, so the
    geometry math in reminder_rect() and _corner_slot() -- which is plain
    arithmetic, no Win32 in it -- can be reused unchanged once this is wired
    in.

    TWO TRANSLATIONS, NEITHER OF WHICH WINDOWS NEEDS:

    Coordinates. NSScreen's origin is the BOTTOM-left of the primary screen,
    Y increasing upward -- the opposite of Win32's top-left-origin, Y
    increasing downward that the rest of this app assumes. Every rectangle
    below is flipped into that top-left convention before it leaves this
    function, so nothing downstream has to know macOS did anything
    differently. Get this backwards and a monitor arrangement silently
    renders upside down relative to reality -- it fails quietly, not loudly,
    which is exactly the kind of bug this project has been bitten by before
    with unverified platform assumptions (see the ctypes argtypes history in
    blink_reminder.py).

    DPI. macOS reports backingScaleFactor (1.0, or 2.0 on Retina), not a DPI
    number. It is scaled to 96 * factor here purely so downstream code that
    already expects "96 is 100%" (reminder_rect, the SettingsWindow's s()
    scaler) keeps working without a second unit system to reason about. This
    is a modelling choice, not a fact about macOS -- flag it if it ever
    causes a mismatch against how Retina scaling actually behaves in practice.
    """
    screens = NSScreen.screens()
    if not screens:
        return []
    primary = screens[0]
    primary_h = primary.frame().size.height

    def flip(rect):
        x = rect.origin.x
        top = primary_h - (rect.origin.y + rect.size.height)
        return x, top, rect.size.width, rect.size.height

    out = []
    for i, s in enumerate(screens):
        x, y, w, h = flip(s.frame())
        wx, wy, ww, wh = flip(s.visibleFrame())
        dpi = int(round(96 * s.backingScaleFactor()))
        out.append((int(x), int(y), int(w), int(h), dpi, i == 0,
                    int(wx), int(wy), int(ww), int(wh)))
    return out


class _ClickThroughPanel(NSPanel):
    """An NSPanel that refuses to become key or main, belt-and-suspenders
    alongside NSWindowStyleMaskNonactivatingPanel. The style mask should be
    sufficient on its own; overriding both costs nothing and this project has
    learned not to trust a single, unverified platform guarantee."""

    def canBecomeKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False


def _make_overlay_window(x, y, w, h):
    """One borderless, click-through, always-visible panel at a screen rect
    already given in the flipped (top-left-origin) convention monitor_areas()
    returns -- converted back to AppKit's bottom-left convention here, once,
    at the only point that has to know both systems exist."""
    screens = NSScreen.screens()
    primary_h = screens[0].frame().size.height if screens else h
    ns_y = primary_h - (y + h)

    panel = _ClickThroughPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(x, ns_y, w, h),
        NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
        NSBackingStoreBuffered,
        False,
    )
    panel.setOpaque_(False)
    panel.setBackgroundColor_(NSColor.clearColor())
    panel.setHasShadow_(False)
    panel.setIgnoresMouseEvents_(True)
    panel.setCollectionBehavior_(_OVERLAY_COLLECTION)
    panel.setLevel_(NSFloatingWindowLevel)
    return panel


def _nscolor(hex_colour):
    """'#RRGGBB' -> NSColor. The app's own colour picker only ever produces
    this format, so no other input shape is handled."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0)


class _PaneView(NSView):
    """Draws exactly one pulse's content: a dim wash, a dot, or a word.

    A plain drawRect_, not a CALayer animation -- v1 aims for "correctly
    visible, correctly positioned, genuinely click-through", not for
    reproducing the Windows build's fade/hold/gap pulse timing pixel for
    pixel. That refinement is worth doing once the fundamentals are confirmed
    on real hardware, not before.
    """

    def setContent_(self, content):
        self._content = content
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        content = getattr(self, "_content", None)
        if content is None:
            return
        style, colour, message, opacity, font_size = content
        col = _nscolor(colour)
        if style == "dim":
            col.colorWithAlphaComponent_(opacity).set()
            NSBezierPath.fillRect_(rect)
        elif style == "dot":
            col.colorWithAlphaComponent_(opacity).set()
            inset = 2
            oval = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(inset, inset, rect.size.width - inset * 2,
                          rect.size.height - inset * 2))
            oval.fill()
        else:  # "text"
            font = NSFont.systemFontOfSize_(font_size)
            attrs = {"NSColor": col.colorWithAlphaComponent_(opacity),
                    "NSFont": font}
            s = NSString.stringWithString_(message)
            size = s.sizeWithAttributes_(attrs)
            px = (rect.size.width - size.width) / 2.0
            py = (rect.size.height - size.height) / 2.0
            s.drawAtPoint_withAttributes_((px, py), attrs)


class Overlay:
    """Matches blink_reminder.Overlay's call shape (pulse(cfg), interrupt(),
    .indicator) so wiring this in later is a platform-selection line, not a
    rewrite of App. See the module docstring for what's simplified in this
    first pass versus the Windows original.
    """

    def __init__(self):
        _ensure_nsapp()
        self.panes = []
        self.active = []
        self.indicator = None
        self._job = None

    def _panes_for(self, n):
        while len(self.panes) < n:
            win = _make_overlay_window(0, 0, 10, 10)
            view = _PaneView.alloc().initWithFrame_(NSMakeRect(0, 0, 10, 10))
            win.setContentView_(view)
            self.panes.append((win, view))
        return self.panes[:n]

    def interrupt(self):
        if self.active:
            self._hide_all()

    def _hide_all(self):
        for win, _view in self.active:
            win.orderOut_(None)
        self.active = []
        if self.indicator is not None:
            self.indicator.show()

    def pulse(self, cfg):
        """A single held pulse, on every monitor cfg asks for. No blinks/gap
        choreography yet -- see the class docstring."""
        mons = [m for m in monitor_areas() if cfg.get("all_monitors") or m[5]]
        panes = self._panes_for(len(mons))
        self.active = []
        for (win, view), mon in zip(panes, mons):
            x, y, w, h = _reminder_rect(mon, cfg)
            ns_y = _flip_y(y, h)
            win.setFrame_display_(NSMakeRect(x, ns_y, w, h), True)
            view.setFrame_(NSMakeRect(0, 0, w, h))
            view.setContent_((cfg["style"], cfg["colour"],
                             cfg.get("message", ""), cfg.get("opacity", 0.6),
                             cfg.get("font_size", 20)))
            win.orderFrontRegardless()
            self.active.append((win, view))
        if self.indicator is not None:
            self.indicator.hide()
        hold_s = (int(cfg.get("hold_ms", 800)) + 2 * int(cfg.get("fade_ms", 0))) / 1000.0
        self._schedule(max(0.3, hold_s), self._hide_all)

    def _schedule(self, seconds, fn):
        from Foundation import NSTimer
        self._job = NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            seconds, False, lambda t: fn())


def _flip_y(y, h):
    screens = NSScreen.screens()
    primary_h = screens[0].frame().size.height if screens else (y + h)
    return primary_h - (y + h)


def _reminder_rect(mon, cfg):
    """A deliberately small reimplementation of blink_reminder.reminder_rect
    for this preview module, so mac_backend.py has no import-time dependency
    on blink_reminder.py. Once wired in for real, this should be DELETED and
    the real reminder_rect (which already handles every corner + centre case
    and is unit-tested) used instead -- duplicating geometry logic across two
    files is exactly the kind of drift this project has paid for before.
    """
    x, y, w, h, dpi, primary, wx, wy, ww, wh = mon
    scale = dpi / 96.0
    if cfg["style"] == "dim":
        return x, y, w, h
    size = int(cfg.get("dot_size", 72) * scale)
    margin = int(cfg.get("margin", 48) * scale)
    corner = cfg.get("corner", "center")
    if corner == "center":
        cx, cy = wx + ww // 2, wy + wh // 2
    else:
        cx = wx + margin if "left" in corner else wx + ww - margin
        cy = wy + margin if "top" in corner else wy + wh - margin
    return cx - size // 2, cy - size // 2, size, size


class RunningIndicator:
    """A small always-on dot per screen. No fly-to-target animation in this
    pass -- apply()/show()/hide() are enough to prove the mechanism; the
    Windows build's flight choreography is a refinement layered on top once
    the basics are confirmed working."""

    def __init__(self):
        _ensure_nsapp()
        self.cfg = None
        self.pips = []
        self.on_leave = None
        self.on_park = None

    def apply(self, cfg):
        self.cfg = cfg
        if self.pips:
            self.show()

    def show(self):
        if self.cfg is None:
            return
        mons = monitor_areas()
        size = 10
        while len(self.pips) < len(mons):
            win = _make_overlay_window(0, 0, size, size)
            view = _PaneView.alloc().initWithFrame_(NSMakeRect(0, 0, size, size))
            win.setContentView_(view)
            self.pips.append((win, view))
        for (win, view), mon in zip(self.pips, mons):
            x, y, w, h, *_rest, wx, wy, ww, wh = mon
            px, py = wx + ww - size - 12, wy + wh - size - 12
            ns_y = _flip_y(py, size)
            win.setFrame_display_(NSMakeRect(px, ns_y, size, size), True)
            view.setFrame_(NSMakeRect(0, 0, size, size))
            view.setContent_(("dot", self.cfg["colour"], "", 0.85, 0))
            win.orderFrontRegardless()
        if self.on_park:
            self.on_park()

    def hide(self):
        for win, _view in self.pips:
            win.orderOut_(None)
        if self.on_leave:
            self.on_leave()


class CountdownLabel:
    """A small text panel above the indicator dot. Suppressed while the
    indicator is away (mid-reminder) so it never floats over empty space."""

    def __init__(self):
        _ensure_nsapp()
        self.win = _make_overlay_window(0, 0, 90, 24)
        self.view = _PaneView.alloc().initWithFrame_(NSMakeRect(0, 0, 90, 24))
        self.win.setContentView_(self.view)
        self._text = ""

    def set_text(self, text):
        self._text = text
        self.view.setContent_(("text", "#FFFFFF", text, 0.9, 12))
        self.win.orderFrontRegardless()

    def suppress(self):
        self.win.orderOut_(None)

    def resume(self):
        if self._text:
            self.win.orderFrontRegardless()


def play_sound(path):
    """NSSound, not afplay-in-a-subprocess: no process spawn per reminder,
    and NSSound.play() returns immediately (async), matching how
    winsound.PlaySound(..., SND_MEMORY|SND_ASYNC) behaves on Windows -- a
    reminder sound must never block the pulse waiting for playback to finish.
    """
    if NSSound is None or not os.path.exists(path):
        return
    snd = NSSound.alloc().initWithContentsOfFile_byReference_(path, True)
    if snd is not None:
        snd.play()


def set_startup(enabled):
    """SMAppService (macOS 13+) is tried first; a LaunchAgent plist is the
    fallback for anything older. Register() requires the caller to be a
    properly bundled, LaunchServices-registered .app -- which is what
    PyInstaller's --windowed output on macOS actually produces, not a bare
    executable -- but that pairing has not been exercised end to end."""
    if _HAVE_SM_APP_SERVICE:
        svc = SMAppService.mainAppService()
        if enabled:
            svc.registerAndReturnError_(None)
        else:
            svc.unregisterAndReturnError_(None)
        return

    if enabled:
        exe = sys.executable
        plist = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
                "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
                "<plist version=\"1.0\"><dict>\n"
                "<key>Label</key><string>%s</string>\n"
                "<key>ProgramArguments</key><array><string>%s</string></array>\n"
                "<key>RunAtLoad</key><true/>\n"
                "</dict></plist>\n" % (LOGIN_ITEM_ID, exe))
        os.makedirs(os.path.dirname(LAUNCH_AGENT_PLIST), exist_ok=True)
        with open(LAUNCH_AGENT_PLIST, "w", encoding="utf-8") as fh:
            fh.write(plist)
        os.system('launchctl load -w "%s"' % LAUNCH_AGENT_PLIST)
    else:
        if os.path.exists(LAUNCH_AGENT_PLIST):
            os.system('launchctl unload -w "%s"' % LAUNCH_AGENT_PLIST)
            os.remove(LAUNCH_AGENT_PLIST)


def startup_enabled():
    if _HAVE_SM_APP_SERVICE:
        # .status is an enum; 1 == SMAppServiceStatusEnabled.
        return SMAppService.mainAppService().status() == 1
    return os.path.exists(LAUNCH_AGENT_PLIST)
