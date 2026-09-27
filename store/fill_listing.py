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


def key(name):
    """Field names, reduced so "Short description" == "ShortDescription"."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    lang = data.get("language")
    if not lang:
        sys.exit("%s has no \"language\" key" % path)
    # Keys starting with _ are notes to whoever edits the file.
    values = {k: v for k, v in data.items()
              if k != "language" and not k.startswith("_")}
    return lang, values


def main(argv):
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
    if [key(c) for c in header[:3]] != list(FIXED):
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
        lang, values = load(path)
        if lang in header:
            col = header.index(lang)
        else:
            col = len(header)
            header.append(lang)
            print("  %s: new column %d" % (lang, col))

        unknown = [k for k in values if key(k) not in by_field]
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
