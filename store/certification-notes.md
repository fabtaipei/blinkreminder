# Notes for certification

Paste this into Partner Center's "Notes for certification" box on every
submission. Update the date line each time.

**Why this matters more than usual for this app:** Dry Eyes Blink Reminder Lite is a
tray-only application with no main window, and its visible output is a
deliberately subtle, click-through overlay. A tester who launches it and waits
may see nothing at all and conclude the app is broken or incomplete. Store
Policy 10.3 states that a product which cannot be tested may fail
certification, so these notes are the mitigation.

---

## Paste this

_Tested by the developer on Windows 11 (build 26200), single and dual monitor,
on 17 September 2026._

**There is no main window.** Dry Eyes Blink Reminder Lite runs in the notification area
(system tray). After launching, look for its icon — a small amber ring — next to
the clock. You may need to click the `^` arrow to reveal hidden icons.
**Right-click the icon** for the menu: Blink now, Snooze, Settings, and Quit.

**To see a reminder immediately**, without waiting for the timer:
- Right-click the tray icon and choose **Blink now**, or
- Open **Settings** and click **Preview blink** or **Preview break** at the
  bottom of the window.

**A pop-up window appears on first launch** confirming the app is running in
the background. This is intentional and must be dismissed by the user; a
tray-only app that shows nothing on launch is indistinguishable from one that
failed to start.

**The small dot in the corner of each screen is intentional.** It is the
"running" indicator, it is click-through, and it animates to and from the
reminder. It is not a rendering artefact.

**The overlays are deliberately non-interactive.** They use
`WS_EX_TRANSPARENT` and `WS_EX_NOACTIVATE`, so mouse clicks pass through them
and they never take keyboard focus. That is by design: the app must never
interrupt what the user is doing.

**Expected limitations, all by design:** the app runs at medium integrity, so
its overlays will correctly NOT paint over UAC prompts, other elevated windows,
or exclusive-fullscreen games. This is intended behaviour, not a defect.

**No network connection is required to test anything.** The app makes no
network requests at all. There is no account, no sign-in, no trial and no
in-app purchase. All functionality is available immediately on launch.

**Default timings:** a blink reminder every 45 seconds and a "look away" break
on the wall clock every 30 minutes, both adjustable in Settings. If you want to
observe an unattended reminder rather than forcing one, the blink interval can
be set as low as 3 seconds in Settings.

**Accessibility / photosensitivity:** the reminder pulse is rate-limited in
code so that no combination of user settings can exceed three flashes per
second (WCAG 2.3.1 Level A). At the shipped defaults it is well under two.
