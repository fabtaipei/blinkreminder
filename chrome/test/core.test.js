// The extension's rules, under Node: cd chrome && node --test test/
//
// The same promises the desktop's test_asks.py checks, ported with the code:
// a day of use counts once, an ask is late rather than lost, "Don't ask
// again" ends them all -- plus the things only the extension has to get
// right, like which pages it can draw on and which alarms are too stale.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
  DEFAULTS, MIN_INTERVAL, intervalUnit, intervalSeconds,
  SOUNDS, TEACH_COUNT, freshTutorial, loadTutorial, teachingDue, questionDue,
  teachingPulse, captionInk,
  normalize, limitFlashRate, pulseOf, pulseMs,
  msToNextBreak, isStale, drawable, resolveLanguage, freshAsks, loadAsks,
  countDay, dueAsk, todayIso, feelOf, FEELS, reviewUrl, onWindows,
} from "../core.js";
import { LANGUAGES, STRINGS } from "../strings.js";

const CODES = LANGUAGES.map(([, c]) => c);

test("defaults survive normalize unchanged", () => {
  assert.deepEqual(normalize(undefined), DEFAULTS);
  assert.deepEqual(normalize(DEFAULTS), DEFAULTS);
});

test("each damaged setting falls back on its own", () => {
  const got = normalize({
    enabled: "yes", blinkInterval: 45, breakMinutes: 30, language: "xx",
    blink: { opacity: 7, style: "spiral", colour: "red", hold: "500", dotPct: 50 },
  }, CODES);
  assert.equal(got.enabled, true);
  assert.equal(got.blinkInterval, 45, "any number of seconds, not a fixed step");
  assert.equal(got.breakMinutes, 30);
  assert.equal(got.language, "auto");
  assert.equal(got.blink.opacity, 1, "clamped, not discarded");
  assert.equal(got.blink.style, "dot");
  assert.equal(got.blink.colour, DEFAULTS.blink.colour);
  assert.equal(got.blink.hold, 500, "a numeric string is still a number");
  assert.equal(got.blink.dotPct, 50, "the good value next to bad ones is kept");
});

test("the interval is any number of seconds Chrome can keep", () => {
  assert.equal(intervalSeconds(45, 1), 45, "not rounded to a step");
  assert.equal(intervalSeconds(20, 1), MIN_INTERVAL, "under Chrome's floor");
  assert.equal(intervalSeconds(5, 60), 300, "minutes become seconds");
  assert.equal(intervalSeconds(9999, 60), 999 * 60, "clamped at the ceiling");
  assert.equal(intervalSeconds("x", 1), MIN_INTERVAL, "nonsense falls to the floor");
  assert.equal(normalize({ blinkInterval: 45 }).blinkInterval, 45);
  assert.equal(normalize({ blinkInterval: 5 }).blinkInterval, MIN_INTERVAL);
});

test("an interval is shown in the unit a person would say it in", () => {
  assert.equal(intervalUnit(45), 1);
  assert.equal(intervalUnit(90), 1, "ninety seconds, not 1.5 minutes");
  assert.equal(intervalUnit(120), 60);
  assert.equal(intervalUnit(150), 1, "two and a half minutes reads in seconds");
  assert.equal(intervalUnit(1200), 60);
});

test("a fast repeating pulse is slowed to three flashes a second at most", () => {
  const p = limitFlashRate({ fade: 0, hold: 50, gap: 0, blinks: 5 });
  assert.ok(2 * p.fade + p.hold + p.gap >= 350);
  const one = limitFlashRate({ fade: 0, hold: 50, gap: 0, blinks: 1 });
  assert.equal(one.gap, 0, "a single pulse cannot flash, so it is left alone");
});

test("the default word fills in only when none was typed", () => {
  assert.equal(pulseOf(DEFAULTS, "blink", "Blink").message, "Blink");
  const typed = normalize({ blink: { message: "Look up" } });
  assert.equal(pulseOf(typed, "blink", "Blink").message, "Look up");
  assert.equal(pulseMs({ fade: 500, hold: 500, blinks: 2, gap: 150 }), 3150);
});

test("breaks land on the wall clock", () => {
  const at = (h, m, s) => new Date(2026, 9, 21, h, m, s);
  assert.equal(msToNextBreak(30, at(10, 0, 0)), 30 * 60000);
  assert.equal(msToNextBreak(30, at(10, 29, 0)), 60000);
  assert.equal(msToNextBreak(30, at(10, 45, 30)), 14 * 60000 + 30000);
  assert.equal(msToNextBreak(20, at(23, 59, 0)), 60000, "midnight is a boundary");
});

