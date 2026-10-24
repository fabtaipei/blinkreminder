# Microsoft Store — the listing update

24 October 2026. The Chrome listing rewritten for Windows: same structure and
voice, the browser-only parts removed, and the one argument the extension
cannot make put back in.

`listing-en-GB.json` is the base listing and already holds the fields that do
not change — Title, DevStudio, the eleven Features, the seven SearchTerms.
Only what is below is different.

---

## 1. What carries over from Chrome, and what does not

**Removed, because it is meaningless on Windows**

- The whole opt-in page-access section. There are no host permissions here.
- "Nothing on any page is ever read." There is no page.
- Keyboard shortcuts. Those are `chrome.commands`; the desktop app has none.
- "Windows app available." This *is* the Windows app.

**Added back, because Windows can say it and the browser cannot**

- **On every screen.** Reminders on every connected monitor, correctly sized
  on each even at different scaling. This is the reason to install the
  desktop app rather than the extension, and it belongs high in the copy.
- **A countdown to the next break**, in the corner of every screen.
- **No camera.** A desktop app that watches your eyes is a thing people
  reasonably fear; the extension is never suspected of it.
- **Three flashes a second, enforced in code.** WCAG 2.3.1. Both products
  implement it, only this one has ever said so.
- **The tray notes.** No main window, right-click for Settings.

**Gained from the Chrome rewrite**

- The 20-20-20 rule is named. The old MS description never used the phrase
  once, on a store where the listing text is most of the ranking.
- A medical disclaimer, which the MS listing did not have at all.
- "Blink more often" replaces "blink fully" in the opening line — the claim
  the app can actually keep.

---

## 2. Description — paste this

> Two reminders in one app: a gentle cue to blink, and a 20-20-20 eye break.
> It stays out of your way. You can click and type straight through it.
>
> Staring at a screen roughly halves how often you blink, and many of the
> blinks that remain are incomplete. If your doctor has told you to blink
> more often, this helps you do it consistently.
>
> BLINK CUE – VISUAL AND SOUND
>
> A soft cue appears on screen every 30 seconds, or at any interval you
> choose. A gentle chime carries it when you don't see the cue. A blink
> reminder has to reach you even when your eyes are on something else. Four
> sounds, volume from 0% to 100%.
>
> BREAK CUE – EVERY 20 MINUTES
>
> The screen tints gently to remind you to look away and take a break. It
> runs on the wall clock, so it lands at the same minutes past the hour
> whenever you started the app. Choose 15, 20, 30 or 60 minutes. Twenty is
> the 20-20-20 rule your optometrist may have mentioned: every 20 minutes,
> look about 20 feet away for 20 seconds.
>
> ON EVERY SCREEN
>
> Reminders appear on every connected monitor, correctly sized on each one
> even when your displays run at different scaling. A small dot in the
> corner of each screen shows the app is running, with a countdown to the
> next break above it.
>
> IT WON'T INTERRUPT YOU
>
> The cue never takes focus, so it cannot swallow a keystroke, and it fades
> by itself. There is no pop-up, no window, and nothing to dismiss. Snooze
> it if needed.
>
> CUSTOMISABLE – TURN ANYTHING DOWN, OR OFF
>
> Four styles: a dot, a word of your own, a gentle dim, or a small corner
> dot.
>
> Size, position, colour, strength, timing and sound are all customisable,
> and each reminder keeps its own settings, so the blink cue can be barely
> there while the break is harder to ignore. Preview any change before you
> save it. Anything you do not want, switch off.
>
> Available in thirty languages, following the language Windows itself is
> displayed in, or set by hand from the top right of Settings.
>
> NOTHING LEAVES YOUR DEVICE
>
> No account. No sign-in. No ads, no analytics, no tracking. There is no
> network connection of any kind — the app never contacts any server,
> including ours.
>
> It does not use your camera. It works on a timer; it does not watch you.
> And the reminder is rate-limited in code, so no combination of settings
> can exceed three flashes per second.
>
> GOOD TO KNOW
>
> The app runs in the notification area and has no main window. Right-click
> its tray icon for Settings.
>
> This is a reminder to do something you may already have been advised to
> do. It is not a medical device and it does not diagnose or treat any
> condition. If your eyes hurt, or stay uncomfortable, see an eye-care
> professional.

---

## 3. Screenshots

Six, 1920×1080, in `store/ms/`. Upload in this order.

| # | File | Argument |
|---|---|---|
| 1 | `m1-two-reminders.png` | what it is |
| 2 | `m2-seen-and-heard.png` | it works |
| 3 | `m3-four-styles.png` | it will not annoy you |
| 4 | `m4-20-20-20.png` | the rule, and the search term |
| 5 | `m5-every-screen.png` | **the one the browser cannot make** |
| 6 | `m6-private.png` | trust, including the camera and the flash limit |

Accents follow the Chrome picks: lime, cool, warm, lime, lime, lime.

Rebuild with:

    py store/make_ms_screens.py

The existing `store/screenshots/*.png` (1922×1080 photographs of the real
app) are not deleted. One of them is worth keeping as a seventh, showing the
actual settings panel — the Store allows up to nine, and a listing made
only of posters is a listing with nothing real in it.

### Captions to fix

`DesktopScreenshotCaption2` currently reads "every 20, 30 or 60 minutes of
the hour" and omits 15, which the app has offered since the start. Captions
1 and 3 are also duplicates of each other.

---

## 4. Unchanged, deliberately

- **"Lite" stays in the Windows name.** It only sells where the buyer fears
  weight, and someone choosing a desktop application has a reason to care.
  It was dropped on Chrome for the opposite reason.
- **The amber icon stays**, for now. The Chrome extension has moved to a
  lime disc with a B; the two will not match until this one is dealt with
  deliberately.
- **The seven search terms stay.** They are already well chosen and already
  filled in.
- **Features 1 to 11 stay.**

---

## 5. Also outstanding

- `dist-msix/BlinkReminder-1.4.1.0.msix` is built and unsubmitted.
- Two ratings. From sampling the catalogue, Microsoft shows no star score
  below five, so three more flips this listing from "no rating" to a
  visible one. That is a larger visual change than anything in this file.
