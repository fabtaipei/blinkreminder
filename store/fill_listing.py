"""Write one or more languages into a Partner Center listings .csv.

    py store\\fill_listing.py <exported.csv> store\\listing-zh-Hant.json ...
        [--align-trailers] [--shots DIR] [--logos DIR] [--drop CODE]
        [--only-changed <the .csv last imported>]

Partner Center's "Export listing" (app overview page, Store listings section)
gives a UTF-8 .csv whose first four columns are Field, ID, Type and default,
followed by one column per language-locale code. This fills in a language
column from a .json file of the same copy, and writes <exported>-filled.csv
beside it, ready for "Import listings".

Why bother, for one language? Because there will be nine more, and the web
form is the same nineteen boxes every time. Also because the copy then lives
in the repo, reviewable and diffable, rather than only in a browser.

Three rules it keeps:

  * Field, ID and Type are never touched. Partner Center rejects the file if
    they change, and it does not say which cell was the problem.
  * A key that matches no row in the export is an ERROR, not a warning. The
    exact field names differ between product types and change over time, and
    a silently dropped Description is exactly the failure worth preventing.
  * Nothing is deleted. Rows this file says nothing about keep whatever the
    export had -- which is what leaves the screenshots and the trailer
    alone. Blanking a trailer row in the .csv deletes the file from Partner
    Center for good.

--only-changed makes the result small. Once the assets are in Partner
Center, a copy change touches four rows out of 429, and Microsoft's import
docs say an untouched row can simply be left out. Dropping the rest takes
the screenshot paths with it, so the import goes back to being a .csv
rather than a folder of images already uploaded: 42 MB becomes 18 KB.
"""

import csv
import io
import json
import os
import re
import sys

FIXED = ("field", "id", "type")

# What every new language inherits from the base listing unless its .json
# says otherwise. Driven by the Type column rather than by a list of field
# names: Partner Center marks an asset row "Relative path (or URL to file in
# Partner Center)", so "copy the assets" needs no list to keep in sync, and a
# slot Microsoft adds next year is covered the day it appears.
#
# This exists because of one that was missed by hand. The 16:9 hero image
# (PromoImage1920x1080) is not decoration: without it a trailer uploads,
# validates, and then does not appear at the top of the listing. Partner
# Center says so on the page; it is not the kind of thing to re-derive per
# language.
#
# `also` carries the non-asset rows that would be meaningless without the
# assets they govern -- OverrideLogosForWin10 is the switch that decides
# whether the override logos are used at all.
DEFAULT_COPY = {
    "column": "en-gb",
    "assets": True,
    "also": ["OverrideLogosForWin10"],
    "except": [],
}

ASSET_TYPE_HINT = "relative path"


