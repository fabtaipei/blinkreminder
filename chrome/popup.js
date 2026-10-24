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

// The donation and review asks. They used to go out only as a notification,
// which the operating system may refuse to show -- and when it did, the ask
// was spent anyway and nobody ever saw it. Now it waits here until it is
// answered, and the toolbar carries a mark while it does.
async function renderAsk() {
  const { pendingAsk } = await chrome.storage.local.get("pendingAsk");
  $("ask").hidden = !pendingAsk;
  if (!pendingAsk) return;
  const donate = pendingAsk.kind === "donate";
  // Literal strings, so the build can check every language has them.
  $("ask-title").textContent =
    donate ? T("Like the app?") : T("Finding it useful?");
  $("ask-message").textContent = donate
    ? T("If this independent app works well for you, would you consider a small donation? Thank you!")
    : T("A short review helps others with tired eyes find it. Thank you!");
  $("ask-do").textContent = donate ? T("Buy me a coffee") : T("Rate this app");
}

async function answer(action) {
  const { pendingAsk } = await chrome.storage.local.get("pendingAsk");
  await chrome.runtime.sendMessage({ type: "ask-resolve", action });
  return pendingAsk;
}

async function render() {
  const { cfg, snoozed } = await load();
  setLanguage(cfg.language);
  localize();

  await renderAsk();
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
$("ask-do").addEventListener("click", async () => {
  const ask = await answer("done");
  chrome.tabs.create({ url: ask && ask.kind === "donate" ? SUPPORT_URL
    : reviewUrl(chrome.runtime.id, navigator.userAgent) });
  window.close();
});
$("ask-later").addEventListener("click", async () => {
  await answer("later");
  state = await render();
});
$("ask-never").addEventListener("click", async () => {
  await answer("never");
  state = await render();
});
$("settings").addEventListener("click", () => chrome.runtime.openOptionsPage());
$("howto").addEventListener("click", () =>
  chrome.tabs.create({ url: "options.html#welcome" }));
$("coffee").addEventListener("click", () => chrome.tabs.create({ url: SUPPORT_URL }));
$("rate").addEventListener("click", () => chrome.tabs.create(
  { url: reviewUrl(chrome.runtime.id, navigator.userAgent) }));
