// The settings page, and the welcome shown on install.
//
// Every change is saved as it is made -- the Chrome convention, and there is
// no window to close with a Save button anyway. The background worker hears
// the change in storage and reschedules.

import {
  MIN_INTERVAL, intervalUnit, intervalSeconds,
  BREAK_MINUTES, CORNERS, FEELS, PAGE_ORIGINS, SUPPORT_URL,
  WINDOWS_APP_URL, DISPLAY_NAME, normalize, feelOf, pulseOf, reviewUrl,
  onWindows,
} from "./core.js";
import { CODES, setLanguage, T, localize, defaultWord } from "./i18n.js";
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

// -- one reminder's controls -------------------------------------------------

// Both cards show the same four things in the same order -- style, strength,
// sound, Advanced -- so every row on the blink card sits level with its twin
// on the break card. What applies to one style and not another, and what is
// set once and then left alone, goes inside Advanced, where a row that does
// not apply is simply absent. That split is why the two cards line up, and
// it is the shape the desktop panel has.
//
// The literals are here, not in a table, so the build can find every one and
// prove all thirty languages have it.

// Advanced is rebuilt on every render, so whether it was open has to be
// remembered outside it, or changing a control inside would close it.
const advOpen = { blink: false, brk: false };

function lookControls(kind) {
  const l = cfg[kind];
  const set = (patch) => { Object.assign(l, patch); save(); };
  // A change of style, position or timing changes which rows apply or what
  // they read, so those redraw the card.
  const restyle = (patch) => { Object.assign(l, patch); save(); render(); };

  const style = el("div", { className: "row" }, segmented(
    [["dot", T("A dot")], ["text", T("A word")], ["dim", T("Dim screen")]],
    l.style, (s) => restyle({ style: s })));
  const strength = row(T("Strength"),
    ...percent(Math.round(l.opacity * 100), 2, (v) => set({ opacity: v / 100 })));
  const sound = switchRow(T("Play a sound"), l.sound, (s) => set({ sound: s }));

  const btn = el("button", { className: "preview",
    textContent: T(kind === "blink" ? "Preview blink" : "Preview break") });
  btn.addEventListener("click", () => preview(kind));

  return [style, strength, sound, advanced(kind, l, set, restyle), btn];
}

function advanced(kind, l, set, restyle) {
  const box = el("details", { className: "advanced", open: advOpen[kind] });
  box.addEventListener("toggle", () => { advOpen[kind] = box.open; });
  // Trimmed: the desktop's label carries two leading spaces to clear the
  // arrow drawn beside it, and here the arrow is drawn by CSS.
  box.append(el("summary", { textContent: T("  Advanced settings").trim() }));
  const rows = el("div", { className: "adv-rows" });
  box.append(rows);

  const colour = el("input", { type: "color", value: l.colour });
  colour.addEventListener("change", () => set({ colour: colour.value }));
  rows.append(row(T("Colour"), colour));

  if (l.style === "dot") {
    rows.append(row(T("Dot size"), ...percent(l.dotPct, 5, (v) => set({ dotPct: v }))));
  }
  if (l.style === "text") {
    const word = el("input", { type: "text", value: l.message || "",
                               placeholder: defaultWord(kind), maxLength: 60 });
    word.addEventListener("change", () => set({ message: word.value.trim() || null }));
    rows.append(row(T("Word to show"), word));
    rows.append(row(T("Word size"),
                    num(l.fontSize, 10, 200, 1, (v) => set({ fontSize: v }))));
  }
  if (l.style !== "dim") {
    const names = { center: T("Centre"), "top-left": T("Top left"),
                    "top-right": T("Top right"), "bottom-left": T("Bottom left"),
                    "bottom-right": T("Bottom right") };
    rows.append(row(T("Position"), select(CORNERS.map((c) => [c, names[c]]),
                                          l.corner, (corner) => restyle({ corner }))));
    // Centring makes the distance from an edge meaningless, so the control
    // for it is absent rather than dead.
    if (l.corner !== "center") {
      rows.append(row(T("Edge margin"),
                      num(l.margin, 0, 500, 1, (v) => set({ margin: v }))));
    }
  }

  // The desktop's three presets. Hand-tuned timings show as Custom, which
  // cannot be picked -- only arrived at, by moving one of the four below it.
  const feelNames = { Gentle: T("Gentle"), Standard: T("Standard"), Sharp: T("Sharp") };
  const feel = feelOf(l);
  const choices = Object.keys(FEELS).map((f) => [f, feelNames[f]]);
  if (feel === "Custom") choices.push(["Custom", T("Custom")]);
  rows.append(row(T("Flash style"), select(choices, feel, (f) => {
    if (FEELS[f]) restyle({ ...FEELS[f] });
  })));
  rows.append(row(T("Hold (s)"), secs(l.hold, 0.05, 5, (v) => restyle({ hold: v }))));
  rows.append(row(T("Fade (s)"), secs(l.fade, 0, 5, (v) => restyle({ fade: v }))));
  rows.append(row(T("Pulses"), num(l.blinks, 1, 10, 1, (v) => restyle({ blinks: v }))));
  // Only meaningful once a reminder pulses more than once.
  if (l.blinks > 1) {
    rows.append(row(T("Gap between pulses"),
                    secs(l.gap, 0, 2, (v) => restyle({ gap: v }))));
  }

  // A device can be muted and a volume left at the floor, and neither is
  // visible. Test plays this reminder's chime at this reminder's volume.
  const test = el("button", { textContent: T("Test") });
  test.addEventListener("click", () =>
    chrome.runtime.sendMessage({ type: "chime", volume: l.volume }));
  rows.append(row(T("Volume"),
                  ...percent(Math.round(l.volume * 100), 20,
                             (v) => set({ volume: v / 100 })), test));

  // The break's alone: the blink has no countdown to show.
  if (kind === "brk") {
    rows.append(switchRow(T("Show countdown"), cfg.showCountdown, (v) => {
      cfg.showCountdown = v;
      save();
    }));
  }
  return box;
}

// How often to blink: a number and a unit, as the desktop's panel asks it,
// rather than a list of fixed choices. Switching the unit reinterprets the
// number -- 60 with minutes picked means every 60 minutes -- which is what
// the desktop does, and what makes the pair read as one sentence.
function intervalControl() {
  const unit = intervalUnit(cfg.blinkInterval);
  const value = Math.round(cfg.blinkInterval / unit);
  const apply = (v, u) => {
    cfg.blinkInterval = intervalSeconds(v, u);
    save();
    render();
  };
  return [
    num(value, unit === 60 ? 1 : MIN_INTERVAL, 999, 1, (v) => apply(v, unit)),
    segmented([[1, T("seconds")], [60, T("minutes")]], unit, (u) => apply(value, u)),
  ];
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
  // Drawn on the page, so it needs the same access the cue does.
  $("page-dot").checked = cfg.pageDot && granted;
  $("page-dot").disabled = !granted;
  $("page-dot").closest(".row").classList.toggle("off", !granted);

  $("blink-interval").replaceChildren(...intervalControl());
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

async function setPageCue(on) {
  if (on) await chrome.permissions.request(PAGE_ORIGINS);
  else await chrome.permissions.remove(PAGE_ORIGINS);
  render();
}
$("page-cue").addEventListener("change", (e) => setPageCue(e.target.checked));
$("page-dot").addEventListener("change", (e) => {
  cfg.pageDot = e.target.checked;
  save();
});
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
