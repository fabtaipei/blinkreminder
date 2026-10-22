// A small dot in the corner of the page: "it is running, you just cannot see
// it" -- the desktop app's corner indicator, as far as a browser allows.
//
// Opt-in, and off by default. It is the one thing this extension leaves on a
// page permanently, so it is the one thing the user has to ask for. It reads
// nothing from the page: the only thing it touches is an element of its own.
//
// Registered as a content script while the setting is on, and removed from
// every open page the moment it is switched off.

(() => {
  if (globalThis.__blinkReminderDot) return;

  // Logical pixels, matching the desktop indicator: 9 across, clear of the
  // corner a scrollbar occupies.
  const SIZE = 9;
  const RIGHT = 20;
  const BOTTOM = 14;
  const ALPHA = 0.55;

  let host = null;
  let timer = null;
  let hidden = 0;        // suppressed until this time, while a cue is showing
  let state = null;      // the settings, as last read

  function css(el, props) {
    for (const [k, v] of Object.entries(props)) el.style.setProperty(k, v, "important");
  }

  function build(colour) {
    const h = document.createElement("blink-reminder-dot");
    h.setAttribute("aria-hidden", "true");
    css(h, {
      all: "initial", display: "block", position: "fixed",
      bottom: `${BOTTOM}px`, right: `${RIGHT}px`,
      width: `${SIZE}px`, height: `${SIZE}px`, "border-radius": "50%",
      background: colour, opacity: String(ALPHA),
      // A dark ring round the core, for the same reason the desktop's 16px
      // tray icon keeps two tones: this sits on a background the app did not
      // choose. Lime alone is nearly invisible on a white page.
      "box-shadow": "0 0 0 1px rgba(0, 0, 0, 0.55)",
      margin: "0", padding: "0", border: "0",
      // Never in the way: no clicks, no selection, and under the cue rather
      // than over it, so a reminder is never drawn around a hole.
      "pointer-events": "none", "user-select": "none",
      "z-index": "2147483646",
    });
    return h;
  }

  function wanted() {
    if (!state || !state.pageDot || !state.enabled) return false;
    if (state.snoozeUntil && state.snoozeUntil > Date.now()) return false;
    return Date.now() >= hidden;
  }

  function paint() {
    clearTimeout(timer);
    const on = wanted();
    if (on && !host) {
      host = build(state.colour);
      document.documentElement.append(host);
    } else if (on) {
      css(host, { background: state.colour });
    } else if (host) {
      host.remove();
      host = null;
    }
    // Come back by itself when a snooze runs out or a cue finishes, rather
    // than waiting for the next thing that happens to change.
    const next = [hidden, state && state.snoozeUntil]
      .filter((t) => t && t > Date.now())
      .sort((a, b) => a - b)[0];
    if (next) timer = setTimeout(paint, next - Date.now() + 50);
  }

  async function read() {
    try {
      const { cfg, snoozeUntil } = await chrome.storage.local.get(["cfg", "snoozeUntil"]);
      const c = cfg || {};
      const blink = c.blink || {};
      state = {
        pageDot: c.pageDot === true,
        enabled: c.enabled !== false,
        snoozeUntil: snoozeUntil || 0,
        // The blink's own colour, as the desktop indicator uses it.
        colour: /^#[0-9a-fA-F]{6}$/.test(blink.colour || "") ? blink.colour : "#bde401",
      };
      paint();
    } catch {
      // The extension was reloaded or disabled under us; leave nothing behind.
      off();
    }
  }

  function off() {
    clearTimeout(timer);
    if (host) {
      host.remove();
      host = null;
    }
  }

  globalThis.__blinkReminderDot = {
    off,
    // Called by cue.js: the dot steps out of the way for the length of a
    // reminder, so the two are never on screen together.
    suppress(ms) {
      hidden = Date.now() + ms;
      paint();
    },
  };

  try {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === "local" && ("cfg" in changes || "snoozeUntil" in changes)) read();
    });
  } catch { /* no storage access: the dot simply never appears */ }
  read();
})();
