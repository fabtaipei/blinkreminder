// The schedule, and getting each reminder in front of someone.
//
// A service worker: Chrome stops it whenever it is idle and starts it again
// for the next event, so nothing here lives in a variable between events.
// Settings, the snooze and the ask count are in storage; the timers are
// chrome.alarms, which outlive the worker.

import {
  DISPLAY_NAME, SNOOZE_MINUTES, SUPPORT_URL, ASK_SETTLE_MS, normalize, pulseOf,
  pulseMs, msToNextBreak, isStale, drawable, todayIso, loadAsks, countDay,
  dueAsk, reviewUrl, PAGE_ORIGINS, TEACH_COUNT, freshTutorial, loadTutorial,
  teachingDue, questionDue, teachingPulse,
} from "./core.js";
import { CODES, setLanguage, T, defaultWord, captionLine, noSpaces } from "./i18n.js";

// The corner dot, while it is switched on: a content script on every page
// the user has granted, rather than an injection per reminder, because it
// has to be there the whole time and survive navigation.
const DOT_SCRIPT = {
  id: "page-dot",
  js: ["dot.js"],
  matches: ["http://*/*", "https://*/*"],
  runAt: "document_idle",
};

// A blink this late was missed while the computer slept. Chrome fires every
// missed alarm on waking; firing them is a burst of noise, not a reminder.
const BLINK_STALE_MS = 20000;
const BREAK_STALE_MS = 120000;

// -- state ------------------------------------------------------------------

async function getCfg() {
  const { cfg } = await chrome.storage.local.get("cfg");
  const c = normalize(cfg, CODES);
  setLanguage(c.language);
  return c;
}

async function getTutorial() {
  const { tutorial } = await chrome.storage.local.get("tutorial");
  return loadTutorial(tutorial);
}

async function setTutorial(t) {
  await chrome.storage.local.set({ tutorial: t });
}

async function snoozedUntil() {
  const { snoozeUntil } = await chrome.storage.local.get("snoozeUntil");
  return snoozeUntil && snoozeUntil > Date.now() ? snoozeUntil : 0;
}

async function sessionValue(key, fallback) {
  const got = (await chrome.storage.session.get(key))[key];
  return got === undefined ? fallback : got;
}

// -- the schedule -----------------------------------------------------------

async function schedule() {
  const cfg = await getCfg();
  const snooze = await snoozedUntil();
  const live = cfg.enabled && !snooze;

  if (live) {
    // Recreated only when missing or changed: recreating it on every wake
    // would restart the interval each time and push the next blink back.
    const period = cfg.blinkInterval / 60;
    const current = await chrome.alarms.get("blink");
    if (!current || current.periodInMinutes !== period) {
      await chrome.alarms.create("blink", { delayInMinutes: period,
                                           periodInMinutes: period });
    }
  } else {
    await chrome.alarms.clear("blink");
  }

  if (live && cfg.breakEnabled) {
    await chrome.alarms.create("break",
      { when: Date.now() + msToNextBreak(cfg.breakMinutes) });
  } else {
    await chrome.alarms.clear("break");
  }

  await syncPageDot(cfg);

  if (snooze) await chrome.alarms.create("snooze", { when: snooze });
  else await chrome.alarms.clear("snooze");

  // On the minute, so the badge's minutes-to-break turns over when the
  // clock does rather than up to a minute late.
  if (!(await chrome.alarms.get("tick"))) {
    const now = Date.now();
    await chrome.alarms.create("tick",
      { when: now + 60000 - (now % 60000) + 500, periodInMinutes: 1 });
  }
  await updateBadge(cfg, live);
}

async function nextBreakAfterThisOne() {
  const cfg = await getCfg();
  if (!cfg.enabled || !cfg.breakEnabled || (await snoozedUntil())) return;
  // Measured from a few seconds ahead: an alarm that fired a hair early
  // would otherwise find the boundary it is meant to mark still in front
  // of it, and schedule the same break twice.
  const ahead = Date.now() + 5000;
  await chrome.alarms.create("break",
    { when: ahead + msToNextBreak(cfg.breakMinutes, new Date(ahead)) });
}

