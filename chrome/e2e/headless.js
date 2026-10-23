// The extension in a real Chrome, headless, end to end.
//
//     node chrome/e2e/headless.js [path-to-chrome] [screenshot-folder]
//
// Headless, with a throwaway profile and audio muted: nothing appears on
// screen, nothing touches your own Chrome profile, nothing makes a sound.
// Notifications are never triggered here -- on Windows they would be real
// toasts -- so only the on-page path is driven.
//
// The test copy is granted site access in its manifest, because the real one
// asks for it with a click, which a test cannot make.

import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { cpSync, mkdtempSync, readFileSync, writeFileSync, rmSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
// BLINK_EXT_SRC=dist-chrome/unpacked tests the package exactly as built.
const SRC = resolve(process.env.BLINK_EXT_SRC || resolve(HERE, ".."));
const CHROME = process.argv[2] ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";
const SHOTS = process.argv[3] || null;

const failures = [];
function check(what, ok, detail = "") {
  console.log(`  ${ok ? "ok  " : "FAIL"}  ${what}${detail ? `  (${detail})` : ""}`);
  if (!ok) failures.push(what);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const STUB_NOTIFICATIONS = `globalThis.__notified = [];
  chrome.notifications.create = async (id, opts) => { __notified.push({ id, ...opts }); return id; };
  chrome.notifications.clear = async () => true; 1`;

// -- a copy of the extension, with site access granted up front --------------
const work = mkdtempSync(join(tmpdir(), "blink-ext-e2e-"));
// What Chrome would load: no tests, no tooling, and no __pycache__, whose
// leading underscore Chrome refuses outright.
function copyExtension(dest) {
  cpSync(SRC, dest, { recursive: true,
    filter: (p) => !/[\\/](e2e|test|node_modules|__pycache__)([\\/]|$)/.test(p) });
  return dest;
}
const ext = copyExtension(join(work, "ext"));
const manifest = JSON.parse(readFileSync(join(ext, "manifest.json"), "utf8"));
manifest.host_permissions = ["http://*/*", "https://*/*"];
writeFileSync(join(ext, "manifest.json"), JSON.stringify(manifest, null, 2));

// -- a page to draw on --------------------------------------------------------
const server = createServer((req, res) => {
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  res.end(`<!doctype html><title>page</title>
    <style>body{font:16px sans-serif;margin:40px;background:#fff}
    [popover]{background:red!important} div{z-index:99999;position:relative}</style>
    <h1>An ordinary page</h1><p>With some text, and a hostile stylesheet.</p>
    <input id="typing" value="typing here">`);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const PAGE = `http://127.0.0.1:${server.address().port}/`;

// -- Chrome, over the DevTools pipe -------------------------------------------
const chrome = spawn(CHROME, [
  "--headless=new", `--user-data-dir=${join(work, "profile")}`,
  "--remote-debugging-pipe", "--enable-unsafe-extension-debugging",
  "--no-first-run", "--no-default-browser-check", "--mute-audio",
  "--window-size=1280,800", "about:blank",
], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });
const toChrome = chrome.stdio[3], fromChrome = chrome.stdio[4];

let nextId = 1;
const pending = new Map();
const events = [];
let buffer = "";
fromChrome.on("data", (chunk) => {
  buffer += chunk.toString("utf8");
  let end;
  while ((end = buffer.indexOf("\0")) >= 0) {
    const msg = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    if (msg.id && pending.has(msg.id)) {
      const { ok, fail } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? fail(new Error(JSON.stringify(msg.error))) : ok(msg.result);
    } else if (msg.method) {
      events.push(msg);
    }
  }
});

function send(method, params = {}, sessionId) {
  const id = nextId++;
  toChrome.write(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }) + "\0");
  return new Promise((ok, fail) => {
    pending.set(id, { ok, fail });
    setTimeout(() => { if (pending.delete(id)) fail(new Error(`timeout: ${method}`)); }, 15000);
  });
}

async function evaluate(sessionId, expression, contextId) {
  const r = await send("Runtime.evaluate",
    { expression, awaitPromise: true, returnByValue: true,
      ...(contextId ? { contextId } : {}) }, sessionId);
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}

async function attach(targetId) {
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Runtime.enable", {}, sessionId);
  return sessionId;
}

async function shot(sessionId, name) {
  if (!SHOTS) return;
  mkdirSync(SHOTS, { recursive: true });
  const { data } = await send("Page.captureScreenshot", { format: "png" }, sessionId);
  writeFileSync(join(SHOTS, `${name}.png`), Buffer.from(data, "base64"));
}

async function openTab(url) {
  const { targetId } = await send("Target.createTarget", { url });
  const sessionId = await attach(targetId);
  await send("Page.enable", {}, sessionId);
  await sleep(800);
  return { targetId, sessionId };
}

try {
  await send("Browser.getVersion").then((v) => console.log(v.product));
  const { id } = await send("Extensions.loadUnpacked", { path: ext });
  check("the extension loads", !!id, id);
  await sleep(1500);

  let targets = [];
  for (let i = 0; i < 20; i++) {
    targets = (await send("Target.getTargets")).targetInfos;
    if (targets.some((t) => t.url.includes(`${id}/options.html`))) break;
    await sleep(250);
  }
  const sw = targets.find((t) => t.type === "service_worker" && t.url.includes(id));
  check("its service worker starts", !!sw);
  const swS = await attach(sw.targetId);

  const welcome = targets.find((t) => t.url.includes(`${id}/options.html#welcome`));
  check("installing opens the welcome page", !!welcome,
        welcome ? "" : targets.map((t) => t.type + " " + t.url).join(", "));
  // Headless Chrome never sees a person, so it reports "idle"; the timed
  // paths below would all stop at "away". Tell the worker someone is here.
  await evaluate(swS, "chrome.idle.queryState = async () => 'active', 1");
  // Never a real notification: on Windows it would be a toast on the screen
  // of whoever is running this. Recorded instead, for the checks below.
  await evaluate(swS, STUB_NOTIFICATIONS);

  const alarms = await evaluate(swS, "chrome.alarms.getAll().then(a => a.map(x => x.name).sort())");
  check("blink, break and tick alarms are set", JSON.stringify(alarms) === '["blink","break","tick"]',
        JSON.stringify(alarms));
  const badge = await evaluate(swS, "chrome.action.getBadgeText({})");
  check("the badge counts down to the break", /^\d+$/.test(badge) && +badge <= 30, badge);

  // -- the cue on a page ------------------------------------------------------
  const page = await openTab(PAGE);
  await send("Target.activateTarget", { targetId: page.targetId });
  await evaluate(page.sessionId, "document.getElementById('typing').focus(), 1");
  const focusedWin = await evaluate(swS,
    "chrome.windows.getLastFocused().then(w => w.focused)");
  console.log(`  (headless reports the window focused: ${focusedWin})`);

  const result = await evaluate(swS, "__blinkReminder.deliver('blink', { manual: true })");
  check("Blink now draws on the page", result === "page", result);
  await sleep(250);
  const seen = await evaluate(page.sessionId, `(() => {
    const host = document.querySelector('blink-reminder-cue');
    if (!host) return null;
    const cs = getComputedStyle(host);
    return { bg: cs.backgroundColor, focus: document.activeElement.id };
  })()`);
  // The fade happens inside a closed shadow root, so it is read from the
  // extension's own isolated world, where cue.js keeps a way to look.
  const iso = events.filter((e) => e.method === "Runtime.executionContextCreated" &&
    e.sessionId === page.sessionId && e.params.context.auxData?.type === "isolated").pop();
  const st = iso && await evaluate(page.sessionId, "globalThis.__blinkReminderCue.state()",
                                   iso.params.context.id);
  // Sampled rather than caught at one moment: the cue fades in, holds and
  // fades out, and how long deliver() took to return (it may have had to
  // start an offscreen document for the chime) decides where in that we
  // would land. The peak is what the setting promises.
  let peak = st?.opacity ?? 0;
  for (let i = 0; i < 12 && iso; i++) {
    peak = Math.max(peak, await evaluate(page.sessionId,
      "globalThis.__blinkReminderCue.state()?.opacity ?? 0", iso.params.context.id));
    await sleep(90);
  }
  check("the cue is on the page", !!seen && !!st);
  check("it is in the top layer", st?.open === true);
  check("it reaches the strength it was set to", Math.abs(peak - 0.345) < 0.02,
        String(peak));
  check("clicks pass through it", st?.events === "none");
  check("the page's own [popover] style does not reach it",
        seen?.bg === "rgba(0, 0, 0, 0)", seen?.bg);
  check("focus stays where the user left it", seen?.focus === "typing", seen?.focus);
  await shot(page.sessionId, "page-blink-dot");
  await sleep(3000);
  const gone = await evaluate(page.sessionId, "document.querySelector('blink-reminder-cue') === null");
  check("it removes itself when done", gone);

  // A break, quietly (sound off), in its default dim style.
  await evaluate(swS, `chrome.storage.local.get('cfg').then(({cfg}) =>
    chrome.storage.local.set({ cfg: { ...(cfg || {}), brk: { style: 'dim', sound: false } } }))`);
  await sleep(300);
  const brk = await evaluate(swS, "__blinkReminder.deliver('break', { manual: true })");
  check("a break dims the page", brk === "page", brk);
  await sleep(1500);
  await shot(page.sessionId, "page-break-dim");
  const quiet = await evaluate(swS, "__blinkReminder.deliver('blink')");
  check("a timed blink waits while the break is on screen", quiet === "break showing", quiet);

  // -- the tutorial: the first reminders carry the instruction ---------------
  await evaluate(swS, "chrome.storage.local.remove('tutorial')");
  // The break just shown left the blink quiet for its duration; the lesson
  // is not about that rule, so clear it rather than waiting it out.
  await evaluate(swS, "chrome.storage.session.remove('quietUntil')");
  await evaluate(swS, "__notified.length = 0, 1");
  for (let n = 1; n <= 3; n++) {
    const kind = await evaluate(swS, "__blinkReminder.deliver('blink')");
    await sleep(300);
    const seen = iso && await evaluate(page.sessionId,
      "globalThis.__blinkReminderCue.state()?.caption ?? null",
      iso.params.context.id);
    const taught = n <= 2;
    check(`reminder ${n} ${taught ? "carries" : "does not carry"} the instruction`,
          (seen === "Close\u2026\nsqueeze\u2026\nopen") === taught,
          `${kind}, caption=${JSON.stringify(seen)}`);
    if (n === 2) await shot(page.sessionId, "page-taught");
    await sleep(3200);
  }
  const asked = await evaluate(swS, "__notified.at(-1)");
  check("the question follows the last taught reminder",
        asked?.id === "question" && asked?.buttons?.length === 2, asked?.id);
  check("... and is owed until it is put away",
        (await evaluate(swS, "chrome.storage.local.get('tutorial')")).tutorial?.question,
        "pending");

  // The question page: four buttons that lead to a control, and Got it.
  const qt = await openTab(`chrome-extension://${id}/options.html#question`);
  await sleep(600);
  const buttons = await evaluate(qt.sessionId,
    "[...document.querySelectorAll('#question-buttons button')].map(b => b.textContent)");
  check("the question page offers the four settings and Got it",
        buttons.length === 5 && buttons[4] === "Got it", JSON.stringify(buttons));
  await evaluate(qt.sessionId,
    "document.querySelector('#question-buttons button').click(), 1");
  await sleep(900);
  check("a button rings the control it names",
        await evaluate(qt.sessionId,
          "!!document.querySelector('#blink-card [data-point=\"strength\"].ring')"));
  await shot(qt.sessionId, "question");
  await evaluate(qt.sessionId,
    "document.querySelectorAll('#question-buttons button')[4].click(), 1");
  await sleep(600);
  check("Got it puts the question away for good",
        (await evaluate(swS, "chrome.storage.local.get('tutorial')")).tutorial?.question,
        "done");
  await send("Target.closeTarget", { targetId: qt.targetId });

  // -- the corner dot: opt-in, and gone again the moment it is switched off ---
  const setDot = (on) => evaluate(swS, `chrome.storage.local.get('cfg').then(({cfg}) =>
    chrome.storage.local.set({ cfg: { ...(cfg || {}), pageDot: ${on} } }))`);
  await setDot(true);
  await sleep(1500);
  const dot = await evaluate(page.sessionId, `(() => {
    const d = document.querySelector('blink-reminder-dot');
    if (!d) return null;
    const cs = getComputedStyle(d);
    return { events: cs.pointerEvents, position: cs.position, width: cs.width,
             bg: cs.backgroundColor };
  })()`);
  check("the opt-in corner dot appears", !!dot, JSON.stringify(dot));
  check("... click-through, fixed, and in the blink's colour",
        dot?.events === "none" && dot?.position === "fixed"
        && dot?.bg === "rgb(189, 228, 1)", JSON.stringify(dot));
  await shot(page.sessionId, "page-dot");
  // A page opened AFTER it was switched on: the registered content script,
  // not the one-off injection into tabs that were already open.
  const fresh = await openTab(PAGE);
  await sleep(900);
  check("... and on a page opened afterwards",
        await evaluate(fresh.sessionId,
          "document.querySelector('blink-reminder-dot') !== null"),
        JSON.stringify(await evaluate(swS,
          "chrome.scripting.getRegisteredContentScripts().then(r => r.map(x => x.id))")));
  await send("Target.closeTarget", { targetId: fresh.targetId });
  await setDot(false);
  await sleep(1500);
  check("... and is removed from an open page when switched off",
        await evaluate(page.sessionId,
          "document.querySelector('blink-reminder-dot') === null"));

  // -- the extension's own pages, light and dark, in a few languages -----------
  for (const [lang, scheme] of [["en", "light"], ["en", "dark"], ["de", "dark"],
                                ["ar", "light"], ["zh-Hant", "dark"]]) {
    await evaluate(swS, `chrome.storage.local.get('cfg').then(({cfg}) =>
      chrome.storage.local.set({ cfg: { ...(cfg || {}), language: '${lang}' } }))`);
    for (const [file, w, h] of [["options.html#welcome", 1100, 1500], ["popup.html", 320, 420]]) {
      const tab = await openTab(`chrome-extension://${id}/${file}`);
      await send("Emulation.setEmulatedMedia", { features: [
        { name: "prefers-color-scheme", value: scheme }] }, tab.sessionId);
      await send("Emulation.setDeviceMetricsOverride",
        { width: w, height: h, deviceScaleFactor: 1, mobile: false }, tab.sessionId);
      await sleep(500);
      const info = await evaluate(tab.sessionId, `({ dir: document.dir, lang: document.documentElement.lang,
        empty: [...document.querySelectorAll('[data-t]')].filter(e => !e.textContent.trim()).length,
        height: document.documentElement.scrollHeight })`);
      check(`${file.split(".")[0]} in ${lang}/${scheme}: every label filled`, info.empty === 0,
            `lang=${info.lang} dir=${info.dir}`);
      await shot(tab.sessionId, `${file.split(".")[0]}-${lang}-${scheme}`);
      await send("Target.closeTarget", { targetId: tab.targetId });
    }
  }

  // -- every control says what it is ----------------------------------------
  // A screen reader landing on the Sound dropdown or the Volume slider used
  // to hear "combo box" and "slider" with no name attached, because the row
  // caption was a plain <span> sitting beside the control rather than a
  // label bound to it.
  {
    const tab = await openTab(`chrome-extension://${id}/options.html`);
    await sleep(700);
    const unnamed = await evaluate(tab.sessionId, `(() => {
      const named = (e) => {
        if (e.labels && [...e.labels].some((l) => l.textContent.trim())) return true;
        if ((e.getAttribute('aria-label') || '').trim()) return true;
        const by = e.getAttribute('aria-labelledby');
        const src = by && document.getElementById(by);
        return !!(src && src.textContent.trim());
      };
      const bad = [];
      for (const e of document.querySelectorAll('input, select')) {
        if (e.type === 'hidden' || e.closest('[hidden]')) continue;
        if (!named(e)) bad.push(e.id || e.type || e.tagName);
      }
      for (const g of document.querySelectorAll('.segmented, #blink-interval')) {
        if (g.closest('[hidden]')) continue;
        if (g.getAttribute('role') !== 'group') {
          bad.push('role:' + (g.id || g.className));
        } else if (!named(g) && !g.parentElement.closest('[role=group]')) {
          // A group nested in a named group reads as its options.
          bad.push('group:' + (g.id || g.className));
        }
      }
      return bad;
    })()`);
    check("every control on the settings page says what it is",
          unnamed.length === 0, unnamed.join(", ") || "all named");
    await send("Target.closeTarget", { targetId: tab.targetId });
  }

  // -- as shipped: no site access until someone switches it on -------------
  const shipped = copyExtension(join(work, "shipped"));
  const { id: id2 } = await send("Extensions.loadUnpacked", { path: shipped });
  let sw2;
  for (let i = 0; i < 20 && !sw2; i++) {
    await sleep(250);
    sw2 = (await send("Target.getTargets")).targetInfos.find(
      (t) => t.type === "service_worker" && t.url.includes(id2));
  }
  const sw2S = await attach(sw2.targetId);
  await evaluate(sw2S, "chrome.idle.queryState = async () => 'active', 1");
  await evaluate(sw2S, STUB_NOTIFICATIONS);
  check("as shipped, it has no access to pages",
        (await evaluate(sw2S, `chrome.permissions.contains(${JSON.stringify({ origins: ["https://*/*"] })})`)) === false);
  const viaToast = await evaluate(sw2S, "__blinkReminder.deliver('blink', { manual: true })");
  const toast = await evaluate(sw2S, "__notified.at(-1)");
  check("without it, Blink now still shows something", viaToast === "notification", viaToast);
  check("... carrying the instruction", toast?.message === "Close… squeeze… open",
        JSON.stringify(toast?.message));
  // Silence follows the reminder's own sound setting, whatever that is set to.
  check("... and sounding only if that reminder is set to",
        toast?.silent === false, String(toast?.silent));
  await evaluate(sw2S, `chrome.storage.local.get('cfg').then(({cfg}) =>
    chrome.storage.local.set({ cfg: { ...(cfg || {}), blink: { sound: false } } }))`);
  await sleep(300);
  await evaluate(sw2S, "__blinkReminder.deliver('blink', { manual: true })");
  check("... silent when it is not",
        (await evaluate(sw2S, "__notified.at(-1)"))?.silent === true);
  const nothingOnPage = await evaluate(page.sessionId,
    "document.querySelector('blink-reminder-cue') === null");
  check("... and nothing is drawn on the page", nothingOnPage);

  // A TIMED blink, though, is never turned into a toast: it would be one a
  // minute. The user is told once that it has nowhere to draw.
  await evaluate(sw2S, "__notified.length = 0, 1");
  const timed = await evaluate(sw2S, "__blinkReminder.deliver('blink')");
  check("a timed blink is not turned into a notification",
        timed === "nowhere to draw", timed);
  const warned = await evaluate(sw2S, "__notified.at(-1)");
  check("... and says once that it has nowhere to draw",
        warned?.id === "access" && warned?.buttons?.length === 1, warned?.id);
  await evaluate(sw2S, "__blinkReminder.deliver('blink')");
  await evaluate(sw2S, "__blinkReminder.deliver('blink')");
  check("... once, not on every reminder",
        await evaluate(sw2S, "__notified.length"), 1);

  // ... and the toolbar says so for as long as it is true, which one
  // notification cannot. Running with nowhere to draw used to look exactly
  // like running.
  const blind = await evaluate(sw2S,
    "chrome.action.getBadgeText({}).then(text => chrome.action.getTitle({})" +
    ".then(title => ({ text, title })))");
  check("the toolbar shows that it has nowhere to draw",
        blind?.text === "!", JSON.stringify(blind?.text));
  check("... and its tooltip says so in words",
        /access/i.test(blind?.title || ""), blind?.title);

  // Twelve days of use, long since the browser started: the coffee ask.
  await evaluate(sw2S, `Promise.all([
    chrome.storage.local.set({ asks: { days_used: 12, last_counted: "${new Date().toISOString().slice(0, 10)}",
                                       shown: [], opted_out: false, last_ask: "" } }),
    chrome.storage.session.set({ startedAt: 1 })])`);
  await evaluate(sw2S, "__blinkReminder.checkAsks()");
  const ask = await evaluate(sw2S, "__notified.at(-1)");
  check("on the twelfth day of use, the coffee ask appears",
        ask?.id === "ask-donate" && ask?.buttons?.length === 2 && ask?.requireInteraction === true,
        ask?.id);
  await evaluate(sw2S, "__blinkReminder.checkAsks()");
  check("... once, not every minute", (await evaluate(sw2S, "__notified.length")) === 2);

  for (const [file, w, h] of [["options.html#welcome", 1100, 900], ["popup.html", 320, 460]]) {
    const tab = await openTab(`chrome-extension://${id2}/${file}`);
    await send("Emulation.setDeviceMetricsOverride",
      { width: w, height: h, deviceScaleFactor: 1, mobile: false }, tab.sessionId);
    await sleep(500);
    const offered = await evaluate(tab.sessionId, file.startsWith("popup")
      ? "!document.getElementById('page-cue').hidden"
      : "!document.getElementById('welcome-grant-box').hidden");
    check(`${file.split(".")[0]} offers to show the cue on pages`, offered);
    await shot(tab.sessionId, `shipped-${file.split(".")[0]}`);
    await send("Target.closeTarget", { targetId: tab.targetId });
  }

  const errors = events.filter((e) => e.method === "Runtime.exceptionThrown");
  const cmds = await evaluate(swS,
    "chrome.commands.getAll().then(c => c.map(x => x.name).sort())");
  check("keyboard shortcuts are registered",
        Array.isArray(cmds) && cmds.includes("snooze") && cmds.includes("blink-now"),
        JSON.stringify(cmds));

  check("no uncaught errors anywhere", errors.length === 0,
        errors.map((e) => e.params.exceptionDetails.exception?.description?.split("\n")[0]).join("; "));
} catch (e) {
  check("the run completed", false, e.message);
} finally {
  try { await send("Browser.close"); } catch { /* already gone */ }
  chrome.kill();
  server.close();
  await sleep(500);
  try { rmSync(work, { recursive: true, force: true }); } catch { /* Chrome may hold a file */ }
}

console.log(failures.length ? `\n${failures.length} FAILURE(S)` : "\nall checks passed");
process.exit(failures.length ? 1 : 0);