test("an alarm fired late after sleep is stale", () => {
  assert.equal(isStale(1000, 5000, 20000), false);
  assert.equal(isStale(1000, 3600000, 20000), true);
});

test("the cue is drawn on web pages only", () => {
  assert.equal(drawable("https://example.com/a"), true);
  assert.equal(drawable("http://localhost:8000/"), true);
  for (const url of ["chrome://settings", "chrome-extension://x/options.html",
                     "file:///C:/a.pdf", undefined,
                     "https://chromewebstore.google.com/detail/x",
                     "https://microsoftedge.microsoft.com/addons/detail/x"]) {
    assert.equal(drawable(url), false, String(url));
  }
});

test("the browser's language resolves to one we speak", () => {
  assert.equal(resolveLanguage("en-GB", CODES), "en");
  assert.equal(resolveLanguage("zh-TW", CODES), "zh-Hant");
  assert.equal(resolveLanguage("zh-HK", CODES), "zh-Hant");
  assert.equal(resolveLanguage("zh-CN", CODES), "zh-Hans");
  assert.equal(resolveLanguage("zh", CODES), "zh-Hans");
  assert.equal(resolveLanguage("pt-BR", CODES), "pt");
  assert.equal(resolveLanguage("no", CODES), "nb");
  assert.equal(resolveLanguage("fil", CODES), "en");
  assert.equal(resolveLanguage("sw", CODES), "en", "unspoken falls back to English");
});

test("strings.js covers every language with the same keys", () => {
  const keys = Object.keys(STRINGS.fr).sort();
  assert.equal(Object.keys(STRINGS).length, CODES.length - 1, "all but English");
  for (const [code, table] of Object.entries(STRINGS)) {
    assert.deepEqual(Object.keys(table).sort(), keys, code);
  }
});

test("presets are recognised, hand-tuned timings are Custom", () => {
  assert.equal(feelOf({ ...DEFAULTS.blink, ...FEELS.Gentle }), "Gentle");
  assert.equal(feelOf(DEFAULTS.blink), "Custom");
});

test("rate goes to the store this copy came from", () => {
  assert.match(reviewUrl("abc", "Mozilla/5.0 Chrome/155.0"), /chromewebstore.*abc\/reviews/);
  assert.match(reviewUrl("abc", "Mozilla/5.0 Chrome/155.0 Edg/155.0"), /microsoftedge/);
  assert.equal(onWindows("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"), true);
  assert.equal(onWindows("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"), false);
});

// -- days of use and the asks: the desktop's rules, ported ------------------

test("a day counts once, however often the browser opens", () => {
  const st = freshAsks();
  assert.equal(countDay(st, "2026-10-01"), true);
  assert.equal(countDay(st, "2026-10-01"), false);
  assert.equal(countDay(st, "2026-10-04"), true, "three days asleep count one");
  assert.equal(st.days_used, 2);
});

test("a clock moved back never counts a day twice", () => {
  const st = freshAsks();
  countDay(st, "2026-10-05");
  assert.equal(countDay(st, "2026-10-04"), false);
  assert.equal(countDay(st, "2026-10-05"), false);
  assert.equal(st.days_used, 1);
});

test("a date once set far in the future is pulled back, not waited out", () => {
  const st = { ...freshAsks(), days_used: 3, last_counted: "2027-06-01" };
  assert.equal(countDay(st, "2026-10-05"), false);
  assert.equal(st.last_counted, "2026-10-05");
  assert.equal(countDay(st, "2026-10-06"), true);
});

test("an ask is due once its day is reached, and late rather than lost", () => {
  const st = { ...freshAsks(), days_used: 11 };
  assert.equal(dueAsk(st, "d"), null);
  st.days_used = 30;
  assert.deepEqual(dueAsk(st, "d"), [12, "donate"], "the earliest unshown first");
  st.shown.push(12);
  assert.deepEqual(dueAsk(st, "d"), [25, "review"]);
});

test("at most one ask a day", () => {
  const st = { ...freshAsks(), days_used: 30, shown: [12], last_ask: "d" };
  assert.equal(dueAsk(st, "d"), null);
  assert.deepEqual(dueAsk(st, "e"), [25, "review"]);
});

test("Don't ask again ends every ask, reviews included", () => {
  const st = { ...freshAsks(), days_used: 200, opted_out: true };
  assert.equal(dueAsk(st, "d"), null);
});

test("a kind that cannot be asked is skipped, not spent", () => {
  const st = { ...freshAsks(), days_used: 30 };
  assert.deepEqual(dueAsk(st, "d", (k) => k === "review"), [25, "review"]);
  assert.deepEqual(st.shown, []);
});