// Register or remove the corner dot, and bring every page already open
// into line -- a registered script only reaches pages loaded after it.
async function syncPageDot(cfg) {
  let on = false;
  try {
    on = cfg.pageDot && await chrome.permissions.contains(PAGE_ORIGINS);
    const already = (await chrome.scripting.getRegisteredContentScripts(
      { ids: [DOT_SCRIPT.id] })).length > 0;
    if (on && !already) await chrome.scripting.registerContentScripts([DOT_SCRIPT]);
    if (!on && already) {
      await chrome.scripting.unregisterContentScripts({ ids: [DOT_SCRIPT.id] });
    }
    console.log("page dot:", on ? "on" : "off",
                "registered:", (await chrome.scripting.getRegisteredContentScripts(
                  { ids: [DOT_SCRIPT.id] })).length);
    if (on === already) return;                       // nothing changed
  } catch (e) {
    console.warn("page dot", e);
    return;
  }
  for (const tab of await chrome.tabs.query({ url: ["http://*/*", "https://*/*"] })) {
    try {
      if (on) {
        await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["dot.js"] });
      } else {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => { globalThis.__blinkReminderDot?.off(); },
        });
      }
    } catch { /* a page this extension may not touch; nothing to do */ }
  }
}

async function updateBadge(cfg, live) {
  const icon = live ? "icon" : "icon-off";
  await chrome.action.setIcon({ path: { 16: `icons/${icon}-16.png`,
                                        32: `icons/${icon}-32.png` } });
  let text = "";
  if (live && cfg.breakEnabled && cfg.showCountdown) {
    text = String(Math.ceil(msToNextBreak(cfg.breakMinutes) / 60000));
  }
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color: "#3A3A3A" });
  await chrome.action.setBadgeTextColor({ color: "#F2F3F5" });
}

// -- delivering a reminder --------------------------------------------------

// The active tab of the window in use, or null if Chrome is not in front.
async function frontTab() {
  let win;
  try {
    win = await chrome.windows.getLastFocused({ windowTypes: ["normal"] });
  } catch {
    return null;
  }
  if (!win || !win.focused || win.state === "minimized") return null;
  const [tab] = await chrome.tabs.query({ active: true, windowId: win.id });
  return tab || null;
}

async function draw(tabId, pulse) {
  await chrome.scripting.executeScript({ target: { tabId }, files: ["cue.js"] });
  await chrome.scripting.executeScript({
    target: { tabId },
    // Not returned: the cue runs for seconds, and nothing here waits on it.
    func: (p) => { globalThis.__blinkReminderCue(p); },
    args: [pulse],
  });
}

async function notify(kind, pulse) {
  const id = "cue-" + kind;
  await chrome.notifications.clear(id);
  await chrome.notifications.create(id, {
    type: "basic",
    iconUrl: "icons/icon-128.png",
    title: DISPLAY_NAME,
    message: kind === "blink" ? captionLine() : pulse.message,
    silent: !pulse.sound,
    priority: kind === "break" ? 1 : 0,
  });
  // A reminder, not a message to keep: gone once it has done its job, so a
  // day of blinks does not pile up in the notification centre.
  setTimeout(() => chrome.notifications.clear(id), kind === "blink" ? 4000 : 20000);
}

// Played from an offscreen document: a web page may not make a sound until
// someone has clicked it, and the cue never asks anyone to click.
async function chime(volume = 0.6) {
  try {
    const open = await chrome.runtime.getContexts(
      { contextTypes: ["OFFSCREEN_DOCUMENT"] });
    if (!open.length) {
      await chrome.offscreen.createDocument({
        url: "offscreen.html", reasons: ["AUDIO_PLAYBACK"],
        justification: "Plays the reminder's chime.",
      });
    }
    await chrome.runtime.sendMessage({ target: "offscreen", type: "chime", volume });
  } catch (e) {
    console.warn("chime", e);
  }
}

