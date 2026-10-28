// The settings page, and the welcome shown on install.
//
// Every change is saved as it is made -- the Chrome convention, and there is
// no window to close with a Save button anyway. The background worker hears
// the change in storage and reschedules.

import {
  MIN_INTERVAL, intervalUnit, intervalSeconds, SOUNDS, loadTutorial, questionDue,
  teachingPulse, captionInk,
  BREAK_MINUTES, CORNERS, FEELS, PAGE_ORIGINS, SUPPORT_URL, SUPPORT_EMAIL,
  WINDOWS_APP_URL, DISPLAY_NAME, normalize, feelOf, pulseOf, reviewUrl,
  onWindows,
} from "./core.js";
import { CODES, setLanguage, T, localize, defaultWord, noSpaces } from "./i18n.js";
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

// Every row names its own control. The label used to be a bare <span>, which
// left a screen reader on the Sound dropdown or the Volume slider announcing
// "combo box" or "slider" with nothing to say what it set. Every row on this
// page comes through here, so naming it here names nearly all of them.
let fieldSeq = 0;

function row(label, ...controls) {
  const id = "row" + (++fieldSeq);
  const tag = el("label", { id, textContent: label });
  // The number beside a slider is not the control; skip it when looking.
  const target = controls.find(
    (c) => c && c.nodeType === 1 && !c.classList.contains("pct"));
  if (target && /^(INPUT|SELECT|TEXTAREA)$/.test(target.tagName)) {
    if (!target.id) target.id = "f" + fieldSeq;
    tag.htmlFor = target.id;
  } else if (target && target.tagName === "DIV") {
    // A row of buttons cannot be the target of <label for>, so the group
    // carries the name instead.
    target.setAttribute("role", "group");
    target.setAttribute("aria-labelledby", id);
  }
  return el("div", { className: "row" }, tag,
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
  group.setAttribute("role", "group");
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

  const styles = segmented(
    [["dot", T("A dot")], ["text", T("A word")], ["dim", T("Dim screen")]],
    l.style, (s) => restyle({ style: s }));
  // This row carries no caption of its own -- the card's heading is the
  // caption -- so the group borrows it rather than inventing a word that
  // would need translating into thirty languages to say what is already there.
  styles.setAttribute("aria-labelledby", kind === "blink" ? "blink-h" : "break-h");
  const style = el("div", { className: "row" }, styles);
  const strength = row(T("Strength"),
    ...percent(Math.round(l.opacity * 100), 2, (v) => set({ opacity: v / 100 })));
  strength.dataset.point = "strength";
  const sound = switchRow(T("Play a sound"), l.sound, (s) => set({ sound: s }));
  sound.dataset.point = "sound";

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
    const size = row(T("Dot size"), ...percent(l.dotPct, 5, (v) => set({ dotPct: v })));
    size.dataset.point = "size";
    rows.append(size);
  }
  if (l.style === "text") {
    const word = el("input", { type: "text", value: l.message || "",
                               placeholder: defaultWord(kind), maxLength: 60 });
    word.addEventListener("change", () => set({ message: word.value.trim() || null }));
    rows.append(row(T("Word to show"), word));
    const size = row(T("Word size"),
                     num(l.fontSize, 10, 200, 1, (v) => set({ fontSize: v })));
    size.dataset.point = "size";
    rows.append(size);
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
  const hold = row(T("Hold (s)"), secs(l.hold, 0.05, 5, (v) => restyle({ hold: v })));
  hold.dataset.point = "duration";
  rows.append(hold);
  rows.append(row(T("Fade (s)"), secs(l.fade, 0, 5, (v) => restyle({ fade: v }))));
  rows.append(row(T("Pulses"), num(l.blinks, 1, 10, 1, (v) => restyle({ blinks: v }))));
  // Only meaningful once a reminder pulses more than once.
  if (l.blinks > 1) {
    rows.append(row(T("Gap between pulses"),
                    secs(l.gap, 0, 2, (v) => restyle({ gap: v }))));
  }

  // A device can be muted and a volume left at the floor, and neither is
  // visible. Test plays this reminder's chime at this reminder's volume.
  const names = { ding: T("Ding"), chord: T("Chord"), chime: T("Chime"),
                  notify: T("Notify") };
  rows.append(row(T("Sound"), select(SOUNDS.map((s) => [s, names[s]]), l.soundName,
                                     (soundName) => restyle({ soundName }))));
  const test = el("button", { textContent: T("Test") });
  test.addEventListener("click", () =>
    chrome.runtime.sendMessage({ type: "chime", volume: l.volume, name: l.soundName }));
  rows.append(row(T("Volume"),
                  ...percent(Math.round(l.volume * 100), 1,
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
  const count = num(value, unit === 60 ? 1 : MIN_INTERVAL, 999, 1,
                    (v) => apply(v, unit));
  // The caption for this pair sits in the row above, so the box says what it
  // is itself; the seconds/minutes buttons are inside the named group and
  // read as its options.
  count.setAttribute("aria-label", T("Remind me every"));
  return [
    count,
    segmented([[1, T("seconds")], [60, T("minutes")]], unit, (u) => apply(value, u)),
  ];
}

// -- the tutorial ------------------------------------------------------------

// Which card a question button leads to: the blink's, since the lesson is
// about the blink reminder.
const POINTS = ["strength", "size", "duration", "sound"];

async function endQuestion() {
  const { tutorial } = await chrome.storage.local.get("tutorial");
  const t = loadTutorial(tutorial);
  t.question = "done";
  await chrome.storage.local.set({ tutorial: t });
  $("question").hidden = true;
}

// Open whatever has to be open, bring the row into view, and ring it.
async function pointAt(target) {
  if (target === "size" || target === "duration") advOpen.blink = true;
  await render();
  const row = document.querySelector(`#blink-card [data-point="${target}"]`);
  if (!row) return;
  row.scrollIntoView({ block: "center", behavior: "smooth" });
  row.classList.remove("ring");
  void row.offsetWidth;                       // restart the animation
  row.classList.add("ring");
  setTimeout(() => row.classList.remove("ring"), 6000);
}

function questionButtons() {
  const out = POINTS.map((p) => {
    const b = el("button", { className: "tint",
      textContent: T(p === "strength" ? "Strength"
                   : p === "size" ? "Size"
                   : p === "duration" ? "Duration" : "Sound") });
    b.addEventListener("click", () => pointAt(p));
    return b;
  });
  const got = el("button", { className: "primary", textContent: T("Got it") });
  got.addEventListener("click", endQuestion);
  out.push(got);
  return out;
}

// Show me: one reminder exactly as the first few are taught, then the
// question about it -- the same pairing the desktop welcome card has.
async function showMe() {
  const pulse = teachingPulse(pulseOf(cfg, "blink", defaultWord("blink")),
                              T("Close…\nsqueeze…\nopen"), noSpaces());
  pulse.ink = captionInk(pulse.colour);
  globalThis.__blinkReminderCue(pulse);
  if (cfg.blink.sound) {
    chrome.runtime.sendMessage({ type: "chime", volume: cfg.blink.volume,
                                 name: cfg.blink.soundName });
  }
  const { tutorial } = await chrome.storage.local.get("tutorial");
  if (loadTutorial(tutorial).question !== "done") {
    setTimeout(() => { $("question").hidden = false; }, 1200);
  }
}

function preview(kind) {
  globalThis.__blinkReminderCue(pulseOf(cfg, kind, defaultWord(kind)));
  if (cfg[kind].sound) {
    chrome.runtime.sendMessage({ type: "chime", volume: cfg[kind].volume,
                                 name: cfg[kind].soundName });
  }
}

// -- the page ---------------------------------------------------------------

async function render() {
  const lang = setLanguage(cfg.language);
  localize();
  document.title = DISPLAY_NAME;
  const granted = await chrome.permissions.contains(PAGE_ORIGINS);

  // The same facts the desktop app puts in its report dialog, and left
  // untranslated for the same reason the log is: a version string means the
  // same thing in every language, and a report arriving in one the author
  // cannot read helps nobody.
  $("report-card").hidden = location.hash !== "#report";
  $("report-title").textContent = T("Report a problem");
  $("report-mail").textContent = SUPPORT_EMAIL;
  $("report-details").textContent = [
    `${DISPLAY_NAME} ${chrome.runtime.getManifest().version} (Chrome)`,
    navigator.userAgent,
    `Language: ${chrome.i18n.getUILanguage()}`,
  ].join("\n");

  $("welcome").hidden = location.hash !== "#welcome";
  $("welcome-title").textContent = T("How this app works?");
  $("welcome-grant-box").hidden = granted;

  const { tutorial } = await chrome.storage.local.get("tutorial");
  const asking = location.hash === "#question" && questionDue(loadTutorial(tutorial));
  if (asking) $("question").hidden = false;
  $("question-title").textContent = T("Too weak or intrusive?");
  $("question-buttons").replaceChildren(...questionButtons());

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
  // The heading sits in the row above these, so say in the group what the
  // layout says in space.
  $("blink-interval").setAttribute("role", "group");
  $("blink-interval").setAttribute("aria-label", T("Remind me every"));
  $("break-enabled").checked = cfg.breakEnabled;
  const minutes = Object.assign(segmented(
    BREAK_MINUTES.map((m) => [m, `${m} ${T("min")}`]), cfg.breakMinutes,
    (breakMinutes) => { cfg.breakMinutes = breakMinutes; save(); render(); }),
    { id: "break-minutes" });
  // No visible caption of its own -- the cards are aligned, and this row is
  // blank on the blink side -- so the switch above it supplies the name.
  minutes.setAttribute("aria-label", T("Remind me to look away"));
  $("break-minutes").replaceWith(minutes);
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
$("show-me").addEventListener("click", showMe);
$("got-it").addEventListener("click", () => {
  history.replaceState(null, "", location.pathname);
  render();
});

$("coffee").href = SUPPORT_URL;
$("rate").href = reviewUrl(chrome.runtime.id, navigator.userAgent);
$("windows").href = WINDOWS_APP_URL;
// Not an href: this page IS the report card, so it reveals the section and
// leaves the user where they already were rather than reloading.
$("report").addEventListener("click", () => {
  location.hash = "#report";
  $("report-card").hidden = false;
  $("report-card").scrollIntoView({ block: "start" });
});
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
