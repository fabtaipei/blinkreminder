// The rules, with no chrome.* in sight, so they can be tested under Node.
//
// Everything here is a port of something the desktop app already does and
// has already had to get right: the flash-rate limit, the wall-clock break,
// counting days of use honestly, and when an ask is due. The comments say
// where a rule came from when the reason is not obvious from the code.

export const DISPLAY_NAME = "Dry Eyes Blink Reminder Lite";
export const SUPPORT_URL = "https://buymeacoffee.com/kennytechy";
export const WINDOWS_APP_URL = "https://apps.microsoft.com/detail/9NBRV5W24KH5";

// The on-page cue needs access to web pages, and asks for it only when it is
// switched on: installed without it, the extension shows no "read and change
// all your data" warning, and reminders come as notifications instead.
export const PAGE_ORIGINS = { origins: ["http://*/*", "https://*/*"] };

// Chrome will not run an extension alarm more often than every 30 seconds,
// so the blink interval comes in 30-second steps.
export const INTERVALS = [30, 60, 90, 120, 180, 240, 300, 600, 900, 1200];
export const BREAK_MINUTES = [15, 20, 30, 60];
export const SNOOZE_MINUTES = 30;
export const STYLES = ["dot", "text", "dim"];
export const CORNERS = ["center", "top-left", "top-right", "bottom-left",
                        "bottom-right"];

// The desktop's look values. One cue each, every key its own, so a pulse is
// BUILT from one reminder's settings and nothing is inherited by accident.
// `message: null` means "the default word, in the language in force", so a
// change of language changes it -- a word the user typed stays as typed.
export const DEFAULTS = {
  enabled: true,
  language: "auto",
  // A permanent dot in the corner of the page, saying the extension is
  // running. Off by default: it is the only thing this extension would
  // leave on a page for good, so it is asked for rather than assumed.
  pageDot: false,
  blinkInterval: 60,
  breakEnabled: true,
  breakMinutes: 30,
  showCountdown: true,
  blink: {
    style: "dot", opacity: 0.345, hold: 500, fade: 500, blinks: 2, gap: 150,
    colour: "#bde401", message: null, corner: "center", dotPct: 90,
    fontSize: 36, margin: 48, sound: false, volume: 0.6,
  },
  brk: {
    style: "dim", opacity: 0.401, hold: 3000, fade: 800, blinks: 1, gap: 120,
    colour: "#bde401", message: null, corner: "center", dotPct: 22,
    fontSize: 36, margin: 48, sound: true, volume: 0.6,
  },
};

// The desktop's three flash presets. Timings that match none show as Custom.
export const FEELS = {
  Gentle: { hold: 800, fade: 700, blinks: 1 },
  Standard: { hold: 400, fade: 300, blinks: 2 },
  Sharp: { hold: 150, fade: 60, blinks: 3 },
};

export function feelOf(look) {
  for (const [name, f] of Object.entries(FEELS)) {
    if (look.hold === f.hold && look.fade === f.fade && look.blinks === f.blinks) {
      return name;
    }
  }
  return "Custom";
}

function num(v, lo, hi, fallback, integer = false) {
  const n = Number(v);
  if (typeof v === "boolean" || v === null || v === "" || !Number.isFinite(n)) {
    return fallback;
  }
  const clamped = Math.min(hi, Math.max(lo, n));
  return integer ? Math.round(clamped) : clamped;
}

function pick(v, allowed, fallback) {
  return allowed.includes(v) ? v : fallback;
}

function colour(v, fallback) {
  return typeof v === "string" && /^#[0-9a-fA-F]{6}$/.test(v) ? v : fallback;
}

