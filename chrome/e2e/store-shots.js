// Chrome Web Store screenshots, taken in a real Chrome at exactly 1280x800.
//
//     node chrome/e2e/store-shots.js [chrome.exe] [out-dir]
//
// Headless, with a throwaway profile, so nothing appears on screen and the
// developer's own Chrome is untouched. The copy it loads is granted site
// access in its manifest, because a screenshot cannot click Chrome's prompt.
//
// It shoots the product, not a mock-up: the real cue, over a real page, at
// the settings the extension actually ships with. These are the raw frames;
// store/make_chrome_assets.py lays them out and captions them.

import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { cpSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(HERE, "..");
const CHROME = process.argv[2] ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";
const OUT = process.argv[3] || resolve(SRC, "..", "store", "chrome");
const W = 1280, H = 800;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
mkdirSync(OUT, { recursive: true });

const work = mkdtempSync(join(tmpdir(), "blink-shots-"));
const ext = join(work, "ext");
cpSync(SRC, ext, { recursive: true,
  filter: (p) => !/[\\/](e2e|test|node_modules|__pycache__)([\\/]|$)/.test(p) });
const manifest = JSON.parse(readFileSync(join(ext, "manifest.json"), "utf8"));
manifest.host_permissions = ["http://*/*", "https://*/*"];
writeFileSync(join(ext, "manifest.json"), JSON.stringify(manifest, null, 2));

// A plain reading page. Nobody else's site, nobody else's branding: the
// screenshot has to show the cue, and a recognisable website in a store
// listing is someone else's trade mark.
const PAGE = `<!doctype html><meta charset="utf-8"><title>An article</title>
<style>
 /* Dark, because that is where the cue's own default strength reads as it
    really is. On a white page a 34% lime wash is honestly faint, and a
    listing image that has to be squinted at tells nobody anything. */
 :root { color-scheme: dark }
 body { margin: 0; background: #14171a; color: #c3ccd6;
        font: 16px/1.75 Georgia, "Times New Roman", serif; }
 header { border-bottom: 1px solid #262b31; padding: 14px 0;
          font: 600 13px/1 system-ui, sans-serif; color: #7d8794;
          letter-spacing: .14em; text-transform: uppercase; }
 main { max-width: 640px; margin: 0 auto; padding: 0 24px 60px; }
 h1 { font: 700 34px/1.25 system-ui, sans-serif; margin: 36px 0 6px;
      color: #e8eef5; }
 .by { color: #7d8794; font: 14px/1 system-ui, sans-serif; margin-bottom: 28px; }
 p { margin: 0 0 20px; }
</style>
<main>
 <header>Long read</header>
 <h1>The quiet hours of a working day</h1>
 <p class="by">Nine minutes to read</p>
 <p>Reading on a screen changes something small and easy to miss. The eyes
 settle, the lids move less, and the film of tears that keeps the surface
 comfortable is renewed more slowly than it is lost.</p>
 <p>None of this is dramatic. It is the accumulation that tells: an afternoon
 of documents, a long call, an evening of spreadsheets, and by the end of it a
 grittiness that sleep clears and the next morning restores.</p>
 <p>What helps is not effort but interruption of the mildest kind. A cue at
 the edge of attention, often enough to catch the habit before it settles,
 gentle enough that the sentence being written survives it.</p>
 <p>The eyelid closes in roughly a tenth of a second. Done fully, that is
 enough to spread the film evenly across the surface again, which is the whole
 of the mechanism and the whole of the advice.</p>
</main>`;

const server = createServer((req, res) => {
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  res.end(PAGE);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const URL_ = `http://127.0.0.1:${server.address().port}/`;

const chrome = spawn(CHROME, [
  "--headless=new", `--user-data-dir=${join(work, "profile")}`,
  "--remote-debugging-pipe", "--enable-unsafe-extension-debugging",
  "--no-first-run", "--no-default-browser-check", "--mute-audio",
  `--window-size=${W},${H}`, "about:blank",
], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"] });
const toChrome = chrome.stdio[3], fromChrome = chrome.stdio[4];

let nextId = 1;
const pending = new Map();
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
    }
  }
});
function send(method, params = {}, sessionId) {
  const id = nextId++;
  toChrome.write(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }) + "\0");
  return new Promise((ok, fail) => {
    pending.set(id, { ok, fail });
    setTimeout(() => { if (pending.delete(id)) fail(new Error(`timeout ${method}`)); }, 20000);
  });
}
async function evaluate(sessionId, expression) {
  const r = await send("Runtime.evaluate",
    { expression, awaitPromise: true, returnByValue: true }, sessionId);
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 300));
  return r.result.value;
}
async function openTab(url, width = W, height = H) {
  const { targetId } = await send("Target.createTarget", { url });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Runtime.enable", {}, sessionId);
  await send("Page.enable", {}, sessionId);
  await send("Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 1, mobile: false }, sessionId);
  await sleep(700);
  return { targetId, sessionId };
}
async function shot(sessionId, name) {
  const { data } = await send("Page.captureScreenshot",
    { format: "png", captureBeyondViewport: false }, sessionId);
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(data, "base64"));
  console.log(`  ${name}.png`);
}

try {
  const { id } = await send("Extensions.loadUnpacked", { path: ext });
  await sleep(1500);
  const sw = (await send("Target.getTargets")).targetInfos.find(
    (t) => t.type === "service_worker" && t.url.includes(id));
  const { sessionId: swS } = await send("Target.attachToTarget",
    { targetId: sw.targetId, flatten: true });
  await send("Runtime.enable", {}, swS);
  await evaluate(swS, "chrome.idle.queryState = async () => 'active', 1");

  const page = await openTab(URL_);
  await send("Target.activateTarget", { targetId: page.targetId });

  // 1. the blink cue, at the strength it ships with
  await evaluate(swS, "__blinkReminder.deliver('blink', { manual: true })");
  await sleep(700);
  await shot(page.sessionId, "1-blink-cue-raw");
  await sleep(3000);

  // 2. the break, which dims the whole page
  await evaluate(swS, "__blinkReminder.deliver('break', { manual: true })");
  await sleep(1400);
  await shot(page.sessionId, "2-break-raw");
  await sleep(4000);

  // 3. the corner dot, saying it is running
  await evaluate(swS, `chrome.storage.local.get('cfg').then(({cfg}) =>
    chrome.storage.local.set({ cfg: { ...(cfg || {}), pageDot: true } }))`);
  await sleep(1500);
  await shot(page.sessionId, "3-corner-dot-raw");

  // 4. the settings
  const opts = await openTab(`chrome-extension://${id}/options.html`);
  await sleep(900);
  await shot(opts.sessionId, "4-settings-raw");

  // 5. the pop-up, at its own size, for compositing
  const pop = await openTab(`chrome-extension://${id}/popup.html`, 320, 430);
  await sleep(700);
  await shot(pop.sessionId, "5-popup-raw");
} catch (e) {
  console.log("failed:", e.message);
} finally {
  try { await send("Browser.close"); } catch { /* gone */ }
  chrome.kill();
  server.close();
  await sleep(400);
  try { rmSync(work, { recursive: true, force: true }); } catch { /* held */ }
}
console.log(`\nwritten to ${OUT}`);