def key(name):
    """Field names, reduced so "Short description" == "ShortDescription"."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# Field, ID and Type. Never a language, never written, and never matched:
# Indonesian's code is "id", which is exactly the ID column's heading, and
# a case-insensitive search over the whole header found it there and wrote
# an entire listing over thirty field IDs. The docs are explicit that those
# three columns must not change, and this is how they would have.
RESERVED_COLUMNS = 3


def column(header, code):
    """The index of a language column, however Partner Center cased it.

    The export writes the codes lower-case -- "zh-hant" -- while the manifest
    and everything else in this repo use "zh-Hant". Matching exactly would
    quietly add a SECOND column and leave the listing empty.

    The search starts past Field, ID and Type. "default" is still findable,
    since copying from it is a reasonable thing to ask for.
    """
    for i, name in enumerate(header):
        if i >= RESERVED_COLUMNS and (name or "").lower() == code.lower():
            return i
    return None


TRAILER_ASSETS = ("Trailer%d", "TrailerThumbnail%d", "TrailerClosedCaption%d",
                  "TrailerAudioDescription%d")


def align_all_trailers(rows, header, base="en-gb"):
    """Make every language's trailers exactly the base listing's.

    Slot by slot: where the base has trailer N, every language gets the
    same video, thumbnail, captions file and audio description, and keeps
    its own translated title; where the base has none, the language's
    trailer N is cleared, title and all.

    Before writing anything, lists every trailer that no listing will
    reference afterwards. Those are the files Partner Center deletes on
    import, permanently, and the reason this is a flag and not a default.
    """
    b = column(header, base)
    if b is None:
        sys.exit("--align-trailers needs a %r column" % base)
    by = {r[0]: r for r in rows[1:] if r}
    langs = [i for i in range(RESERVED_COLUMNS + 1, len(header)) if i != b]

    def refs():
        seen = set()
        for r in rows[1:]:
            if r and r[0].startswith("Trailer") and "Title" not in r[0]:
                seen.update(r[i] for i in range(RESERVED_COLUMNS + 1, len(r))
                            if r[i].strip())
        return seen

    before = refs()
    changed = 0
    for n in range(1, 16):
        if ("Trailer%d" % n) not in by:
            break
        base_has = bool(by["Trailer%d" % n][b].strip())
        for i in langs:
            for pat in TRAILER_ASSETS:
                r = by.get(pat % n)
                if r is not None and r[i] != r[b]:
                    r[i] = r[b]
                    changed += 1
            t = by.get("TrailerTitle%d" % n)
            if t is not None:
                if not base_has and t[i]:
                    t[i] = ""
                    changed += 1
                elif base_has and not t[i].strip():
                    t[i] = t[b]
                    changed += 1
    top = by.get("TrailerToPlayAtTopOfListing")
    if top is not None:
        for i in langs:
            if top[i] != top[b]:
                top[i] = top[b]
                changed += 1

    gone = sorted(before - refs())
    print("  --align-trailers: %d cell(s) changed" % changed)
    if gone:
        print("  !! %d trailer file(s) will no longer be referenced by any "
              "listing, and Partner Center DELETES them on import:" % len(gone))
        for g in gone:
            print("       %s" % g)
    else:
        print("     no trailer file loses its last reference")


SHARED_SHOTS = "_shared"


def attach_local_shots(rows, header, shots_dir):
    """Point screenshot cells at local files, for Import folder.

    Partner Center wants the path to start with the import folder's own
    name, so it is built from that folder rather than from the path given
    here -- getting it wrong is an import that silently uploads nothing.

    A `_shared` folder supplies any slot a language does not have of its
    own, and every language points at that one copy. Without it the five
    drawn slides went in thirty-one times each: two hundred and twenty-three
    image uploads where seventy-one would do, which is an import that starts
    and then simply stops.
    """
    shots_dir = os.path.abspath(shots_dir)
    root = os.path.basename(os.path.dirname(shots_dir))   # the import folder
    leaf = os.path.basename(shots_dir)

    def slots_in(folder, code):
        found = {}
        for name in sorted(os.listdir(folder)):
            slot, ext = os.path.splitext(name)
            if slot.isdigit() and ext.lower() == ".png":
                found[slot] = "%s/%s/%s/%s" % (root, leaf, code, name)
        return found

    shared = {}
    shared_dir = os.path.join(shots_dir, SHARED_SHOTS)
    if os.path.isdir(shared_dir):
        shared = slots_in(shared_dir, SHARED_SHOTS)
        print("  --shots: %d shared slot(s), uploaded once and used by all"
              % len(shared))

    by = {r[0]: r for r in rows[1:] if r}
    total, own = 0, 0
    for code in sorted(os.listdir(shots_dir)):
        folder = os.path.join(shots_dir, code)
        if not os.path.isdir(folder) or code == SHARED_SHOTS:
            continue
        col = column(header, code)
        if col is None:
            print("  --shots: no %r column; skipped" % code)
            continue
        mine = slots_in(folder, code)
        own += len(mine)
        use = dict(shared)
        use.update(mine)                  # a language's own file always wins
        for slot, path in sorted(use.items(), key=lambda kv: int(kv[0])):
            row = by.get("DesktopScreenshot%s" % slot)
            if row is None:
                continue
            while len(row) <= col:
                row.append("")
            row[col] = path
            total += 1
    print("  --shots: %d screenshot cell(s) across the languages, from %d "
          "shared file(s) and %d of their own"
          % (total, len(shared), own))


# Which logo file fills which row. The Override pair only takes effect when
# OverrideLogosForWin10 is true, which is why that is set alongside them --
# uploading a 150x150 and wondering why nothing changed is the usual way to
# lose an afternoon here.
LOGO_ROWS = (
    ("tile-300x300.png", "StoreLogo300x300"),
    ("tile-150x150.png", "StoreLogoOverride150x150"),
    ("tile-71x71.png", "StoreLogoOverride71x71"),
    ("boxart-1080x1080.png", "StoreLogo1080x1080"),
    ("poster-720x1080.png", "StoreLogo720x1080"),
    ("hero-1920x1080.png", "PromoImage1920x1080"),
)


def attach_local_logos(rows, header, logos_dir):
    """Point the logo cells at local files, for every language at once.

    A logo is not language-specific, so unlike the screenshots these are
    written into every language column. Setting them for English alone is
    how a listing ends up with one mark in English and the old one in the
    other twenty-nine.
    """
    logos_dir = os.path.abspath(logos_dir)
    root = os.path.basename(os.path.dirname(logos_dir))
    leaf = os.path.basename(logos_dir)
    by = {r[0]: r for r in rows[1:] if r}
    langs = [i for i in range(RESERVED_COLUMNS + 1, len(header))
             if (header[i] or "").strip()]
    done = 0
    for name, field in LOGO_ROWS:
        if not os.path.exists(os.path.join(logos_dir, name)):
            print("  --logos: %s missing; %s left alone" % (name, field))
            continue
        row = by.get(field)
        if row is None:
            print("  --logos: no %r row; skipped" % field)
            continue
        for i in langs:
            while len(row) <= i:
                row.append("")
            row[i] = "%s/%s/%s" % (root, leaf, name)
        done += 1
    flag = by.get("OverrideLogosForWin10")
    if flag is not None and done:
        for i in langs:
            while len(flag) <= i:
                flag.append("")
            flag[i] = "True"
    print("  --logos: %d logo row(s) set across %d language column(s)"
          % (done, len(langs)))


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    lang = data.get("language")
    if not lang:
        sys.exit("%s has no \"language\" key" % path)
    # Absent means DEFAULT_COPY, which is the point: a new language should
    # inherit the artwork by saying nothing. An explicit {} opts out.
    copy_from = data.get("_copy_from", DEFAULT_COPY)
    # Other keys starting with _ are notes to whoever edits the file.
    values = {k: v for k, v in data.items()
              if k != "language" and not k.startswith("_")}
    return lang, values, copy_from


def trim_to_changes(rows, baseline_path):
    """Keep only the rows that differ from `baseline_path`, plus trailers.

    Microsoft's import documentation: "If you don't want to make any edits
    to a particular field, you can delete the entire row from the
    spreadsheet, with the exception of the rows for trailers and their
    associated thumbnails and titles. Other than for these items, deleting a
    row will not impact the data associated with that field in your
    listings."

    So an unchanged row is noise, and dropping it takes the screenshot and
    logo rows with it -- which is what makes the import a .csv again rather
    than a folder of images that are already in Partner Center.

    Trailer rows are the documented exception and stay whatever they say:
    deleting one deletes the video from the account.

    Columns are NOT trimmed. A row that survives must carry every language's
    current value, because a blank Text cell is a deletion, not a no-op.
    """
    with io.open(baseline_path, encoding="utf-8-sig", newline="") as fh:
        was = {key(r[0]): r for r in csv.reader(fh) if r and r[0].strip()}

    header = rows[0]
    kept, changed, trailers = [header], [], 0
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        if row[0].strip().lower().startswith("trailer"):
            # An empty trailer row names no file, so dropping it cannot
            # delete one. Only the rows that actually hold a URL are kept,
            # which is 4 of 76 and the difference between a readable file
            # and a wall of commas.
            if any(c.strip() for c in row[RESERVED_COLUMNS:]):
                kept.append(row)
                trailers += 1
            continue
        old = was.get(key(row[0]))
        if old is None:
            kept.append(row)          # a field the baseline never had
            changed.append(row[0])
            continue
        padded = old + [""] * (len(row) - len(old))
        if padded[:len(row)] != row:
            kept.append(row)
            changed.append(row[0])

    print("\n--only-changed %s" % os.path.basename(baseline_path))
    print("  %d row(s) differ: %s" % (len(changed), ", ".join(changed) or "none"))
    print("  %d trailer row(s) kept verbatim (deleting one deletes the file)"
          % trailers)
    print("  %d unchanged row(s) dropped" % (len(rows) - len(kept)))
    return kept


def main(argv):
    # --drop <code>, repeatable: remove a language column entirely. For a
    # language added to the product by mistake -- an empty column is still a
    # listing, and Partner Center requires a Description in every listing,
    # so leaving it in place fails the import for a language you do not want.
    # --align-trailers: every language's trailers become exactly the base
    # listing's, including REMOVING ones the base no longer has. Opt-in,
    # never default, because it is the one thing this tool does that
    # Partner Center cannot undo: a trailer no listing references any more
    # is deleted from the account. The run reports each such file by name.
    align_trailers = "--align-trailers" in argv
    logos = None
    if "--logos" in argv:
        i = argv.index("--logos")
        logos = argv[i + 1]
        del argv[i:i + 2]
    argv = [a for a in argv if a != "--align-trailers"]
    # --shots DIR: point each language's DesktopScreenshotN at a local file
    # under DIR/<code>/N.png, for a folder import. These OVERRIDE inherited
    # artwork, which the asset copier never does -- a localised screenshot
    # is the one case where the base listing's image is the wrong answer.
    shots = None
    if "--shots" in argv:
        i = argv.index("--shots")
        shots = argv[i + 1]
        del argv[i:i + 2]
    # --only-changed BASELINE: write just the rows that differ from
    # BASELINE, which is normally the .csv last imported. Microsoft's import
    # docs are explicit that this is safe -- "deleting a row will not impact
    # the data associated with that field in your listings" -- and it turns
    # a 42 MB folder into a few kilobytes, because the rows carrying the
    # screenshot paths are among the ones that did not change.
    baseline = None
    if "--only-changed" in argv:
        i = argv.index("--only-changed")
        baseline = argv[i + 1]
        del argv[i:i + 2]
    drops = []
    while "--drop" in argv:
        i = argv.index("--drop")
        drops.append(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) < 2:
        sys.exit(__doc__)
    csv_path, json_paths = argv[0], argv[1:]

    # utf-8-sig: Excel's "CSV UTF-8" writes a BOM, and Partner Center's own
    # export may too. Reading it as plain utf-8 would put an invisible
    # character on the front of the word "Field" and match nothing.
    with io.open(csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        sys.exit("%s is empty" % csv_path)

    header = rows[0]
    # The third column is headed "Type (Type)" in a real export, not "Type",
    # so this checks the prefix rather than the whole string.
    shape = (key(header[0]) == "field" and key(header[1]) == "id"
             and key(header[2]).startswith("type"))
    if not shape:
        sys.exit("%s does not look like a Partner Center export -- its first "
                 "three columns are %r, expected Field, ID, Type"
                 % (csv_path, header[:3]))
    print("%s: %d rows, columns %s" % (os.path.basename(csv_path),
                                       len(rows) - 1, header))

    by_field = {}
    for row in rows[1:]:
        if row and row[0].strip():
            by_field.setdefault(key(row[0]), row)

    failed = False
    for path in json_paths:
        lang, values, copy_from = load(path)
        col = column(header, lang)
        if col is None:
            col = len(header)
            header.append(lang)
            print("  %s: new column %d" % (lang, col))
        else:
            print("  %s: existing column %d (%r)" % (lang, col, header[col]))

        unknown = [k for k in values if key(k) not in by_field]
        if copy_from:
            unknown += [k for k in (list(copy_from.get("fields", []))
                                    + list(copy_from.get("also", []))
                                    + list(copy_from.get("except", [])))
                        if key(k) not in by_field]
        if unknown:
            failed = True
            print("\n  %s: %d key(s) match no field in the export:"
                  % (path, len(unknown)))
            for k in unknown:
                near = [r[0] for f, r in by_field.items() if key(k)[:6] in f]
                print("      %-22s nearest: %s" % (k, ", ".join(near) or "none"))
            continue

        for name, value in values.items():
            row = by_field[key(name)]
            while len(row) <= col:
                row.append("")
            row[col] = value
        print("  %s: %d field(s) written" % (lang, len(values)))

        # Assets are reused, never re-uploaded: a Partner Center URL works in
        # any listing of the same product. This is how a new language gets
        # the screenshots the Store requires without anyone producing a set
        # in that language. Only empty cells are filled, so a language that
        # DOES have its own artwork keeps it.
        if copy_from:
            src = column(header, copy_from["column"])
            if src is None:
                failed = True
                print("      no %r column to copy from; have %s"
                      % (copy_from["column"], header))
                continue

            skip = {key(k) for k in copy_from.get("except", [])}
            wanted = []
            if copy_from.get("assets"):
                # Every row the export itself calls an asset.
                wanted += [r[0] for r in rows[1:]
                           if len(r) > 2 and ASSET_TYPE_HINT in r[2].lower()]
            wanted += list(copy_from.get("fields", []))
            # `also` is handled separately below, because it follows the
            # source even when the target already has a value.
            switches = {key(k) for k in copy_from.get("also", [])}
            wanted += list(copy_from.get("also", []))

            copied, kept, forced = 0, 0, 0
            for name in wanted:
                k = key(name)
                if k in skip:
                    continue
                row = by_field[k]
                while len(row) <= max(col, src):
                    row.append("")
                if not row[src].strip():
                    continue
                if k in switches:
                    # A switch, not content: it decides whether the assets
                    # just copied are used at all. OverrideLogosForWin10 sat
                    # at False on a language whose override logos had been
                    # copied in, which meant copying them achieved nothing.
                    # So these follow the source rather than being preserved.
                    if row[col] != row[src]:
                        row[col] = row[src]
                        forced += 1
                    continue
                if row[col].strip():
                    # Already has its own -- a localised screenshot uploaded
                    # by hand, say. Never overwritten.
                    kept += 1
                    continue
                row[col] = row[src]
                copied += 1
            print("      %d reused from %s, %d already had their own, "
                  "%d switch(es) aligned" % (copied, header[src], kept, forced))

        # The two Partner Center insists on per listing. A screenshot is also
        # required, but an empty cell there inherits the default column's,
        # which is the point -- English screenshots, no Chinese ones needed.
        for required in ("Description", "Title"):
            if key(required) not in {key(k) for k in values}:
                print("      note: %s not set for %s; it will inherit the "
                      "default column" % (required, lang))

    if failed:
        sys.exit("\nnothing written -- fix the key names above and re-run")

    # Every row padded to the header's width, or Excel and the importer
    # disagree about where the last column is.
    for row in rows[1:]:
        while len(row) < len(header):
            row.append("")

    if align_trailers:
        align_all_trailers(rows, header)
    if shots:
        attach_local_shots(rows, header, shots)
    if logos:
        attach_local_logos(rows, header, logos)

    for code in drops:
        i = column(header, code)
        if i is None:
            print("  --drop %s: no such column, nothing to do" % code)
            continue
        if i <= RESERVED_COLUMNS:
            sys.exit("--drop %s would remove %r, which is not a language"
                     % (code, header[i]))
        filled = sum(1 for r in rows[1:] if len(r) > i and r[i].strip())
        for row in rows:
            del row[i]
        print("  --drop %s: column removed (it held %d non-empty cell(s))"
              % (code, filled))

    suffix = "-filled.csv"
    if baseline:
        rows = trim_to_changes(rows, baseline)
        suffix = "-changes.csv"

    out = os.path.splitext(csv_path)[0] + suffix
    # BOM on purpose: the docs tell you to save as Excel's "CSV UTF-8", which
    # writes one, so this is the encoding Partner Center is known to accept.
    with io.open(out, "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print("\nwrote %s  (%d bytes)" % (out, os.path.getsize(out)))
    print("Import it with \"Import listings\" > \"Import .csv\" on the app "
          "overview page.")


if __name__ == "__main__":
    main(sys.argv[1:])
