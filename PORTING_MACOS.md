# Porting to macOS -- current state

Written entirely on Windows, with no Mac to test any of it on. That's the
headline fact about everything below: it's a real engineering attempt, not a
finished port, and the first job for anyone with Mac access is to find out
which parts of it are wrong.

## Run this first

```
python3 -m pip install -r requirements-mac.txt
python3 macsmoke.py
```

Ten seconds, one window, nothing else installed or configured. It exists to
answer exactly one question before any time is spent on the rest: **can this
Mac show a window that's genuinely click-through, never steals keyboard
focus, and survives a Space switch.** That's the one trick the whole overlay
depends on. The script prints what it actually set the window's flags to,
and the file's docstring has a short manual checklist (click through it,
watch the Dock, switch Spaces, keep typing elsewhere).

If that fails or behaves differently than described, **stop there** and
report exactly what happened -- don't debug forward into `mac_backend.py`
first.

## What exists

`mac_backend.py` -- a macOS implementation of the pieces of `blink_reminder.py`
that are Win32-specific on Windows: `Overlay`, `RunningIndicator`,
`CountdownLabel`, `monitor_areas()`, `play_sound()`, `set_startup()`. Built
on AppKit via PyObjC, not on Tkinter -- `-transparentcolor`, the Tk attribute
the Windows Overlay's transparency depends on, doesn't exist on macOS Tk at
all, so this was never a matter of swapping the Win32 calls underneath the
same Canvas code.

**Not wired into `blink_reminder.py` yet, on purpose.** The Windows app and
its test suite are untouched by any of this. Wiring it in (a `sys.platform`
branch inside `App.__init__` choosing which backend to construct) is a small,
mechanical step -- worth doing once `macsmoke.py` and a short manual run of
`mac_backend.py`'s pieces confirm the approach actually works, not before.

## What's simplified, on purpose, for this first pass

- **No flight animation.** The Windows `RunningIndicator` flies from its
  corner to the reminder and back; this version just shows and hides. Worth
  adding once the fundamentals are confirmed, not before.
- **No blink/gap choreography in a pulse.** One held pulse per reminder, not
  the fade-in/hold/fade-out/gap/repeat sequence the Windows build supports.
- **`_reminder_rect()` is duplicated**, not imported from `blink_reminder.py`,
  so this file has no import-time dependency on it while it's still a
  preview. Once wired in for real, delete the copy and use the real one --
  it already handles every corner case and has tests.

## What's genuinely unverified, not just simplified

- The `NSScreen` coordinate flip (`monitor_areas()`'s docstring explains why
  it's needed: Cocoa's origin is bottom-left, Y-up; everything else in this
  app assumes top-left, Y-down). The math should be right; it has never run
  against a real multi-monitor Mac.
- `NSSound` playing a file from inside a PyInstaller `--onefile` bundle's
  temp-extraction path.
- `SMAppService` registration against a PyInstaller `--windowed` `.app`
  bundle specifically -- it needs the caller to be a properly bundled,
  LaunchServices-registered app, which PyInstaller's `--windowed` output
  should be, but that pairing hasn't been exercised end to end.

## Building (once the above is confirmed)

Not written yet -- there's no point writing a `build_mac.py` PyInstaller spec
before the runtime code it would package is known to work. `build.py`
(Windows) is the model to follow: same idea, `--windowed` instead of
`--onefile` (`--onefile` on macOS re-extracts and re-launches itself on every
start, which is a worse experience for something that's meant to feel like
part of the system, not a downloaded tool).

## Distribution

Shipping unsigned for now -- no Apple Developer Program membership ($99/yr)
yet, since Mac demand hasn't been validated at all. Unsigned means Gatekeeper
blocks the first launch; the person has to go to **System Settings > Privacy
& Security > Open Anyway**. That's a one-time override per downloaded copy,
not a recurring prompt. Worth paying for signing + notarization once/if this
version shows real pull, same reasoning as the Windows Store pricing
decision earlier in this project.
