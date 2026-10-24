// The rules, with no chrome.* in sight, so they can be tested under Node.
//
// Everything here is a port of something the desktop app already does and
// has already had to get right: the flash-rate limit, the wall-clock break,
// counting days of use honestly, and when an ask is due. The comments say
// where a rule came from when the reason is not obvious from the code.

export const DISPLAY_NAME = "Dry Eyes Blink Reminder";
export const SUPPORT_URL = "https://buymeacoffee.com/kennytechy";
// Tagged, so the Microsoft Store's own campaign report can say how many
// Windows installs this extension sent it. The tag is only read at the
// other end; it changes nothing about the page it opens.
export const WINDOWS_APP_URL =
  "https://apps.microsoft.com/detail/9NBRV5W24KH5?cid=chrome-ext";

// The on-page cue needs access to web pages, and asks for it only when it is
// switched on: installed without it, the extension shows no "read and change
// all your data" warning, and reminders come as notifications instead.
export const PAGE_ORIGINS = { origins: ["http://*/*", "https://*/*"] };

// Any number of seconds the user likes, as on the desktop -- except that
// Chrome will not run an extension alarm more often than every 30 seconds,
// which is the floor rather than a step. The ceiling is the desktop's: its
// spinbox holds at most 999 of whichever unit is picked.
export const MIN_INTERVAL = 30;
export const MAX_INTERVAL = 999 * 60;

// Which unit to show a stored interval in, and therefore what the number
// beside the picker reads: whole minutes from two minutes up, seconds below
// that, which is how a person would say it.
export function intervalUnit(seconds) {
  return seconds >= 120 && seconds % 60 === 0 ? 60 : 1;
}

// A typed number and its unit, as the seconds to store.
export function intervalSeconds(value, unit) {
  const n = Math.round(Number(value) * Number(unit));
  return Math.min(MAX_INTERVAL, Math.max(MIN_INTERVAL, Number.isFinite(n) ? n : MIN_INTERVAL));
}
export const BREAK_MINUTES = [15, 20, 30, 60];
export const SNOOZE_MINUTES = 30;
export const STYLES = ["dot", "text", "dim"];

// Four sounds, the same four the desktop offers, synthesised here rather
// than shipped as files -- Windows' own Media sounds are Microsoft's to
// distribute, not ours. Each reminder picks its own, so the break can be
// told apart from the blink by ear.
export const SOUNDS = ["ding", "chord", "chime", "notify"];
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
  // running -- the desktop app's corner indicator, which is always on and
  // has no setting at all. On by default here too, and still invisible
  // until someone grants access to pages: it cannot appear before the one
  // decision that matters has been made deliberately.
  pageDot: true,
  blinkInterval: 30,
  breakEnabled: true,
  breakMinutes: 30,
  showCountdown: true,
  blink: {
    style: "dot", opacity: 0.345, hold: 500, fade: 250, blinks: 2, gap: 150,
    colour: "#bde401", message: null, corner: "center", dotPct: 90,
    // A chime on every blink, which at the default interval is one a
    // minute. The desktop ships this off; here it is on, at the author's
    // call, after a reviewer said the sound was what made it work for them.
    // The author's own, after living with it: a 30-second interval, a
    // quicker fade, and a chime well below the default.
    fontSize: 36, margin: 48, sound: true, soundName: "ding", volume: 0.2,
  },
  brk: {
    style: "dim", opacity: 0.401, hold: 3000, fade: 800, blinks: 1, gap: 120,
    colour: "#bde401", message: null, corner: "center", dotPct: 22,
    fontSize: 36, margin: 48, sound: true, soundName: "ding", volume: 0.6,
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
    soundName: pick(s.soundName, SOUNDS, d.soundName),
    // Down to 1%. The desktop stops at a fifth because below that its
    // Windows .wav is inaudible; these are synthesised, so the quiet end
    // is usable -- and someone who wants a barely-there tick should have it.
    volume: num(s.volume, 0.01, 1, d.volume),
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
    blinkInterval: num(s.blinkInterval, MIN_INTERVAL, MAX_INTERVAL,
                       DEFAULTS.blinkInterval, true),
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

// -------------------------------------------------------------- the tutorial
// Taught at the moment it is needed rather than up front -- the same design
// as the desktop app's, and for the same reason. The first few blink
// reminders carry the instruction itself; after the last of them comes one
// question about how it felt, whose answers open the settings at the control
// that changes it.

// Few enough that a lesson does not become the way the reminder always looks.
export const TEACH_COUNT = 2;

export function freshTutorial() {
  return { welcomed: false, taught: 0, question: "pending" };
}

export function loadTutorial(saved) {
  const t = freshTutorial();
  if (!saved || typeof saved !== "object") return t;
  if (typeof saved.welcomed === "boolean") t.welcomed = saved.welcomed;
  if (Number.isInteger(saved.taught) && saved.taught >= 0) t.taught = saved.taught;
  if (saved.question === "done") t.question = "done";
  return t;
}

export function teachingDue(t) {
  return t.taught < TEACH_COUNT;
}

// Owed until it has been put away, so a browser closed while it was up asks
// again rather than losing it.
export function questionDue(t) {
  return !teachingDue(t) && t.question === "pending";
}

// Near-black on a light cue, white on a dark one, so the instruction can be
// read whatever colour the cue has been set to.
export function captionInk(colour) {
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(colour || "");
  if (!m) return "#FFFFFF";
  const [r, g, b] = m.slice(1).map((h) => parseInt(h, 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.45 ? "#11161C" : "#FFFFFF";
}

// A pulse as a taught one: the user's own reminder, with the instruction
// added. Nothing else changes -- an earlier desktop version made it stronger
// and longer, which taught people what a reminder they would never see again
// looked like.
export function teachingPulse(pulse, caption, noSpaces) {
  const out = { ...pulse };
  if (out.style === "text") out.message = caption.split("\n").join(noSpaces ? "" : " ");
  else out.caption = caption;
  out.ink = captionInk(out.colour);
  return out;
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
