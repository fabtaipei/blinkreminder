# Chrome Web Store submission — what to paste

Upload `dist-chrome/blink-reminder-chrome-1.0.0.zip`. Everything below is
ready to copy into the dashboard's own fields.

The **name** and the **short description** are not typed in: the Store reads
them from `_locales/`, so they arrive already translated into 29 languages.
Only the long description below is English-only.

## Images

Screenshots go in **Global assets**, not Localised: global is the set everyone
sees, and localised overrides it for one language only. The words on them are
English, so there is nothing to override.

| Field | File |
|---|---|
| Screenshots (1280×800, in this order) | `1-blink-cue.png`, `4-settings.png`, `5-popup.png`, `2-break.png`, `3-corner-dot.png` |
| Small promo tile (440×280) | `promo-440x280.png` |
| Marquee promo tile (1400×560) | `marquee-1400x560.png` — optional; it is what a featured placement uses |
| Icon (128×128) | taken from the package; `icon-128.png` if a field asks for the file |

Each carries one word across it, as the Windows listing puts BLINK across
its own: BLINK, CUSTOMISABLE, SNOOZE ANY TIME, TAKE A BREAK, WORKING QUIETLY.
A lime circle over an article could otherwise be anything, and a caption in
small print at the top does not get read. The demo page is dark because that is where the
cue's own default strength reads as it really is — on a white page a 34%
wash is honestly faint, and a listing image nobody can see tells nobody
anything.

The `-raw` files are the untouched captures. Re-run the two commands at the
foot of this file to rebuild everything from them.

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

Short on purpose, but each says why the permission is *needed*, not just what
it touches. The day count is explained before a reviewer can mistake it for
usage tracking.

| Permission | Paste this |
|---|---|
| `alarms` | A service worker cannot hold a timer, so the blink interval and the wall-clock break are scheduled with chrome.alarms. |
| `storage` | Remembers settings between sessions: intervals, cue style, colour, size, timing, sound, language and tutorial progress. Also a count of days used, which only decides when the occasional coffee or review message appears. All kept in chrome.storage.local; nothing synced, nothing sent. |
| `notifications` | Delivers the break reminder when the cue cannot be drawn on the page, and the occasional coffee or review message. |
| `idle` | Skips reminders while the computer is idle or locked. |
| `scripting` | Injects the extension's own cue script to draw the reminder and the optional corner dot. Both ship in the package; each adds one element and removes it. No page content is read. |
| `offscreen` | Plays the reminder chime. A page cannot play a sound unprompted, so it plays from an offscreen document. |
| Host permissions | Requested only when the user turns on the on-page cue. Used solely to draw the cue and the corner dot; no page content is read, and the extension makes no network requests. |

**Remote code:** no. Every script ships inside the package.

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
