"""Write one or more languages into a Partner Center listings .csv.

    py store\\fill_listing.py <exported.csv> store\\listing-zh-Hant.json ...

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


def column(header, code):
    """The index of a language column, however Partner Center cased it.

    The export writes the codes lower-case -- "zh-hant" -- while the manifest
    and everything else in this repo use "zh-Hant". Matching exactly would
    quietly add a SECOND column and leave the listing empty.
    """
    for i, name in enumerate(header):
        if (name or "").lower() == code.lower():
            return i
    return None


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


def main(argv):
    # --drop <code>, repeatable: remove a language column entirely. For a
    # language added to the product by mistake -- an empty column is still a
    # listing, and Partner Center requires a Description in every listing,
    # so leaving it in place fails the import for a language you do not want.
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

    for code in drops:
        i = column(header, code)
        if i is None:
            print("  --drop %s: no such column, nothing to do" % code)
            continue
        if i < 4:
            sys.exit("--drop %s would remove %r, which is not a language"
                     % (code, header[i]))
        filled = sum(1 for r in rows[1:] if len(r) > i and r[i].strip())
        for row in rows:
            del row[i]
        print("  --drop %s: column removed (it held %d non-empty cell(s))"
              % (code, filled))

    out = os.path.splitext(csv_path)[0] + "-filled.csv"
    # BOM on purpose: the docs tell you to save as Excel's "CSV UTF-8", which
    # writes one, so this is the encoding Partner Center is known to accept.
    with io.open(out, "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print("\nwrote %s  (%d bytes)" % (out, os.path.getsize(out)))
    print("Import it with \"Import listings\" > \"Import .csv\" on the app "
          "overview page.")


if __name__ == "__main__":
    main(sys.argv[1:])
