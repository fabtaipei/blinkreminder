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

Done: zh-Hant, zh-Hans, fr, es, de, it.

Next candidates, and what each one actually costs:

| | Verdict |
| --- | --- |
| **日本語, 한국어** | Ready to go. CJK runs 75–85% of English, so no layout risk, and the font stacks are the same shape as Chinese's |
| **Português (pt-BR)** | Ready to go. Latin script, similar length to Spanish |
| **हिन्दी, বাংলা** | Done. Nirmala UI covers both, and Windows shapes them correctly through Tk — conjuncts form and vowel marks reorder |
| **العربية, اردو** | Done, with one caveat below |

### Right-to-left: what is true, and what I got wrong

An earlier version of this file said Arabic and Urdu were impossible. That
was an assumption, not a measurement, and measuring it proved it wrong.

**The text is correct.** Tk gets shaping and bidi from Windows: letters
join, forms change by position, and the run reads right to left. Measured,
a shaped Arabic word is 0.94 of the width of its letters laid out singly,
and Urdu 0.56 — there is no way to get those numbers without real shaping.

**One thing did need fixing.** A label is a left-to-right widget, so Tk
lays its text out with a left-to-right base paragraph direction, and that
misplaces any Latin run inside: `التشغيل مع Windows` rendered with Windows
at the front, which is a different sentence. `T()` now wraps RTL languages
in U+202B … U+202C to state the base direction. Two zero-width characters,
and it costs the other twelve languages nothing.

**What is still not done: the LAYOUT is not mirrored.** Labels sit on the
left of each row and controls on the right, as in every other language. A
fully localised Arabic build would flip that. It is a real compromise, and
it is a fair amount of work — every widget is placed at a hard-coded x from
the left edge — but it is a compromise about polish, not about legibility.
The panel is readable and usable as it stands.

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

- **1.1.7.0 speaks fourteen languages:** English, 繁體中文, 简体中文,
  Français, Español, Deutsch, Italiano, Português, 日本語, 한국어, हिन्दी,
  বাংলা, العربية, اردو. 975 translated strings.
- **Listing copy exists for six** (`store/listing-*.json`): zh-Hant,
  zh-Hans, fr, es, de, it. The seven added after them — pt, ja, ko, hi, bn,
  ar, ur — have the APP translated but no listing copy yet. That is the
  next piece of work, and it is the expensive half.
- **Only English and 繁體中文 are live on the Store** as of 1.1.5.0.
  Everything else needs its listing language added in Partner Center, then
  a fresh export, `fill_listing.py`, and an import.
- Thirteen non-English languages cost about **130 KB** in the package,
  which is the whole argument for one package restated with a bigger
  number.
- **Shipped in 1.1.4.0:** English + 繁體中文. Listing copy drafted in
  `store/listing-zh-Hant.txt`.
- **Phase 0: done in 1.1.5.0.** All twelve slots widened; the picker is now
  a one-language button with the list behind a click; the strings live in
  `blink_i18n.py`; the manifest generates its language list from that table;
  `test_i18n.py` enforces completeness, fit and manifest truth, and CI runs
  it before every build.
- **Also drafted:** `store/listing-fr.txt` — French listing copy, app not yet
  translated.
- **Next:** Phase 1. Nothing in Phase 2 is blocked.

### Adding a language, now that Phase 0 is done

1. Add `(label, code)` to `LANGUAGES` and a table to `STRINGS`, both in
   `blink_i18n.py`. Its own docstring is the checklist.
2. `py test_i18n.py`. It will name any string that is missing, orphaned, or
   too wide, and which control it is too wide for.
3. `py build_msix.py`. The manifest picks up the new language by itself.
4. Copy `store/listing-zh-Hant.json`, translate the values, and change
   `language`.
5. In Partner Center: add the listing language, **Export listing**, then

       py store\fill_listing.py <export>.csv store\listing-<code>.json

   and **Import listings → Import .csv**.

Nothing else changes — no new package, no second product, no re-architecture.

### Artwork for a new language is automatic

`fill_listing.py` copies every asset the base listing has, found from the
export's own `Type` column rather than from a list, and only into cells that
are empty — so artwork uploaded by hand for a language is never overwritten.

**This includes the 16:9 hero image, and that matters more than it looks.**
Without `PromoImage1920x1080` a trailer uploads, validates, and then simply
does not appear at the top of the listing. Partner Center says so on the
page: *"For trailers to appear at the top of your Store listing, you must
include a 16:9 'hero' promotional image."* It was left out of the first
Chinese listing by hand and cost an evening finding out why the trailer had
vanished.

`OverrideLogosForWin10` travels with the override logos rather than being
preserved, because it is the switch that decides whether they are used at
all: copying them into a language whose switch says False achieves nothing.
