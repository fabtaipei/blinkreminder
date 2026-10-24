# Chrome Web Store — the 1.2.0 listing update

24 October 2026. Everything needed to update the published listing, in the
order the dashboard asks for it.

`LISTING.md` beside this file still holds the dashboard answers that have not
changed — single purpose, permission justifications, data use, privacy policy
URL, category. Only what is listed here is different.

Live listing before this update: version 1.1.0, name "Dry Eyes Blink Reminder
Lite", 0 ratings, Wellbeing.

---

## 1. Upload the package

    dist-chrome/blink-reminder-chrome-1.2.0.zip

**The name and the short description are inside this file.** Both are read
from `_locales/`, so there is no dashboard field for either and nothing to
paste. Uploading the package is what changes them.

| | |
|---|---|
| Name | `Dry Eyes Blink Reminder · Eye Strain & 20-20-20 Break Timer` (59 of 75) |
| Short description | `Two reminders in one app: a gentle cue to blink, and a 20-20-20 eye break. For dry eyes and digital eye strain. No tracking.` (124 of 132) |

The short description is English only for now. The other 28 languages still
carry the old sentence; they are a separate job, in the calendar for
Wednesday 28 October.

The name is the same in all 29 languages, so it takes effect everywhere.

### Why the name grew a tail

Google's own "Related" panel is the evidence. On BlinkGuard's listing it
shows EyeCare, Eyedle, Digital Eye Relief and EyeRest. On ours it showed
UnDistracted, AppBlock, Cat Gatekeeper and YouTube Row Fixer. The classifier
had filed an eye-care tool with the distraction blockers, because the listing
never used the category's vocabulary once.

"Eye Strain" names the subject. "Eye Strain Relief", which a neighbour uses,
promises an outcome this app cannot support — the FTC has fined a vision app
for that class of claim. Same search value, no exposure.

---

## 2. Images

Six files, all in `store/chrome/`. The thumbnail is a different asset from
the screenshots: it is what appears in the search grid, while the screenshots
appear on the listing page itself.

| Slot | File | Size |
|---|---|---|
| Small promo tile (the thumbnail) | `tile-lime-440x280.png` | 440×280 |
| Marquee promo tile | `tile-dark-1400x560.png` | 1400×560 |
| Screenshot 1 | `s1-two-reminders.png` | 1280×800 |
| Screenshot 2 | `s2-seen-and-heard.png` | 1280×800 |
| Screenshot 3 | `s3-four-styles.png` | 1280×800 |
| Screenshot 4 | `s4-20-20-20.png` | 1280×800 |
| Screenshot 5 | `s5-private.png` | 1280×800 |

Upload the screenshots **in that order**. The first one is the largest on the
page and the one most people see.

These go in **Global assets**, not Localised. Global is the set everyone
sees; localised overrides it for one language only. The words on them are
English and there is nothing to override.

What each screenshot is for:

1. **Two reminders** — what the thing is, to someone who has never heard of
   it. The only slide that has to work on a complete stranger.
2. **Seen and heard** — the cue at a size you can actually see. The old
   screenshots never managed this: at full-page scale the cue is a speck.
3. **Four styles** — answers the buyer's real fear, which is being nagged.
   All four are real renders.
4. **20-20-20** — the rule people have already heard from an optometrist,
   and also what they type into the search box.
5. **Nothing leaves your device** — every line is checkable in the source.

The old numbered screenshots (`1-blink-cue.png` and the rest) are superseded
but not deleted. They are five photographs of the same dark article with one
word laid over them, large enough to hide the feature it names.

Rebuild any of this with:

    py store/make_chrome_screens.py     # the five screenshots
    py store/make_chrome_assets.py      # the tiles and the icon

---

## 3. Detailed description — paste this

This field is English only and is not in `_locales`, so it costs no
translations.

Only the first two lines show before "Read more". They carry the whole
proposition.

