# Localisation plan

How this app goes from two languages to ten or more — the model, the evidence
behind it, and the order to do things in.

Written September 2026, when Traditional Chinese shipped in 1.1.4.0.

---

## The model, in three lines

**One product. One package. Many listings.**

That shape does not change between two languages and twenty. Nothing in the
build, the upload or the certification is per-language.

| | Decision | Where it lives |
| --- | --- | --- |
| 1 | What the app speaks | The `STRINGS` table in the source |
| 2 | How a user gets their language | Automatically, from Windows. Never a prompt |
| 3 | How a user overrides it | One control, showing one language. The rest behind a click |
| 4 | What the Store advertises | `<Resource Language="…"/>` in the manifest — **must equal (1)** |
| 5 | What the Store page says | Store listings, one per language — **independent of everything above** |

Rows 1 and 4 must match, or the Store advertises a language the app does not
speak. Row 5 is free: you can list in a language before translating the app
(a cheap market test), or translate without listing.

---

## Why everything ships in one package

The only argument for choosing a language at install time is download size.
Measured, that argument does not exist here:

| | |
| --- | --- |
| MSIX 1.1.3.0, English only | 13,443,854 bytes |
| MSIX 1.1.4.0, **+ Traditional Chinese** | 13,451,622 bytes |
| Difference | **+7,768 bytes** |

And that 7.8 KB also paid for the language picker, the CJK font stacks, four
themes instead of two, and the text-width change. The translated text itself
is 652 bytes deflated, so **ten languages is about 6.4 KB — 0.05% of the
package.**

For scale, `unicodedata.pyd` — one support DLL, pulled in *to* size Chinese
text correctly — is 712 KB. **One DLL is 109× ten languages of text.**

### The alternatives, and why they lose

| Model | How it works | Verdict |
| --- | --- | --- |
| **Runtime selection** | One package, all languages, picked from the OS language | **Chosen.** Best UX, least work, only one the Store supports |
| Resource packages | `.msixbundle` with a per-language sub-package; the Store ships only what a machine needs | Store-native, but needs Windows `.pri` resources. A PyInstaller app's strings are code, not resources, so it cannot participate — and it would save 6 KB |
| Install-time choice | An installer asks; one language lands on disk | **Impossible in the Store** — MSIX installs silently, there is no installer UI. Also locks the user to a dialog they clicked through |
| A product per language | Ten Store entries | Resets ratings, reviews and ranking to zero ten times; ten submissions per update |

---

## The real constraint: layout, not size

Measured with plausible translations of the 41 tightest slots, in the real
fonts at the real sizes:

| Language | Average width vs English | Slots that overflow |
| --- | --- | --- |
| 繁體中文 (shipped) | 73% | 0 of 41 |
| 日本語 | 83% | 1 |
| Deutsch | 117% | 9 |
| Français | 120% | 8 |
| Русский | 121% | 8 |

CJK is free. European languages are not — but **it is nearly the same slots
every time.** Twelve distinct ones across the three languages, 8–9 in each:

- Footer buttons: **Cancel**, **Save**, **Preview blink**, **Preview break**
- **Test** (sound), **Change…** (colour)
- **Volume** — the label beside the slider, only 60px
- **Word to show** — the label before the entry
- **Startup: turned off in Task Manager** — already tight in English
- **Buy me a coffee** — the notice button
- The notice's card row, *"Right-click the tray icon…"*
- **Got it**

Widen these once and every European language fits. Most are free: the footer
has ~160px of unused space between the preview pair and Cancel/Save. Two need
rearranging — Volume wants its label above the slider rather than beside it,
and the Startup button needs shorter wording per language.

**Do this before translating, not after.** Otherwise each new language
rediscovers the same twelve slots, and fixing them means revisiting every
translation already paid for.

---

## Rule out now

- **Right-to-left: no.** Arabic, Hebrew, Persian, Urdu. The panel is built
  with `place()` and hard-coded x-from-the-left; RTL means mirroring every
  coordinate. That is a layout rewrite, not a translation.
- **Plurals.** `every %d minutes` has two forms in English, three in Russian
  and Polish. The table has two slots, so for those languages translate both
  to one invariant phrasing. If that reads badly in a language you care
  about, that single string earns a per-language callable. Nothing else does.
