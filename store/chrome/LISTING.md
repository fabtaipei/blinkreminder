# Chrome Web Store submission — what to paste

Upload `dist-chrome/blink-reminder-chrome-1.0.0.zip`. Everything below is
ready to copy into the dashboard's own fields.

The **name** and the **short description** are not typed in: the Store reads
them from `_locales/`, so they arrive already translated into 29 languages.
Only the long description below is English-only.

## Images

| Field | File |
|---|---|
| Screenshots (1280×800, in this order) | `1-blink-cue.png`, `4-settings.png`, `5-popup.png`, `2-break.png`, `3-corner-dot.png` |
| Small promo tile (440×280) | `promo-440x280.png` |
| Icon (128×128) | taken from the package |

The corner-dot shot is the weakest — the dot really is nine pixels on an
empty corner, so most of the frame is blank page. Four screenshots is a fine
listing; drop it if it looks thin.

## Category

**Lifestyle → Health**, or Productivity → Workflow & Planning if that reads
better alongside the other eye-care extensions.

## Single purpose

> Reminds the user to blink and to look away from the screen, with a brief
> visual cue drawn over the page in front, or a notification.

## Detailed description

> Staring at a screen roughly halves how often you blink, and many of the
> blinks that remain are incomplete — the eyelids never quite close, so the
> tear film isn't renewed. If your eye doctor has told you to blink fully,
> this is a way to build the habit without thinking about it.
>
> A soft cue appears over the page every so often. You can read straight
> through it: it ignores clicks and keystrokes, never takes focus, and fades
> by itself. Separately, on the wall clock, a reminder to look away from the
> screen for a moment.
>
> • Blink reminder on any interval from 30 seconds
> • Look-away reminder on the hour and half hour, or every 15, 20 or 60 minutes
> • A dot, a word, or a gentle dim — your choice of size, colour, strength,
>   timing and sound
> • A small corner dot while it's running, which you can switch off
> • 30 languages, following your browser
> • No account, no ads, no analytics, no network connection of any kind
>
> The on-page cue is opt-in. Installed, the extension asks for nothing but
> timers and notifications; the permission to draw on pages is requested only
> when you switch that on, and nothing on any page is ever read or sent
> anywhere. The code is public.
>
> There is a full Windows version in the Microsoft Store, which shows the cue
> over every application rather than only in the browser.

## Permission justifications

| Permission | Paste this |
|---|---|
| `alarms` | Times the blink and break reminders. |
| `storage` | Keeps the user's settings and the count of days used, on this device only. |
| `notifications` | Delivers the break reminder when the on-page cue is off or Chrome isn't in front, and the occasional support/review message. |
| `idle` | Skips reminders while the computer is idle or locked. |
| `scripting` | Draws the cue, and the optional corner dot, over the page. |
| `offscreen` | Plays the reminder chime. A web page may not play a sound unprompted, so it is played from an offscreen document. |
| Host access (optional) | Requested only when the user switches on the on-page cue. Used solely to draw the cue and the corner dot; page content is never read, and the extension makes no network requests. |

## Data use

Collects **no** user data — tick nothing. No remote code: every script ships
in the package.

## Privacy policy URL

https://github.com/fabtaipei/blinkreminder/blob/main/store/privacy-policy.md

## Links

| | |
|---|---|
| Homepage | https://apps.microsoft.com/detail/9NBRV5W24KH5 |
| Support | https://github.com/fabtaipei/blinkreminder/issues |

## Rebuilding these images

    node chrome/e2e/store-shots.js     # a real headless Chrome, 1280x800
    py store/make_chrome_assets.py     # composes the two that need it