// Show one reminder. Returns how it went, for "Blink now" and the tests.
//
// On a web page if the on-page cue is switched on and Chrome is in front.
// Otherwise a notification -- except a timed blink, which is skipped while
// Chrome is not in front: a toast every minute over another app is exactly
// the interruption this was built not to be. A break still comes through,
// because a break is the one that matters.
export async function deliver(kind, { manual = false } = {}) {
  const cfg = await getCfg();
  if (!manual) {
    if (!cfg.enabled || (await snoozedUntil())) return "off";
    if (kind === "break" && !cfg.breakEnabled) return "off";
    if ((await chrome.idle.queryState(60)) !== "active") return "away";
    if (kind === "blink" && Date.now() < (await sessionValue("quietUntil", 0))) {
      return "break showing";
    }
  }
  let pulse = pulseOf(cfg, kind, defaultWord(kind));
  // The first few blink reminders carry the instruction, and the question
  // follows the last of them. A manual "Blink now" is not one of the few.
  let teach = false;
  if (kind === "blink" && !manual) {
    const t = await getTutorial();
    if (teachingDue(t)) {
      t.taught += 1;
      await setTutorial(t);
      pulse = teachingPulse(pulse, T("Close…\nsqueeze…\nopen"), noSpaces());
      teach = !teachingDue(t);
    }
  }
  if (kind === "break") {
    await chrome.storage.session.set({ quietUntil: Date.now() + pulseMs(pulse) + 1000 });
  }
  // Once the reminder it is about has faded, not during it.
  if (teach) setTimeout(askQuestion, pulseMs(pulse) + 800);

  if (await chrome.permissions.contains(PAGE_ORIGINS)) {
    const tab = await frontTab();
    if (tab && drawable(tab.url)) {
      try {
        await draw(tab.id, pulse);
        if (pulse.sound) await chime(pulse.volume);
        return "page";
      } catch (e) {
        console.warn("draw", e);          // the page refused; fall through
      }
    }
    if (kind === "blink" && !manual) return "not in front";
  }
  await notify(kind, pulse);
  return "notification";
}

// "Too weak or intrusive?" -- a notification rather than a card drawn on
// someone's page: the answers lead to the settings, and a notification is
// where the browser already puts a question it wants answered.
async function askQuestion() {
  if (!questionDue(await getTutorial())) return;
  await chrome.notifications.create("question", {
    type: "basic", iconUrl: "icons/icon-128.png", requireInteraction: true,
    title: T("Too weak or intrusive?"),
    message: [T("Strength"), T("Size"), T("Duration"), T("Sound")].join(" · "),
    buttons: [{ title: T("Settings") }, { title: T("Got it") }],
  });
}

async function endQuestion() {
  const t = await getTutorial();
  t.question = "done";
  await setTutorial(t);
}

// -- days of use, and the asks ----------------------------------------------

async function fullscreenInFront() {
  try {
    const win = await chrome.windows.getLastFocused();
    return win.focused && win.state === "fullscreen";
  } catch {
    return false;
  }
}

async function checkAsks(cfg) {
  const today = todayIso();
  const st = loadAsks((await chrome.storage.local.get("asks")).asks);
  if (countDay(st, today)) await chrome.storage.local.set({ asks: st });
  const pick = dueAsk(st, today, (kind) => kind !== "donate" || !!SUPPORT_URL);
  if (!pick) return;
  // Not in the first minutes after the browser starts, not while snoozed,
  // away or fullscreen. Each leaves the ask due for the next minute.
  if (Date.now() - (await sessionValue("startedAt", 0)) < ASK_SETTLE_MS) return;
  if (!cfg.enabled || (await snoozedUntil())) return;
  if ((await chrome.idle.queryState(60)) !== "active") return;
  if (await fullscreenInFront()) return;

  const [day, kind] = pick;
  // Spent BEFORE it is shown, as on the desktop: a lost ask is better than
  // one that reappears every minute because showing it failed.
  st.shown.push(day);
  st.last_ask = today;
  await chrome.storage.local.set({ asks: st });
  // Literal strings, so the build can check every language has them.
  const card = kind === "donate"
    ? { title: T("Like the app?"),
        message: T("If this independent app works well for you, would you consider a small donation? Thank you!"),
        buttons: [{ title: T("Buy me a coffee") }, { title: T("Don’t ask again") }] }
    : { title: T("Finding it useful?"),
        message: T("A short review helps others with tired eyes find it. Thank you!"),
        buttons: [{ title: T("Rate this app") }] };
  await chrome.notifications.create("ask-" + kind, {
    type: "basic", iconUrl: "icons/icon-128.png", requireInteraction: true,
    priority: 0, ...card,
  });
}

