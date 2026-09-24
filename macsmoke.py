# -*- coding: utf-8 -*-
"""The one thing to run before trusting anything else about the Mac port.

    python3 -m pip install pyobjc
    python3 macsmoke.py

Deliberately standalone -- it does not import mac_backend.py, so a bug
anywhere else in that file cannot stop this from giving a real answer about
the one thing it tests: can this Mac show a window that a person can click
straight through, that never steals keyboard focus, and that survives a
Space switch. Everything else in the port (the overlay, the indicator, the
countdown, sound, login items) is built on this working. If it doesn't, none
of the rest is worth wiring in yet.

WHAT TO DO WHEN IT RUNS

An amber square appears near the top-left of the main screen. With it up:

  1. Click on whatever is underneath it (a Finder window, desktop icons).
     If the click reaches that window instead of the square, it's click-
     through. If the square receives the click, it's not.
  2. Look at the menu bar and Dock. Nothing should change -- no new item
     highlighted, no app becoming "active". If a "macsmoke" entry appears
     as the frontmatch app, it's stealing focus.
  3. Swipe to another Space (Mission Control), or Cmd-Tab to another app,
     then back. The square should still be exactly where it was.
  4. Type a few keystrokes into whatever app you had open before running
     this. They should go there, not vanish or do nothing.

It prints what it actually set the window's flags to before you even look,
and closes itself after 20 seconds -- or press Ctrl+C in the terminal.
"""
import sys

if sys.platform != "darwin":
    raise SystemExit("this is a macOS-only check")

from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory, NSBackingStoreBuffered,
    NSColor, NSFloatingWindowLevel, NSMakeRect, NSPanel, NSScreen,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorIgnoresCycle, NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless, NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSTimer
from PyObjCTools import AppHelper


class _NeverKeyPanel(NSPanel):
    def canBecomeKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    screen = NSScreen.screens()[0]
    sw = screen.frame().size.width
    sh = screen.frame().size.height
    size = 120
    # Cocoa's origin is bottom-left; placing this near the top-left of the
    # screen means a high y value, not zero.
    rect = NSMakeRect(60, sh - size - 60, size, size)

    panel = _NeverKeyPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        rect,
        NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
        NSBackingStoreBuffered,
        False,
    )
    panel.setOpaque_(False)
    panel.setBackgroundColor_(
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85, 0.60, 0.13, 0.92))
    panel.setHasShadow_(False)
    panel.setIgnoresMouseEvents_(True)
    panel.setCollectionBehavior_(
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorStationary
        | NSWindowCollectionBehaviorIgnoresCycle
    )
    panel.setLevel_(NSFloatingWindowLevel)
    panel.orderFrontRegardless()

    print("window flags read back after setting them:")
    print("  ignoresMouseEvents :", panel.ignoresMouseEvents())
    print("  collectionBehavior :", panel.collectionBehavior())
    print("  level              :", panel.level())
    print("  canBecomeKeyWindow :", panel.canBecomeKeyWindow())
    print()
    print("amber square is up. Follow the checklist in this file's docstring.")
    print("Closing automatically in 20 seconds -- or Ctrl+C now.")

    def _stop(_timer):
        print("done.")
        AppHelper.stopEventLoop()

    NSTimer.scheduledTimerWithTimeInterval_repeats_block_(20.0, False, _stop)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
