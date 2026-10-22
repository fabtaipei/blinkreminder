# Dry Eyes Blink Reminder Lite — Chrome extension

The blink and break reminders of the Windows app, inside Chrome (and Edge),
on Windows, Mac, Linux and ChromeOS. Design: `docs/chrome-extension-design.md`.

## What it does

- **Blink reminder** on an interval (30-second steps — Chrome's own minimum),
  drawn over the web page in front: a dot, a word or a dim. Clicks and keys
  pass straight through it, and it sits above everything, fullscreen video
  included.
- **Break reminder** on the wall clock (`:00` / `:30`, or every 15, 20 or 60
  minutes). If Chrome isn't the window in use, it arrives as a notification.
- **Toolbar pop-up**: on/off, Blink now, interval, snooze 30 minutes, the
  time to the next break. The toolbar badge counts down the minutes.
- **Corner dot** (opt-in, off by default): a small dot in the bottom-right of
  the page while reminders are running, the desktop app's corner indicator as
  far as a browser allows. It needs the same site access the cue does, and it
  steps aside while a reminder is on screen.
- **Settings page**: style, strength, colour, size, position, flash style,
  timings and sound for each reminder, and the language — all 30 of the desktop app's,
  Urdu included (Chrome itself has no Urdu).
- **Tutorial**, as in the desktop app: a welcome page on install, the first
  two blink reminders carrying "Close… squeeze… open", then one question
  — "Too weak or intrusive?" — whose four answers open the settings with
  that control ringed. **Show me** plays a taught reminder and asks the same
  question; **How it works** in the pop-up brings the welcome page back.
- **Coffee/review asks**: the desktop's schedule exactly (days 12, 25, 55, 70,
  150, 170 of use), as a notification, at most one a day; "Don't ask again"
  ends them all.

### Site access is opt-in

Installed, it asks only for timers, storage, notifications and idle detection
— no "read and change all your data" warning. Switching on **Show the cue on
web pages** (offered on the welcome page and in the pop-up) asks Chrome for
access, which is what drawing over a page needs. Nothing on any page is read
or sent anywhere.

Until then, **break reminders arrive as notifications and blink reminders are
not shown** — a blink toast every minute would be the interruption this app
exists not to be. The extension says so once, with a button to the settings,
rather than repeating itself. Chrome's own menu also lets someone narrow
access to a single site, and the cue is drawn there and nowhere else.

## Build, test, try

    py chrome/build_extension.py --zip    # strings, locales, icons; dist-chrome/
    cd chrome && node --test               # the rules: schedule, days, asks
    node chrome/e2e/headless.js            # a real headless Chrome, end to end

`build_extension.py` generates `strings.js` and `_locales/` from
`blink_i18n.py` (shared with the desktop app) and `ext_strings.py` (the six
strings only the extension says), and stops if any string the extension uses
is missing in any language. Never edit `strings.js` by hand.

`e2e/headless.js` runs Chrome headless with a throwaway profile and muted
audio, and replaces notifications with a recorder, so nothing appears on
screen. `BLINK_EXT_SRC=dist-chrome/unpacked` runs it against the package
exactly as built.

**To try it in your own Chrome:** `chrome://extensions` → turn on
**Developer mode** → **Load unpacked** → pick `dist-chrome/unpacked`.

## Chrome Web Store submission notes

One-time US$5 developer registration. Upload `dist-chrome/blink-reminder-chrome-<version>.zip`.

**Single purpose:** Reminds the user to blink and to look away from the screen, with a brief visual cue on the web page in front or a notification.

**Permission justifications**

| Permission | Why |
|---|---|
| `alarms` | Times the blink and break reminders. |
| `storage` | Keeps the user's settings and the count of days used, on this device only. |
| `notifications` | Shows reminders when the on-page cue is off or Chrome isn't in front, and the occasional coffee/review ask. |
| `idle` | Skips reminders while the computer is idle or locked. |
| `scripting` | Draws the cue over the active web page, and the corner dot while that is switched on. |
| `offscreen` | Plays the optional reminder chime (a web page may not play sound unprompted). |
| Host access (optional, `http://*/*`, `https://*/*`) | Requested only when the user switches on the on-page cue. Used solely to draw the cue; page content is never read. |

**Data use:** collects no user data. No remote code. No network requests of any kind.

**Listing:** name and description come from `_locales/` (29 languages). Screenshots must be 1280×800 or 640×400 and taken in Chrome.
