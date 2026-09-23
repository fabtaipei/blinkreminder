# Dry Eyes Blink Reminder Lite

A tray app for two things: a brief cue to blink, and a separate reminder to
look away from the screen for a moment. Both are click-through — they never
take focus and never interrupt what you're doing.

Windows 10/11, 64-bit. [Also on the Microsoft Store](https://apps.microsoft.com/detail/9NBRV5W24KH5)
(same app, auto-updating, no SmartScreen prompt).

## Installing (portable build)

1. Download the latest `.exe` from [Releases](../../releases).
2. Put it somewhere permanent — `C:\Users\<you>\Apps\` is fine. **Not** your
   Downloads folder, and not a USB stick.
3. Double-click it. Windows will show **"Windows protected your PC"** — this
   is SmartScreen reacting to an unsigned app from an unknown publisher, not
   a virus warning. Click **More info**, then **Run anyway**.
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
the next break. Reminders appear on every connected monitor, correctly sized
even across different display scaling.

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

Settings live in `%APPDATA%\BlinkReminder\config.json`.

## Notes

- **If you move the exe after ticking "Start with Windows"**, the shortcut
  will point at the old location. Untick and retick the box to repair it.
- Task Manager shows two entries for the app. That's normal for a
  single-file build: one is the launcher, one is the app.
- First launch takes a second or two while the exe unpacks itself. Later
  launches are quicker.

## Uninstalling

1. Untick **Start with Windows** in Settings.
2. Right-click the tray icon and choose **Quit**.
3. Delete the exe, and delete `%APPDATA%\BlinkReminder` if you want the
   settings gone too.

## Privacy

No account, no analytics, no ads, no network connection of any kind. Full
policy: [store/privacy-policy.md](store/privacy-policy.md).

## Building from source

Needs Python 3.10+, then:

    py -m pip install pystray pillow pyinstaller
    py build.py

Output lands in `dist\Dry Eyes Blink Reminder Lite.exe`. `build.py` generates
the icon and the exe's version resource, so `blink_reminder.py` and
`build.py` are the only tracked sources that matter for a Windows build.

To run without building: `pythonw blink_reminder.py` (`pythonw`, not
`python`, so no console window appears).

### macOS

Not built yet. The settings UI (tkinter) is portable, but the click-through,
never-steals-focus overlay is currently raw Win32 and has no macOS
equivalent implemented — that needs native Cocoa (PyObjC), not a recompile.

## Feedback

Found a bug, or does this help you? Open an
[issue](../../issues), or say hi: ktaiwan@hotmail.com /
[buymeacoffee.com/kennytechy](https://buymeacoffee.com/kennytechy).