> Two reminders in one app: a gentle cue to blink, and a 20-20-20 eye break.
> It stays out of your way. You can read, click and type straight through it.
>
> Staring at a screen roughly halves how often you blink, and many of the
> blinks that remain are incomplete. If your doctor has told you to blink more
> often, this helps you do it consistently.
>
> BLINK CUE – VISUAL AND SOUND
>
> A soft cue appears over the page every 30 seconds, or at any interval you
> choose. A gentle chime carries it when you don't see the cue. A blink
> reminder has to reach you even when your eyes are on something else. Four
> sounds, volume from 0% to 100%.
>
> BREAK CUE – EVERY 20 MINUTES
>
> The page tints gently to remind you to look away and take a break. Choose
> 15, 20, 30 or 60 minutes. Twenty is the 20-20-20 rule your optometrist may
> have mentioned: every 20 minutes, look about 20 feet away for 20 seconds.
>
> IT WON'T INTERRUPT YOU
>
> The cue never takes focus, so it cannot swallow what you are typing, and it
> fades by itself. There is no pop-up, no window, and nothing to dismiss.
> Snooze it if needed.
>
> CUSTOMISABLE – TURN ANYTHING DOWN, OR OFF
>
> Four styles: a dot, a word, a gentle dim, or a small corner dot.
>
> Size, colour, strength, timing and sound are all customisable, so the blink
> cue can be barely there, but just enough to remind you. Anything you do not
> want, switch off.
>
> Available in 29 languages.
>
> NOTHING LEAVES YOUR DEVICE
>
> No account. No sign-in. No ads, no analytics, no tracking. This extension
> makes no network connection, so there is nowhere for anything to go. Nothing
> on any page is ever read.
>
> Showing the cue on web pages is opt-in. Installed, it asks for nothing but
> timers and notifications. Permission to draw on a page is requested only
> when you switch that on, and you can give it one site at a time. The code is
> public.
>
> WINDOWS APP AVAILABLE – THE CUE IN EVERY APP
>
> There is a full Windows version in the Microsoft Store. It shows the cue
> over every application, not only in the browser.
>
> This is a reminder to do something you may already have been advised to do.
> It is not a medical device and it does not diagnose or treat any condition.
> If your eyes hurt, or stay uncomfortable, see an eye-care professional.

### What changed, and why

- **The first two lines** now carry the proposition. They used to open on
  physiology, which is a good hook but answers the wrong question first.
- **The promise not to interrupt is in the opening paragraph**, not under a
  heading of its own. Someone with sore eyes has two questions: will it
  help, and will it drive me mad. Both are answered before "Read more".
- **"How you will still notice the cue" answers the doubt that raises.** A
  reminder quiet enough to ignore is no reminder at all, and the sound is
  what resolves it: the cue has to reach you precisely when your eyes are
  somewhere else. Sound had been buried as a spec — "timing and sound" —
  rather than made as a point.
- **"Blink fully" is gone.** The app reminds people to blink; it cannot
  train a complete one. "Blink more often" is what it can keep.
- **The search terms are in**, inside sentences: dry eyes, digital eye
  strain, 20-20-20, eye break. Not as a list — Chrome suspends listings that
  read as a pile of synonyms.
- **29 languages is stated.** The nearest competitor has 19 and says so.
- **A medical disclaimer closes it.** Category-normal, and cheap protection
  against a claim nobody intended to make.

---

## 4. Do not change

- **Category: Wellbeing.** Correct, and the same as every competitor worth
  comparing to.
- **Data use: collects no user data.** Tick nothing, then the three
  certifications. The day counter named in the storage justification never
  leaves `chrome.storage.local`, and the Store's question is about data
  *collected*, meaning taken off the device.
- **Permissions.** Unchanged from the approved 1.1.0 — same six, host access
  still optional. No new permission means no expanded-permission review.
- **Non-trader status.** The EU consumer-rights notice it puts on the page
  reads badly, but declaring yourself a trader to remove it would be worse.

---

## 5. Not worth doing

- **The Featured badge.** Google announced on 20 August 2026 that it is
  sunsetting the badge, closed self-nominations that day, and closed all
  pending ones. Its stated replacement signal is the rating system.
- **Soliciting reviews.** A policy violation, and the clean record is worth
  more than the stars.

Ratings remain the one lever that matters and the one we cannot pull
directly. The 1.2.0 release is the closest thing to a fix: until now the
review request went out only as a notification, which the operating system
may refuse to show — and when it did, the ask was marked as spent anyway. No
review request has ever reached a human. They now wait in the pop-up until
they are answered.
