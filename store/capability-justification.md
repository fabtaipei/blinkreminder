# restrictedCapability justification — `runFullTrust`

Paste this into Partner Center's justification box. It appears automatically
because the manifest declares a restricted capability; the submission cannot be
completed until it is filled in. Microsoft's guidance is explicit that a thin
request ("it's a desktop app") is denied, so this names the actual APIs.

Approval is per-app, not per-submission — later updates do not re-request it
unless a capability is added.

---

## Paste this

Dry Eyes Blink Reminder Lite is a packaged desktop (Win32) application, declared with
`EntryPoint="Windows.FullTrustApplication"`. `runFullTrust` is the capability
Microsoft requires for this application model; it is the only capability the
package declares, and the app requests no elevation and runs at medium
integrity.

It is used for the following, and nothing else:

**1. Click-through reminder overlays.** The app's entire purpose is to show a
brief, gentle visual cue on every connected monitor. Each overlay is a
borderless top-level window made non-interactive with the Win32 extended
styles `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW`
via `user32!SetWindowLongW`. `WS_EX_TRANSPARENT` and `WS_EX_NOACTIVATE` are
what make the overlay pass clicks straight through to the window underneath and
never take keyboard focus, so it cannot interrupt the user's work. There is no
WinRT equivalent for this.

**2. Per-monitor placement and DPI correctness.** `user32!EnumDisplayMonitors`,
`user32!GetMonitorInfoW`, `shcore!GetDpiForMonitor` and
`user32!SystemParametersInfoW(SPI_GETWORKAREA)` are used to place each overlay
on the correct monitor, at the correct physical size, clear of the taskbar,
across displays running at different scale factors.

**3. Reminder sounds.** `winsound.PlaySound` plays short audio clips read from
the sound files Windows itself ships in `%WINDIR%\Media`. No audio is
downloaded, recorded or captured; the microphone is never opened.

**4. The notification-area icon.** The app lives in the system tray and has no
main window. The icon and its menu use `Shell_NotifyIcon` through the `pystray`
library.

**5. Single-instance enforcement.** A named mutex
(`kernel32!CreateMutexW`, session-local namespace) prevents two copies running
at once and drawing two sets of overlays.

**6. Settings and a local diagnostic log**, written to the application's own
per-user data folder.

The app makes **no network connections of any kind** — it contains no HTTP,
socket or download code. It collects no data, has no account, and includes no
analytics or telemetry. It does not read user documents, capture the screen,
or access the camera. Startup behaviour is declared through `uap5:StartupTask`
and left under the user's control in Task Manager rather than written to any
registry Run key or Startup folder.

---

## If they come back asking for more

Offer these, in this order:

1. The source is a single readable Python file and can be supplied in full.
2. Point at the exact functions: `make_click_through`, `monitor_areas`,
   `reminder_rect`, `play_sound`, `already_running`.
3. Note that the only two outbound actions in the whole app are
   `os.startfile` on an `https://` support link and on `ms-settings:startupapps`,
   both user-initiated, both behind a scheme allow-list.