function look(saved, d) {
  const s = saved && typeof saved === "object" ? saved : {};
  return {
    style: pick(s.style, STYLES, d.style),
    opacity: num(s.opacity, 0.02, 1, d.opacity),
    hold: num(s.hold, 50, 5000, d.hold, true),
    fade: num(s.fade, 0, 5000, d.fade, true),
    blinks: num(s.blinks, 1, 10, d.blinks, true),
    gap: num(s.gap, 0, 2000, d.gap, true),
    colour: colour(s.colour, d.colour),
    message: typeof s.message === "string" && s.message.trim()
      ? s.message.slice(0, 60) : null,
    corner: pick(s.corner, CORNERS, d.corner),
    dotPct: num(s.dotPct, 1, 100, d.dotPct, true),
    fontSize: num(s.fontSize, 10, 200, d.fontSize, true),
    margin: num(s.margin, 0, 500, d.margin, true),
    sound: typeof s.sound === "boolean" ? s.sound : d.sound,
    // As on the desktop: below a fifth the chime is inaudible on most
    // laptop speakers, so that is the floor rather than silence.
    volume: num(s.volume, 0.2, 1, d.volume),
  };
}

// Settings as stored, made safe to use. Each field is checked on its own, so
// one damaged value costs that value and not the rest -- the same promise
// load_config makes on the desktop.
export function normalize(saved, languages = null) {
  const s = saved && typeof saved === "object" ? saved : {};
  const lang = typeof s.language === "string" &&
    (s.language === "auto" || !languages || languages.includes(s.language))
    ? s.language : DEFAULTS.language;
  return {
    enabled: typeof s.enabled === "boolean" ? s.enabled : DEFAULTS.enabled,
    pageDot: typeof s.pageDot === "boolean" ? s.pageDot : DEFAULTS.pageDot,
    language: lang,
    blinkInterval: pick(Number(s.blinkInterval), INTERVALS, DEFAULTS.blinkInterval),
    breakEnabled: typeof s.breakEnabled === "boolean"
      ? s.breakEnabled : DEFAULTS.breakEnabled,
    breakMinutes: pick(Number(s.breakMinutes), BREAK_MINUTES, DEFAULTS.breakMinutes),
    showCountdown: typeof s.showCountdown === "boolean"
      ? s.showCountdown : DEFAULTS.showCountdown,
    blink: look(s.blink, DEFAULTS.blink),
    brk: look(s.brk, DEFAULTS.brk),
  };
}

// WCAG 2.3.1: no more than three flashes in any one second. One cycle is
// fade in, hold, fade out, gap; where that is too short the GAP grows, so
// the look the user tuned survives and only the repeat rate is limited.
export const MIN_PULSE_CYCLE_MS = 350;

export function limitFlashRate(p) {
  const out = { ...p };
  out.blinks = Math.max(1, Math.min(10, Math.round(out.blinks)));
  if (out.blinks > 1) {
    const cycle = 2 * out.fade + out.hold + out.gap;
    if (cycle < MIN_PULSE_CYCLE_MS) out.gap += MIN_PULSE_CYCLE_MS - cycle;
  }
  return out;
}

// One reminder's look as the page script draws it. `word` is the default
// word for this reminder in the language in force, used if none was typed.
export function pulseOf(cfg, kind, word) {
  const l = kind === "blink" ? cfg.blink : cfg.brk;
  return limitFlashRate({ ...l, message: l.message || word });
}

// How long a pulse is on screen, start to finish.
export function pulseMs(p) {
  return (2 * p.fade + p.hold) * p.blinks + p.gap * (p.blinks - 1);
}

// Milliseconds to the next break, counted from local midnight so it lands on
// :00 and :30 (or :15, :20...) whenever the browser happened to start --
// recomputed from the clock every time, so it cannot drift.
export function msToNextBreak(minutes, now = new Date()) {
  const step = Math.max(1, Math.round(minutes)) * 60000;
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const since = now - midnight;
  return step - (since % step);
}

// Chrome fires alarms it missed while the computer slept as soon as it wakes.
// A reminder that is that late is not a reminder, it is noise -- and a burst
// of them at once is worse.
export function isStale(scheduledTime, now, toleranceMs) {
  return now - scheduledTime > toleranceMs;
}

