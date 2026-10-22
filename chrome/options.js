// The settings page, and the welcome shown on install.
//
// Every change is saved as it is made -- the Chrome convention, and there is
// no window to close with a Save button anyway. The background worker hears
// the change in storage and reschedules.

import {
  INTERVALS, BREAK_MINUTES, CORNERS, FEELS, PAGE_ORIGINS, SUPPORT_URL,
  WINDOWS_APP_URL, DISPLAY_NAME, normalize, feelOf, pulseOf, reviewUrl,
  onWindows,
} from "./core.js";
import { CODES, setLanguage, T, localize, intervalLabel, defaultWord } from "./i18n.js";
import { LANGUAGES } from "./strings.js";

const $ = (id) => document.getElementById(id);
let cfg = normalize((await chrome.storage.local.get("cfg")).cfg, CODES);

async function save() {
  cfg = normalize(cfg, CODES);
  await chrome.storage.local.set({ cfg });
}

// -- small builders ---------------------------------------------------------

function el(tag, props = {}, ...children) {
  const e = Object.assign(document.createElement(tag), props);
  e.append(...children);
  return e;
}

function row(label, ...controls) {
  return el("div", { className: "row" }, el("span", { textContent: label }),
            el("div", { className: "control" }, ...controls));
}

function switchRow(label, checked, onChange) {
  const box = el("input", { type: "checkbox", checked });
  box.setAttribute("role", "switch");
  box.addEventListener("change", () => onChange(box.checked));
  return el("label", { className: "row switch" }, el("span", { textContent: label }), box);
}

function segmented(choices, value, onPick) {
  const group = el("div", { className: "segmented" });
  for (const [v, label] of choices) {
    const b = el("button", { type: "button", textContent: label });
    b.setAttribute("aria-pressed", String(v === value));
    b.addEventListener("click", () => onPick(v));
    group.append(b);
  }
  return group;
}

function select(choices, value, onPick) {
  const s = el("select");
  for (const [v, label] of choices) s.append(new Option(label, v, false, v === value));
  s.addEventListener("change", () => onPick(s.value));
  return s;
}

// A 2-100% slider with its number beside it, saved when let go.
function percent(value, lo, onSet) {
  const range = el("input", { type: "range", min: lo, max: 100, value });
  const shown = el("span", { className: "pct", textContent: `${value}%` });
  range.addEventListener("input", () => { shown.textContent = `${range.value}%`; });
  range.addEventListener("change", () => onSet(Number(range.value)));
  return [range, shown];
}

// A number box. Typing past either end is pulled back into range rather than
// refused, so there is no way to leave a setting in a state the cue cannot
// draw.
function num(value, lo, hi, step, onSet) {
  const input = el("input", { type: "number", min: lo, max: hi, step, value });
  input.addEventListener("change", () => {
    const n = Math.min(hi, Math.max(lo, Number(input.value) || lo));
    input.value = n;
    onSet(n);
  });
  return input;
}

// Stored in milliseconds, shown and typed in seconds, as the desktop's
// timing spinboxes are.
function secs(ms, lo, hi, onSet) {
  const input = num(Math.round(ms) / 1000, lo, hi, 0.05,
                    (v) => onSet(Math.round(v * 1000)));
  input.value = (Math.round(ms) / 1000).toFixed(2);
  return input;
}

// Grey a row out instead of removing it.
//
// Every row exists on both cards whether or not it applies, so the blink's
// Strength sits level with the break's and the eye can read across. A row
// that does not apply to the style in force -- Position under a full-screen
// dim, Word size under a dot -- is dimmed and its controls disabled, which
// is what the desktop panel does and why its two cards line up.
function applies(node, on) {
  node.classList.toggle("off", !on);
  for (const c of node.querySelectorAll("input, select, button")) c.disabled = !on;
  return node;
}

// -- one reminder's controls -------------------------------------------------