chrome.notifications.onButtonClicked.addListener(async (id, index) => {
  if (id === "question") {
    await endQuestion();
    if (index === 0) await chrome.tabs.create({ url: "options.html#question" });
  } else if (id === "ask-donate" && index === 0) {
    await chrome.tabs.create({ url: SUPPORT_URL });
  } else if (id === "ask-donate" && index === 1) {
    const st = loadAsks((await chrome.storage.local.get("asks")).asks);
    st.opted_out = true;            // every ask, reviews included
    await chrome.storage.local.set({ asks: st });
  } else if (id === "ask-review" && index === 0) {
    await chrome.tabs.create({ url: reviewUrl(chrome.runtime.id, navigator.userAgent) });
  }
  await chrome.notifications.clear(id);
});

// -- events -----------------------------------------------------------------

chrome.alarms.onAlarm.addListener(async (alarm) => {
  const now = Date.now();
  if (alarm.name === "blink") {
    if (!isStale(alarm.scheduledTime, now, BLINK_STALE_MS)) await deliver("blink");
  } else if (alarm.name === "break") {
    if (!isStale(alarm.scheduledTime, now, BREAK_STALE_MS)) await deliver("break");
    await nextBreakAfterThisOne();
  } else if (alarm.name === "snooze") {
    await chrome.storage.local.remove("snoozeUntil");    // onChanged reschedules
  } else if (alarm.name === "tick") {
    const cfg = await getCfg();
    await updateBadge(cfg, cfg.enabled && !(await snoozedUntil()));
    await checkAsks(cfg);
  }
});

// A belt to the registration's braces. A registered content script should
// reach every page on its own, but it is the one part of this that depends
// on Chrome having accepted a registration made while the extension was
// running; injecting again as each page finishes loading costs nothing when
// the script is already there -- dot.js returns immediately if it is -- and
// means the dot does not quietly go missing if the registration did not take.
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (info.status !== "complete" || !drawable(tab.url)) return;
  const cfg = await getCfg();
  if (!cfg.pageDot || !(await chrome.permissions.contains(PAGE_ORIGINS))) return;
  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["dot.js"] });
  } catch { /* a page this extension may not touch */ }
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && ("cfg" in changes || "snoozeUntil" in changes)) schedule();
});

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  if (!msg || msg.target === "offscreen") return false;
  const jobs = {
    "blink-now": () => deliver("blink", { manual: true }),
    snooze: () => chrome.storage.local.set(
      { snoozeUntil: Date.now() + SNOOZE_MINUTES * 60000 }),
    resume: () => chrome.storage.local.remove("snoozeUntil"),
    chime: () => chime(msg.volume),
  };
  const job = jobs[msg.type];
  if (!job) return false;
  job().then((result) => reply({ result }), (e) => reply({ error: String(e) }));
  return true;                       // the reply comes later
});

chrome.runtime.onStartup.addListener(async () => {
  await chrome.storage.session.set({ startedAt: Date.now() });
  await schedule();
});

chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  await chrome.storage.session.set({ startedAt: Date.now() });
  await schedule();
  // The welcome is where the on-page cue is switched on, so a first install
  // opens it; an update does not.
  if (reason === "install") await chrome.tabs.create({ url: "options.html#welcome" });
});

// Every time the worker starts: make sure the alarms exist. Cheap, and it
// is what keeps a disabled-then-enabled extension from staying silent.
(async () => {
  if (!(await sessionValue("startedAt", 0))) {
    await chrome.storage.session.set({ startedAt: Date.now() });
  }
  await schedule();
})();

// For the end-to-end test, which drives the worker over the debugger.
globalThis.__blinkReminder = {
  deliver, schedule, checkAsks: async () => checkAsks(await getCfg()),
};