- **Fonts.** CJK is handled. Cyrillic, Greek, Polish, Czech, Turkish and
  Vietnamese are already covered by Segoe UI Variable. Thai, Hindi and Khmer
  would each need their own stack and a line-height check.

---

## The steps

### Phase 0 — code, once, before any translating

1. **Widen the twelve tight slots** (see above).
2. **Replace the language picker.** Today it is a two-segment control showing
   both languages — fine at two, indefensible at ten (152px ÷ 10 = 15px a
   segment). Replace with a single button showing the current language,
   opening a short list. Same shape as the Colour row: shows current, click
   to change. Not a `ttk.Combobox` — the panel deliberately has none, because
   its popdown cannot be themed.
3. **Move `STRINGS` to its own module.** Ten languages is ~900 lines of data
   and does not belong inside the GUI. Keep it a plain Python module so
   PyInstaller picks it up as a normal import — no data files, no
   `sys._MEIPASS`, nothing that can go missing.
4. **Make the manifest generate its language list from the table**, so (1)
   and (4) above cannot drift.
5. **Commit the checks as tests, in CI.** Every `T()` key exists, every
   user-facing literal is wrapped, every string fits its slot with a pixel
   budget. This is what makes language ten as safe as language two.

Then **freeze the English wording.** From here every new string costs ten
translations.

### Phase 1 — choose the languages

6. **Read Analytics → Acquisitions by market.** Translate where installs
   already come from, not where they might.
7. Optionally **test a market with a listing only** first — no build, no
   certification, and it answers the question cheaply.

Suggested order, subject to (6):

- **Free today, no layout risk:** zh-Hans, ja, ko
- **After Phase 0:** de, fr, es, pt-BR, it, nl
- **After Phase 0 + plural wording:** ru, pl, tr, vi, id

### Phase 2 — per language

8. **Translate the app** — one table of ~75 strings, then run the checks.
   Minutes.
9. **Write the listing copy** — short description, description, features
   (up to 20), 7 search terms. Several hours each.

Step 9 is the real cost. Step 8 is nearly free.

### Phase 3 — Partner Center, once for all of them

10. **Upload the one `.msix`.** "Languages supported in packages" fills itself
    in from the manifest. Nothing to type.
11. **Add the listing languages** — Store listings → Manage additional
    languages.
12. **Fill each listing.** Look first for **import/export of Store listings**
    (a `.csv` in a `.zip`): fill every language offline, upload once, instead
    of nine web forms.
13. **Reserve localised product names** if you want the Store *page* title in
    each language — Product name on each listing is a dropdown fed by your
    reserved names. Optional.
14. **Submit.** One package, one certification, all languages live together.

### Phase 4 — from then on

- Every release: **one `.msix`, one submission, one certification.** Listings
  are touched only when the copy changes.
- Adding language eleven: **one string table, one listing.** No new package,
  nothing structural.

Only one ordering constraint in the whole plan: **Phase 0 before Phase 2.**

---

## Store notes worth not rediscovering

- **Screenshots and the trailer fall back** to the default language when a
  locale has none. Ten sets are not required.
- **Search terms are per-language, 7 each.** Ten languages is 70 keyword
  slots against 7 today, in far less competitive fields. This is the growth
  lever, more than the translated UI is.
- **"Chinese (Traditional)" (`zh-Hant`), not "Chinese (Taiwan)" (`zh-TW`).**
  The manifest declares `zh-Hant`, and it covers Taiwan, Hong Kong and Macau.
  `zh-TW` is Taiwan only — a second listing to maintain for no extra reach.
- **The Start-menu and tile name is a single string** from the manifest —
  English for everyone — unless a `.pri` file is added purely to localise it.
  The Store *page* title can differ per language. Normal trade-off.
- A listing language that the package does not declare is allowed, and shows
  as "Additional Store listing languages" rather than "Languages supported in
  packages". Fine as a market test; not fine as a permanent state.

---

## Where things stand

- **Shipped in 1.1.4.0:** English + 繁體中文. Manifest declares `en-gb` and
  `zh-Hant`. Listing copy drafted in `store/listing-zh-Hant.txt`.
- **Also drafted:** `store/listing-fr.txt` — French listing copy, app not yet
  translated.
- **Not started:** every item in Phase 0.