// The same rows, in the same order, for both reminders.
//
// The literals are here, not in a table, so the build can find every one and
// prove all thirty languages have it.
function lookControls(kind) {
  const l = cfg[kind];
  const set = (patch) => { Object.assign(l, patch); save(); };
  // A change of style, position or timing changes which rows apply or what
  // they read, so those redraw the card.
  const restyle = (patch) => { Object.assign(l, patch); save(); render(); };
  const dot = l.style === "dot";
  const text = l.style === "text";
  const placed = l.style !== "dim";
  const out = [];

  out.push(el("div", { className: "row" }, segmented(
    [["dot", T("A dot")], ["text", T("A word")], ["dim", T("Dim screen")]],
    l.style, (s) => restyle({ style: s }))));

  out.push(row(T("Strength"),
    ...percent(Math.round(l.opacity * 100), 2, (v) => set({ opacity: v / 100 }))));

  const colour = el("input", { type: "color", value: l.colour });
  colour.addEventListener("change", () => set({ colour: colour.value }));
  out.push(row(T("Colour"), colour));

  // The stored size, not a zero: a greyed row still shows what the setting
  // is, so switching back to a dot holds no surprise.
  out.push(applies(row(T("Dot size"),
    ...percent(l.dotPct, 5, (v) => set({ dotPct: v }))), dot));

  const word = el("input", { type: "text", value: text ? l.message || "" : "",
                             placeholder: defaultWord(kind), maxLength: 60 });
  word.addEventListener("change", () => set({ message: word.value.trim() || null }));
  out.push(applies(row(T("Word to show"), word), text));
  out.push(applies(row(T("Word size"),
    num(l.fontSize, 10, 200, 1, (v) => set({ fontSize: v }))), text));

  const names = { center: T("Centre"), "top-left": T("Top left"),
                  "top-right": T("Top right"), "bottom-left": T("Bottom left"),
                  "bottom-right": T("Bottom right") };
  out.push(applies(row(T("Position"), select(CORNERS.map((c) => [c, names[c]]),
    l.corner, (corner) => restyle({ corner }))), placed));
  // Centring makes the distance from an edge meaningless, so the margin is
  // dead under a dim AND under a centred cue -- a narrower condition than
  // the rest of the position row, exactly as on the desktop.
  out.push(applies(row(T("Edge margin"),
    num(l.margin, 0, 500, 1, (v) => set({ margin: v }))),
    placed && l.corner !== "center"));

  // The desktop's three presets. Hand-tuned timings show as Custom, which
  // cannot be picked -- only arrived at, by moving one of the four below it.
  const feelNames = { Gentle: T("Gentle"), Standard: T("Standard"), Sharp: T("Sharp") };
  const feel = feelOf(l);
  const choices = Object.keys(FEELS).map((f) => [f, feelNames[f]]);
  if (feel === "Custom") choices.push(["Custom", T("Custom")]);
  out.push(row(T("Flash style"), select(choices, feel, (f) => {
    if (FEELS[f]) restyle({ ...FEELS[f] });
  })));
  out.push(row(T("Hold (s)"), secs(l.hold, 0.05, 5, (v) => restyle({ hold: v }))));
  out.push(row(T("Fade (s)"), secs(l.fade, 0, 5, (v) => restyle({ fade: v }))));
  out.push(row(T("Pulses"), num(l.blinks, 1, 10, 1, (v) => restyle({ blinks: v }))));
  // Only meaningful once a reminder pulses more than once.
  out.push(applies(row(T("Gap between pulses"),
    secs(l.gap, 0, 2, (v) => restyle({ gap: v }))), l.blinks > 1));

  out.push(switchRow(T("Play a sound"), l.sound, (s) => restyle({ sound: s })));
  // A device can be muted and a volume left at the floor, and neither is
  // visible. Test plays this reminder's chime at this reminder's volume.
  const test = el("button", { textContent: T("Test") });
  test.addEventListener("click", () =>
    chrome.runtime.sendMessage({ type: "chime", volume: l.volume }));
  out.push(applies(row(T("Volume"),
    ...percent(Math.round(l.volume * 100), 20, (v) => set({ volume: v / 100 })),
    test), l.sound));

  // The break's countdown has no counterpart on the blink card, so the blink
  // carries the row dead rather than leaving a hole the break has to fill.
  out.push(applies(switchRow(T("Show countdown"), cfg.showCountdown, (v) => {
    cfg.showCountdown = v;
    save();
  }), kind === "brk"));

  const btn = el("button", { className: "preview",
    textContent: T(kind === "blink" ? "Preview blink" : "Preview break") });
  btn.addEventListener("click", () => preview(kind));
  out.push(btn);
  return out;
}

