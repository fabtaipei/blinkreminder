// The language in force, and T() to read a string in it.
//
// Not chrome.i18n: that follows the browser's language and nothing else,
// and Chrome has no Urdu at all. The desktop app lets people pick, so this
// does too -- strings.js carries every language, and "auto" means "the
// browser's language, if we speak it".

import { LANGUAGES, RTL, STRINGS } from "./strings.js";
import { resolveLanguage } from "./core.js";

export const CODES = LANGUAGES.map(([, code]) => code);
const NO_SPACES = ["zh-Hant", "zh-Hans", "ja"];
let lang = "en";

export function setLanguage(setting) {
  lang = setting && setting !== "auto" && CODES.includes(setting)
    ? setting
    : resolveLanguage(chrome.i18n.getUILanguage(), CODES);
  return lang;
}

export const language = () => lang;
export const isRtl = () => RTL.includes(lang);

export function T(key) {
  return (STRINGS[lang] && STRINGS[lang][key]) || key;
}

// The word each reminder shows if the user has not typed one.
export function defaultWord(kind) {
  return kind === "blink" ? T("Blink") : T("Look into the distance");
}

// "30 seconds" up to 90, whole minutes from 2.
export function intervalLabel(seconds) {
  return seconds < 120 ? `${seconds} ${T("seconds")}`
                       : `${seconds / 60} ${T("minutes")}`;
}

// The blink instruction on one line, for a notification.
export function captionLine() {
  return T("Close…\nsqueeze…\nopen").split("\n")
    .join(NO_SPACES.includes(lang) ? "" : " ");
}

// Fill every [data-t] element under `root` and set the page's direction.
export function localize(root = document) {
  for (const el of root.querySelectorAll("[data-t]")) {
    el.textContent = T(el.dataset.t);
  }
  document.documentElement.lang = lang;
  document.documentElement.dir = isRtl() ? "rtl" : "ltr";
}
