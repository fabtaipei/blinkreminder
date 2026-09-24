# Dry Eyes Blink Reminder Lite

A tray app for two things: a brief cue to blink, and a separate reminder to
look away from the screen for a moment. Both are click-through — they never
take focus and never interrupt what you're doing.

Windows 10/11, 64-bit. [Also on the Microsoft Store](https://apps.microsoft.com/detail/9NBRV5W24KH5)
(same app, auto-updating, no SmartScreen prompt). macOS is in progress —
see [macOS](#macos) below.

## Why

Staring at a screen drops your blink rate by more than half, and the blinks
that do happen are often partial — the lid never fully closes, so the tear
film never gets renewed. The fix isn't treatment, it's interruption: a cue
regular enough to catch, gentle enough not to break concentration every time.

This app is deliberately two separate things, not one:

- **Blink** — a short, frequent nudge. Anything from a few seconds upward.
- **Break** — a longer, rarer nudge to look into the distance, on the wall
  clock rather than a timer from launch, so it lands at tidy times (e.g.
  `:00` and `:30`) no matter when you started the app. This is the practical
  form of the "20-20-20" rule some people already know.

Each has entirely independent settings. Changing one never touches the
other.

## Installing (portable build)

1. Download the latest `.exe` from [Releases](../../releases).
2. Put it somewhere permanent — `C:\Users\<you>\Apps\` is fine. **Not** your
   Downloads folder, and not a USB stick.
3. Double-click it. Windows will show **"Windows protected your PC"** — this
   is SmartScreen reacting to an unsigned app from an unknown publisher, not
   a virus warning. Click **More info**, then **Run anyway**. (The Microsoft
   Store build doesn't show this at all, if you'd rather install that way.)
4. An amber ring appears in the system tray, next to the clock. You may need
   the `^` arrow to see it. Right-click it for **Settings**.

Nothing is written outside your own user folder, and the app does not touch
Startup unless you tick **Start with Windows** yourself.

## What it does

Two independent reminders, each with its own timing, look and sound:

| | Blink | Break |
| --- | --- | --- |
| Fires | on an interval you set | on the wall clock (e.g. every 30 min, landing on `:00`/`:30`) |
| Default style | a small dot | a screen dim |
| Also available | a word, or a dim | a dot, or a word |

A small indicator dot sits in the corner of each screen with a countdown to
the next break, so a tray-only app never looks like it's failed to start.
Reminders appear on every connected monitor, correctly sized even across
different display scaling, and every overlay is click-through: it never
takes keyboard focus and never blocks a mouse click meant for whatever's
underneath it.

## Settings

Right-click the tray icon, then **Settings**. Each reminder has its own card:

| Setting | What it does |
| --- | --- |
| Remind me every / on the hour | Interval (blink) or wall-clock cadence (break) |
| Style | `dot`, `text`, or `dim` |
| Strength | Opacity of the dim, or how solid the dot/text is |
| Colour | Colour of the dim, dot, or text |
| Sound | Four built-in sounds, each with its own volume, or silent |
| Advanced settings | Size, position, pulse count, fade/hold timing |
| Show on every monitor | Off means primary screen only |
| Start with Windows | Adds or removes a Startup shortcut |

**Preview blink** / **Preview break** show the current settings without
saving. **Save** applies them.

Settings live in `%APPDATA%\BlinkReminder\config.json`. The reminder pulse
is rate-limited in code so that no combination of settings can exceed three
flashes per second (WCAG 2.3.1) — a photosensitivity floor a user cannot
accidentally configure their way past.

## Notes

- **If you move the exe after ticking "Start with Windows"**, the shortcut
  will point at the old location. Untick and retick the box to repair it.
- Task Manager shows two entries for the app. That's normal for a
  single-file build: one is the launcher, one is the app.
- First launch takes a second or two while the exe unpacks itself. Later
  launches are quicker.
- Overlays run at medium integrity and correctly do **not** paint over UAC
  prompts, other elevated windows, or exclusive-fullscreen games. That's
  intended behaviour, not a bug.

## Uninstalling

1. Untick **Start with Windows** in Settings.
2. Right-click the tray icon and choose **Quit**.
3. Delete the exe, and delete `%APPDATA%\BlinkReminder` if you want the
   settings gone too.

## Privacy

No account, no sign-in, no advertising, no analytics, no network connection
of any kind — the app never contacts any server, including its own
developer's. It does not use the camera; it works on a timer, it does not
watch you. Full policy: [store/privacy-policy.md](store/privacy-policy.md).

## Building from source (Windows)

Needs Python 3.10+, then:

    py -m pip install pystray pillow pyinstaller
    py build.py

Output lands in `dist\Dry Eyes Blink Reminder Lite.exe`. `build.py` generates
the icon and the exe's version resource, so `blink_reminder.py` and
`build.py` are the only tracked sources that matter for a Windows build.

To run without building: `pythonw blink_reminder.py` (`pythonw`, not
`python`, so no console window appears).

CI (`.github/workflows/build-windows.yml`) runs the same `build.py` on every
push, and attaches the exe to a GitHub Release on any `v*` tag.

## macOS

**In progress, unverified on real hardware.** No Mac was available to test
any of this while it was written — it's a real attempt, not a finished port,
and the honest state of it matters more here than in any other section.

**Run this first**, on any Mac:

    python3 -m pip install -r requirements-mac.txt
    python3 macsmoke.py

Ten seconds, one window, nothing else needed. It exists to answer exactly
one question before any more time is spent on the rest: can this Mac show a
window that's genuinely click-through, never steals keyboard focus, and
survives a Space switch. That's the one trick the whole macOS overlay
depends on — the script prints what it actually set the window's flags to,
and its own docstring has a short manual checklist. If it fails or behaves
differently than described, stop there and report exactly what happened.

**Why this needs real native code, not a recompile.** The Windows overlay's
click-through comes from raw Win32 (`SetWindowLongW`,
`WS_EX_TRANSPARENT | WS_EX_NOACTIVATE`), and its visual transparency comes
from a Tk attribute, `-transparentcolor`, that doesn't exist on macOS Tk at
all. Neither piece has a cross-platform equivalent in Tkinter — macOS needs
its own window and its own drawing, via AppKit (Cocoa) through PyObjC.

**What exists:** `mac_backend.py`, a macOS implementation of every
Windows-only piece of `blink_reminder.py` — `Overlay`, `RunningIndicator`,
`CountdownLabel`, monitor detection, sound, and Start-at-Login registration
— built with the same call shapes as the Windows classes, so wiring it into
the shared app is a small, mechanical step once it's confirmed working.
**Not wired in yet, on purpose:** the Windows build and its full test suite
are completely untouched by any of this.

The core click-through/non-activating/floating-level combination is grounded
in a real, working example
([yuki-f-saka/live-football-transcriber PR #22](https://github.com/yuki-f-saka/live-football-transcriber/pull/22))
that reads its own window's flags back after setting them — not guessed
from documentation alone.

What's simplified on purpose for this first pass (no flight animation on the
indicator, no multi-pulse choreography, a duplicated `_reminder_rect()` that
should be deleted once this is wired in for real) and what's genuinely
unverified (the `NSScreen` coordinate flip — Cocoa's origin is bottom-left,
Y-up, the opposite of the top-left, Y-down the rest of the app assumes;
`NSSound` from inside a PyInstaller bundle; `SMAppService` against a
PyInstaller `.app`) is written up in full in
[PORTING_MACOS.md](PORTING_MACOS.md).

No signing or notarization yet either — Mac demand hasn't been validated at
all, so it would ship unsigned first (Gatekeeper blocks the first launch;
**System Settings → Privacy & Security → Open Anyway** clears it, once per
downloaded copy, not on every launch) with an Apple Developer Program
membership ($99/yr) only worth paying for if a Mac build shows real pull.

## License

**Not yet decided, and worth knowing before you rely on this repo.** The
source is visible here, but with no `LICENSE` file, default copyright
applies: nobody else has explicit permission to copy, modify, or
redistribute it, whatever the visible-source might suggest. If you want
outside contributions or reuse, a real open-source license (MIT is the usual
low-friction choice for something this size) needs to be added deliberately
— that's a decision for the maintainer, not a default I've picked for you.

© 2026 KennyTechy. All rights reserved unless a license is added.

## Feedback

Found a bug, or does this help you? Open an
[issue](../../issues), or say hi: ktaiwan@hotmail.com /
[buymeacoffee.com/kennytechy](https://buymeacoffee.com/kennytechy).