function preview(kind) {
  globalThis.__blinkReminderCue(pulseOf(cfg, kind, defaultWord(kind)));
  if (cfg[kind].sound) {
    chrome.runtime.sendMessage({ type: "chime", volume: cfg[kind].volume });
  }
}

// -- the page ---------------------------------------------------------------

async function render() {
  const lang = setLanguage(cfg.language);
  localize();
  document.title = DISPLAY_NAME;
  const granted = await chrome.permissions.contains(PAGE_ORIGINS);

  $("welcome").hidden = location.hash !== "#welcome";
  $("welcome-title").textContent = T("How this app works?");
  $("welcome-grant-box").hidden = granted;

  // The language IN FORCE, not "auto": a picker reading "auto" tells nobody
  // anything. Picking one stores that code, as the desktop does.
  $("language").replaceChildren(...LANGUAGES.map(([label, code]) =>
    new Option(label, code, false, code === lang)));

  $("enabled").checked = cfg.enabled;
  $("page-cue").checked = granted;

  $("blink-interval").replaceChildren(...INTERVALS.map((s) =>
    new Option(intervalLabel(s), s, false, s === cfg.blinkInterval)));
  $("break-enabled").checked = cfg.breakEnabled;
  $("break-minutes").replaceWith(Object.assign(segmented(
    BREAK_MINUTES.map((m) => [m, `${m} ${T("min")}`]), cfg.breakMinutes,
    (breakMinutes) => { cfg.breakMinutes = breakMinutes; save(); render(); }),
    { id: "break-minutes" }));
  for (const box of document.querySelectorAll(".look")) {
    box.replaceChildren(...lookControls(box.dataset.kind));
  }
  $("windows").hidden = !onWindows(navigator.userAgent);
}

$("language").addEventListener("change", (e) => {
  cfg.language = e.target.value; save(); render();
});
$("enabled").addEventListener("change", (e) => { cfg.enabled = e.target.checked; save(); });
$("break-enabled").addEventListener("change", (e) => {
  cfg.breakEnabled = e.target.checked; save();
});
$("blink-interval").addEventListener("change", (e) => {
  cfg.blinkInterval = Number(e.target.value); save();
});

async function setPageCue(on) {
  if (on) await chrome.permissions.request(PAGE_ORIGINS);
  else await chrome.permissions.remove(PAGE_ORIGINS);
  render();
}
$("page-cue").addEventListener("change", (e) => setPageCue(e.target.checked));
$("welcome-grant").addEventListener("click", () => setPageCue(true));
$("show-me").addEventListener("click", () => preview("blink"));
$("got-it").addEventListener("click", () => {
  history.replaceState(null, "", location.pathname);
  render();
});

$("coffee").href = SUPPORT_URL;
$("rate").href = reviewUrl(chrome.runtime.id, navigator.userAgent);
$("windows").href = WINDOWS_APP_URL;
for (const id of ["coffee", "rate", "windows"]) $(id).target = "_blank";

// A change made elsewhere -- the pop-up, another settings tab -- shows here.
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local" || !changes.cfg) return;
  const fresh = normalize(changes.cfg.newValue, CODES);
  if (JSON.stringify(fresh) !== JSON.stringify(cfg)) { cfg = fresh; render(); }
});
chrome.permissions.onAdded.addListener(render);
chrome.permissions.onRemoved.addListener(render);

render();
