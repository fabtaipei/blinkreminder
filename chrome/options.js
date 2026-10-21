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

// -- one reminder's look ----------------------------------------------------

// The literals are here, not in a table, so the build can find every one and
// prove all thirty languages have it.
function lookControls(kind) {
  const l = cfg[kind];
  const box = el("div");
  const restyle = (patch) => { Object.assign(l, patch); save(); render(); };
  const set = (patch) => { Object.assign(l, patch); save(); };

  box.append(el("div", { className: "row" }, segmented(
    [["dot", T("A dot")], ["text", T("A word")], ["dim", T("Dim screen")]],
    l.style, (style) => restyle({ style }))));
  box.append(row(T("Strength"),
    ...percent(Math.round(l.opacity * 100), 2, (v) => set({ opacity: v / 100 }))));

  const colour = el("input", { type: "color", value: l.colour });
  colour.addEventListener("change", () => set({ colour: colour.value }));
  box.append(row(T("Colour"), colour));

  if (l.style === "dot") {
    box.append(row(T("Dot size"), ...percent(l.dotPct, 5, (v) => set({ dotPct: v }))));
  }
  if (l.style === "text") {
    const word = el("input", { type: "text", value: l.message || "",
                               placeholder: defaultWord(kind), maxLength: 60 });
    word.addEventListener("change", () => set({ message: word.value.trim() || null }));
    box.append(row(T("Word to show"), word));
    const size = el("input", { type: "number", min: 10, max: 200, value: l.fontSize });
    size.addEventListener("change", () => set({ fontSize: Number(size.value) }));
    box.append(row(T("Word size"), size));
  }
  if (l.style !== "dim") {
    const names = { center: T("Centre"), "top-left": T("Top left"),
                    "top-right": T("Top right"), "bottom-left": T("Bottom left"),
                    "bottom-right": T("Bottom right") };
    box.append(row(T("Position"), select(CORNERS.map((c) => [c, names[c]]),
                                         l.corner, (corner) => set({ corner }))));
  }

  // The desktop's three presets. Hand-tuned timings show as Custom, which
  // cannot be picked -- only arrived at.
  const feelNames = { Gentle: T("Gentle"), Standard: T("Standard"), Sharp: T("Sharp") };
  const feel = feelOf(l);
  const choices = Object.keys(FEELS).map((f) => [f, feelNames[f]]);
  if (feel === "Custom") choices.push(["Custom", T("Custom")]);
  box.append(row(T("Flash style"), select(choices, feel, (f) => {
    if (FEELS[f]) restyle({ ...FEELS[f] });
  })));

  box.append(switchRow(T("Play a sound"), l.sound, (sound) => set({ sound })));
  return box;
}

function preview(kind) {
  globalThis.__blinkReminderCue(pulseOf(cfg, kind, defaultWord(kind)));
  if (cfg[kind].sound) chrome.runtime.sendMessage({ type: "chime" });
}

// -- the page ---------------------------------------------------------------

async function render() {
  const lang = setLanguage(cfg.language);
  localize();
  document.title = DISPLAY_NAME;
  const granted = await chrome.permissions.contains(PAGE_ORIGINS);

  $("welcome").hidden = location.hash !== "#welcome";
  $("welcome-title").textContent = T("%s is running").replace("%s", DISPLAY_NAME);
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
  $("countdown").checked = cfg.showCountdown;

  for (const box of document.querySelectorAll(".look")) {
    box.replaceChildren(lookControls(box.dataset.kind));
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
$("countdown").addEventListener("change", (e) => {
  cfg.showCountdown = e.target.checked; save();
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

for (const b of document.querySelectorAll("button.preview")) {
  b.addEventListener("click", () => preview(b.dataset.kind));
}
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
