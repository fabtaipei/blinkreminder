# Dry Eyes Blink Reminder Lite

**A gentle nudge to blink, and a separate one to look away — both click-through, so neither ever interrupts what you're doing.**

- Two independent reminders: blink on a short timer, look-away on the wall clock
- Click straight through — never steals focus, never blocks a mouse click
- Every connected monitor, correctly sized, whatever the display scaling
- English and 繁體中文, picked up from Windows' own display language
- No network, no account, no analytics — the source is right here if you want to check
- ~20 MB, ~25 MB of RAM while running

**[Download for Windows](../../releases)** · [Microsoft Store](https://apps.microsoft.com/detail/9NBRV5W24KH5) (same app, auto-updates, no SmartScreen prompt) · macOS: in progress, [details below](#macos)

---

<details>
<summary><strong>Installing (portable build)</strong></summary>

1. Download the latest `.exe` from [Releases](../../releases).
2. Put it somewhere permanent — `C:\Users\<you>\Apps\` is fine. **Not** your
   Downloads folder, and not a USB stick.
3. Double-click it. Windows will show **"Windows protected your PC"** — this
   is SmartScreen reacting to an unsigned app from an unknown publisher, not
   a virus warning. Click **More info**, then **Run anyway**. (The Store
   build doesn't show this at all, if you'd rather install that way.)
4. An amber ring appears in the system tray, next to the clock. You may need
   the `^` arrow to see it. Right-click it for **Settings**.

Nothing is written outside your own user folder, and the app does not touch
Startup unless you tick **Start with Windows** yourself.

</details>

<details>
<summary><strong>What it does, and why</strong></summary>

Staring at a screen drops your blink rate by more than half, and the blinks
that do happen are often partial — the lid never fully closes, so the tear
film never renews. The fix isn't treatment, it's interruption: a cue regular
enough to catch, gentle enough not to break concentration every time.

| | Blink | Break |
| --- | --- | --- |
| Fires | on an interval you set | on the wall clock (e.g. every 30 min, landing on `:00`/`:30`) |
| Default style | a small dot | a screen dim |
| Also available | a word, or a dim | a dot, or a word |

The break lands at tidy times regardless of when you started the app — the
practical form of the "20-20-20" rule some people already know. A small
indicator dot sits in the corner of each screen with a countdown to the next
break, so a tray-only app never looks like it's failed to start.

</details>

<details>
<summary><strong>Settings</strong></summary>

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
| Language | English / 繁體中文, top right of the panel. Applies immediately |

**Preview blink** / **Preview break** show the current settings without
saving. **Save** applies them.

Without a config file the app follows the language Windows itself is
displayed in; picking one in the panel pins it from then on. All translated
text lives in `blink_i18n.py`, keyed by the English string, so adding a
language is one dict and nothing else — see [LOCALISATION.md](LOCALISATION.md)
for the whole process, including the Store side.

Settings live in `%APPDATA%\BlinkReminder\config.json`. The reminder pulse
is rate-limited in code so that no combination of settings can exceed three
flashes per second (WCAG 2.3.1) — a photosensitivity floor a user cannot
accidentally configure their way past.

</details>

<details>
<summary><strong>Notes, and uninstalling</strong></summary>

- **If you move the exe after ticking "Start with Windows"**, the shortcut
  will point at the old location. Untick and retick the box to repair it.
- Task Manager shows two entries for the app. That's normal for a
  single-file build: one is the launcher, one is the app.
- First launch takes a second or two while the exe unpacks itself. Later
  launches are quicker.
- Overlays run at medium integrity and correctly do **not** paint over UAC
  prompts, other elevated windows, or exclusive-fullscreen games. That's
  intended behaviour, not a bug.

**To uninstall:** untick **Start with Windows** in Settings, right-click the
tray icon and **Quit**, then delete the exe (and `%APPDATA%\BlinkReminder`
if you want the settings gone too).

</details>

<details>
<summary><strong>Privacy</strong></summary>

No account, no sign-in, no advertising, no analytics, no network connection
of any kind — the app never contacts any server, including its own
developer's. It does not use the camera; it works on a timer, it does not
watch you. Full policy: [store/privacy-policy.md](store/privacy-policy.md).

</details>

<details>
<summary><strong>Building from source (Windows)</strong></summary>

Needs Python 3.10+, then:

    py -m pip install pystray pillow pyinstaller
    py build.py

Output lands in `dist\Dry Eyes Blink Reminder Lite.exe`. `build.py` generates
the icon and the exe's version resource, so `blink_reminder.py`,
`blink_i18n.py` and `build.py` are the only tracked sources that matter for
a Windows build.

`py test_i18n.py` is the gate for translations: every string exists, every
string fits the control it goes in, and the package manifest advertises
exactly the languages the app speaks. CI runs it before every build.

To run without building: `pythonw blink_reminder.py` (`pythonw`, not
`python`, so no console window appears).

CI (`.github/workflows/build-windows.yml`) runs the same `build.py` on every
push, and attaches the exe to a GitHub Release on any `v*` tag.

</details>

<details>
<summary id="macos"><strong>macOS — in progress, unverified on real hardware</strong></summary>

No Mac was available to test any of this while it was written — it's a real
attempt, not a finished port, and that matters more here than anywhere else
in this file.

**Run this first**, on any Mac:

    python3 -m pip install -r requirements-mac.txt
    python3 macsmoke.py

Ten seconds, one window. It answers exactly one question before any more
time goes into the rest: can this Mac show a window that's genuinely
click-through, never steals keyboard focus, and survives a Space switch —
the one trick the whole overlay depends on. The script prints what it
actually set the window's flags to; its own docstring has a short manual
checklist. If it fails, stop there and report what happened.

**Why this needs real native code, not a recompile.** The Windows overlay's
click-through is raw Win32; its transparency comes from a Tk attribute,
`-transparentcolor`, that doesn't exist on macOS Tk at all. Neither has a
cross-platform equivalent — macOS needs its own window and its own drawing,
via AppKit (Cocoa) through PyObjC.

**What exists:** `mac_backend.py`, a macOS implementation of every
Windows-only piece — `Overlay`, `RunningIndicator`, `CountdownLabel`,
monitor detection, sound, Start-at-Login — with the same call shapes as the
Windows classes, so wiring it in is a small step once it's confirmed
working. **Not wired in yet, on purpose:** the Windows build and its test
suite are untouched by any of it.

The click-through/non-activating/floating-level combination is grounded in
a real, working example
([yuki-f-saka/live-football-transcriber PR #22](https://github.com/yuki-f-saka/live-football-transcriber/pull/22))
that reads its own window's flags back after setting them — not guessed
from documentation alone. What's simplified on purpose (no flight animation,
no multi-pulse choreography) and what's genuinely unverified (the `NSScreen`
coordinate flip, `NSSound` from a PyInstaller bundle, `SMAppService` against
a PyInstaller `.app`) is written up in [PORTING_MACOS.md](PORTING_MACOS.md).

No signing yet either — ships unsigned until Mac demand is validated.
Gatekeeper blocks the first launch (**System Settings → Privacy & Security
→ Open Anyway** clears it, once per downloaded copy, not every launch).

</details>

<details>
<summary><strong>License</strong></summary>

No `LICENSE` file, by choice: default copyright applies, so the source here
is visible for transparency — verify the privacy claims above yourself —
but nobody else has permission to copy, modify, or redistribute it.
© 2026 KennyTechy. All rights reserved.

</details>

## Feedback

Found a bug, or does this help you? Open an
[issue](../../issues), or say hi: ktaiwan@hotmail.com /
[buymeacoffee.com/kennytechy](https://buymeacoffee.com/kennytechy).