test("damaged ask state costs only the damaged field", () => {
  assert.deepEqual(loadAsks(null), freshAsks());
  const got = loadAsks({ days_used: -3, last_counted: "2026-10-01",
                         shown: [12, "25", true], opted_out: "yes" });
  assert.equal(got.days_used, 0);
  assert.equal(got.last_counted, "2026-10-01");
  assert.deepEqual(got.shown, [12]);
  assert.equal(got.opted_out, false);
});

test("today is local YYYY-MM-DD, which sorts as dates do", () => {
  assert.equal(todayIso(new Date(2026, 0, 5)), "2026-01-05");
});

// -- the tutorial ------------------------------------------------------------

test("the first few reminders are taught, then the question is owed", () => {
  const t = freshTutorial();
  for (let n = 1; n <= TEACH_COUNT; n++) {
    assert.equal(teachingDue(t), true, `reminder ${n}`);
    assert.equal(questionDue(t), false, "not while still teaching");
    t.taught += 1;
  }
  assert.equal(teachingDue(t), false);
  assert.equal(questionDue(t), true);
  t.question = "done";
  assert.equal(questionDue(t), false, "put away for good");
});

test("a taught pulse is the user's own reminder plus the instruction", () => {
  const plain = pulseOf(DEFAULTS, "blink", "Blink");
  const taught = teachingPulse(plain, "Close…\nsqueeze…\nopen", false);
  assert.equal(taught.caption, "Close…\nsqueeze…\nopen");
  for (const k of Object.keys(plain)) assert.deepEqual(taught[k], plain[k], k);
  assert.equal("caption" in plain, false, "the original is left alone");
});

test("the word style shows the instruction as its word, on one line", () => {
  const word = pulseOf({ ...DEFAULTS, blink: { ...DEFAULTS.blink, style: "text" } },
                       "blink", "Blink");
  const spaced = teachingPulse(word, "Close…\nsqueeze…\nopen", false);
  assert.equal("caption" in spaced, false);
  assert.equal(spaced.message, "Close… squeeze… open");
  const joined = teachingPulse(word, "閉上\n輕輕閉緊\n睜開", true);
  assert.equal(joined.message, "閉上輕輕閉緊睜開", "no spaces where none are written");
});

test("the instruction is readable on whatever colour the cue is", () => {
  assert.equal(captionInk("#bde401"), "#11161C", "dark ink on lime");
  assert.equal(captionInk("#12233f"), "#FFFFFF", "white on navy");
  assert.equal(captionInk("lime"), "#FFFFFF", "a colour that will not parse");
});

test("damaged tutorial state costs only the damaged field", () => {
  assert.deepEqual(loadTutorial(null), freshTutorial());
  const got = loadTutorial({ welcomed: "yes", taught: -2, question: "maybe" });
  assert.deepEqual(got, freshTutorial());
  assert.equal(loadTutorial({ welcomed: true, taught: "x" }).welcomed, true);
});

test("each reminder picks its own sound, from the four the desktop offers", () => {
  assert.deepEqual(SOUNDS, ["ding", "chord", "chime", "notify"]);
  assert.equal(normalize({ blink: { soundName: "chord" } }).blink.soundName, "chord");
  assert.equal(normalize({ blink: { soundName: "tuba" } }).blink.soundName,
               DEFAULTS.blink.soundName, "an unknown name falls back");
  const cfg = normalize({ blink: { soundName: "notify" }, brk: { soundName: "chime" } });
  assert.notEqual(cfg.blink.soundName, cfg.brk.soundName,
                  "the two reminders are independent");
  assert.equal(pulseOf(cfg, "blink", "Blink").soundName, "notify",
               "the pulse carries it to the player");
});

test("volume runs from 1% to 100%", () => {
  assert.equal(normalize({ blink: { volume: 0.01 } }).blink.volume, 0.01);
  assert.equal(normalize({ blink: { volume: 0.004 } }).blink.volume, 0.01, "clamped up");
  assert.equal(normalize({ blink: { volume: 3 } }).blink.volume, 1, "clamped down");
});

test("the shipped defaults are the ones the author settled on", () => {
  assert.equal(DEFAULTS.blinkInterval, 30);
  assert.equal(DEFAULTS.blink.fade, 250);
  assert.equal(DEFAULTS.blink.volume, 0.2);
  assert.equal(DEFAULTS.blink.sound, true);
  assert.equal(DEFAULTS.pageDot, true);
});
