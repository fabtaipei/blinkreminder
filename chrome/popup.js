// The toolbar pop-up: the tray menu of the desktop app, plus the interval.

import { MIN_INTERVAL, intervalUnit, intervalSeconds, PAGE_ORIGINS,
         SUPPORT_URL, normalize, msToNextBreak, reviewUrl } from "./core.js";
import { CODES, setLanguage, T, localize } from "./i18n.js";

const $ = (id) => document.getElementById(id);

// How often to blink: a number and a unit, the same pair the settings page
// and the desktop panel use. Switching the unit reinterprets the number.
function intervalControl(cfg, onSet) {
  const unit = intervalUnit(cfg.blinkInterval);
  const value = Math.round(cfg.blinkInterval / unit);
  const box = document.createElement("input");
  Object.assign(box, { type: "number", min: unit === 60 ? 1 : MIN_INTERVAL,
                       max: 999, step: 1, value });
  box.addEventListener("change", () => onSet(intervalSeconds(box.value, unit)));
  const units = document.createElement("select");
  for (const [u, label] of [[1, T("seconds")], [60, T("minutes")]]) {
    units.append(new Option(label, String(u), false, u === unit));
  }
  units.addEventListener("change", () =>
    onSet(intervalSeconds(value, Number(units.value))));
  return [box, units];
}

async function load() {
  const { cfg, snoozeUntil } = await chrome.storage.local.get(["cfg", "snoozeUntil"]);
  return { cfg: normalize(cfg, CODES),
           snoozed: snoozeUntil && snoozeUntil > Date.now() ? snoozeUntil : 0 };
}

async function save(cfg) {
  await chrome.storage.local.set({ cfg });
}

async function render() {
  const { cfg, snoozed } = await load();
  setLanguage(cfg.language);
  localize();

  $("enabled").checked = cfg.enabled;
  $("interval").replaceChildren(...intervalControl(cfg, async (seconds) => {
    await save({ ...cfg, blinkInterval: seconds });
    state = await render();
  }));
  $("snooze").textContent = snoozed ? T("Resume reminders") : T("Snooze 30 minutes");
  $("snooze").disabled = !cfg.enabled;
  $("break-row").hidden = !(cfg.enabled && cfg.breakEnabled && !snoozed);
  $("page-cue").hidden = await chrome.permissions.contains(PAGE_ORIGINS);
  tick(cfg);
  return { cfg, snoozed };
}

let timer = null;
function tick(cfg) {
  clearTimeout(timer);
  const left = Math.ceil(msToNextBreak(cfg.breakMinutes) / 1000);
  $("countdown").textContent =
    `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
  timer = setTimeout(() => tick(cfg), 1000 - (Date.now() % 1000));
}

let state = await render();

$("enabled").addEventListener("change", async (e) => {
  await save({ ...state.cfg, enabled: e.target.checked });
  state = await render();
});
$("blink-now").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "blink-now" });
  window.close();                       // out of the way of the cue
});
$("snooze").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: state.snoozed ? "resume" : "snooze" });
  state = await render();
});
$("grant").addEventListener("click", async () => {
  // Chrome may close the pop-up to show its own prompt; the grant still
  // lands, and the next opening shows it.
  await chrome.permissions.request(PAGE_ORIGINS);
  state = await render();
});
$("settings").addEventListener("click", () => chrome.runtime.openOptionsPage());
$("howto").addEventListener("click", () =>
  chrome.tabs.create({ url: "options.html#welcome" }));
$("coffee").addEventListener("click", () => chrome.tabs.create({ url: SUPPORT_URL }));
$("rate").addEventListener("click", () => chrome.tabs.create(
  { url: reviewUrl(chrome.runtime.id, navigator.userAgent) }));