// The cue can be drawn on ordinary web pages only. Chrome refuses scripts on
// its own pages and on the extension galleries, by design.
const GALLERIES = [/^https:\/\/chromewebstore\.google\.com\//,
                   /^https:\/\/chrome\.google\.com\/webstore/,
                   /^https:\/\/microsoftedge\.microsoft\.com\/addons/];

export function drawable(url) {
  if (typeof url !== "string" || !/^https?:\/\//.test(url)) return false;
  return !GALLERIES.some((re) => re.test(url));
}

// The browser's UI language ("en-GB", "zh-TW", "nb") as one of ours.
// Chinese is the exception, as on the desktop: Taiwan, Hong Kong and Macau
// read Traditional characters, everywhere else Simplified, and the wrong
// script is worse than English.
export function resolveLanguage(uiLanguage, available) {
  const tag = String(uiLanguage || "en").replace("_", "-").toLowerCase();
  const [primary, ...rest] = tag.split("-");
  if (primary === "zh") {
    return rest.some((r) => ["tw", "hk", "mo", "hant"].includes(r))
      ? "zh-Hant" : "zh-Hans";
  }
  const code = { no: "nb", nn: "nb", fil: "en" }[primary] || primary;
  return available.includes(code) ? code : "en";
}

// ------------------------------------------------------------------ asks
// Six asks over the life of an install, alternating a coffee and a review,
// timed in DAYS OF USE. Same schedule and same rules as the desktop app.

export const ASK_SCHEDULE = [[12, "donate"], [25, "review"], [55, "donate"],
                             [70, "review"], [150, "donate"], [170, "review"]];
export const ASK_SETTLE_MS = 5 * 60000;

export function todayIso(d = new Date()) {
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function freshAsks() {
  return { days_used: 0, last_counted: "", shown: [], opted_out: false,
           last_ask: "" };
}

export function loadAsks(saved) {
  const s = freshAsks();
  if (!saved || typeof saved !== "object") return s;
  if (Number.isInteger(saved.days_used) && saved.days_used >= 0) {
    s.days_used = saved.days_used;
  }
  for (const k of ["last_counted", "last_ask"]) {
    if (typeof saved[k] === "string") s[k] = saved[k];
  }
  if (Array.isArray(saved.shown)) s.shown = saved.shown.filter(Number.isInteger);
  s.opted_out = saved.opted_out === true;
  return s;
}

// Count `today` once. The DATE is the key, so a day with twenty wakes counts
// once and three days asleep count as one. A date behind the last one is
// ignored; one more than a day AHEAD of today is a clock that was once wrong,
// and is pulled back rather than freezing the count until it is caught up.
export function countDay(state, today) {
  const last = state.last_counted;
  if (today > last) {
    state.days_used += 1;
    state.last_counted = today;
    return true;
  }
  if (last > today) {
    const ahead = (Date.parse(last) - Date.parse(today)) / 86400000;
    if (!(ahead <= 1)) state.last_counted = today;   // NaN counts as wrong too
  }
  return false;
}

// The earliest ask whose count is REACHED and not yet shown, at most one a
// day. "Don't ask again" ends all of them, reviews included.
export function dueAsk(state, today, possible = () => true) {
  if (state.opted_out || state.last_ask === today) return null;
  for (const [day, kind] of ASK_SCHEDULE) {
    if (state.days_used < day || state.shown.includes(day)) continue;
    if (!possible(kind)) continue;
    return [day, kind];
  }
  return null;
}

// Where "Rate this app" goes: the review form of whichever store this copy
// came from. Edge installs from its own gallery, under the same id.
export function reviewUrl(id, userAgent) {
  return /\bEdg\//.test(userAgent || "")
    ? `https://microsoftedge.microsoft.com/addons/detail/${id}`
    : `https://chromewebstore.google.com/detail/${id}/reviews`;
}

export function onWindows(userAgent) {
  return /\bWindows\b/.test(userAgent || "");
}
