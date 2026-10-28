"""The rules behind the occasional ask for a coffee or a review.

    py test_asks.py

Two things are tested here, and both are about counting honestly:

  1. DAYS USED.  A day counts once, however many times the laptop opens and
     shuts in it; a laptop asleep for three days counts one, not three; a
     clock moved back never counts a day twice; and a clock that was once
     set into the future cannot freeze the count until the calendar catches
     up with it.

  2. WHICH ASK, WHEN.  An ask is due once its count is REACHED, not only on
     the exact day, so one that could not be shown is late rather than lost.
     At most one a day. "Don't ask again" -- offered on the coffee card
     only -- stops every ask still to come, reviews included. The review is asked for in every build, standalone exe too.

No window is opened. Every path the code could write to -- the ask file,
the activity log and the folder they live in -- is pointed at a temporary
directory first, so running this cannot touch the real app's files.
"""

import json
import os
import shutil
import sys

# Thirty languages go through print(). A console in a legacy code page --
# GitHub's Windows runner uses cp1252 -- cannot encode Czech or Polish,
# and this file crashed there on every push from late September while
# passing locally, where the output was UTF-8 all along.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import blink_reminder as br

FAILURES = []


def check(what, got, want):
    if got == want:
        print("  ok    %s" % what)
    else:
        FAILURES.append(what)
        print("  FAIL  %s\n          got %r, want %r" % (what, got, want))


def always(_kind):
    return True


def coffee_only(kind):
    """A build where one kind of ask cannot be made at all."""
    return kind == "donate"


# ------------------------------------------------------------ 1. days used

def test_count_day():
    print("1. days used")
    s = br.fresh_asks()
    check("the first day counts", br.count_day(s, "2026-10-17"), True)
    check("  ...as day 1", s["days_used"], 1)

    for _ in range(20):
        br.count_day(s, "2026-10-17")
    check("twenty more launches the same day count nothing",
          s["days_used"], 1)

    check("waking three days later counts one day",
          br.count_day(s, "2026-10-20"), True)
    check("  ...so the count is 2, not 4", s["days_used"], 2)

    # One day back is a timezone, or a clock nudged: no count, nothing moves.
    check("a clock moved back a day does not count",
          br.count_day(s, "2026-10-19"), False)
    check("  ...and the count stands", s["days_used"], 2)
    check("  ...and the last day counted is kept", s["last_counted"],
          "2026-10-20")

    # Further back than any timezone can reach, and the code cannot tell
    # "the clock is wrong now" from "the clock was wrong then". It assumes
    # THEN, deliberately: guessing wrong that way over-counts a day or two,
    # while guessing wrong the other way -- a clock that once read 2030 --
    # would freeze the count for years.
    s = br.fresh_asks()
    br.count_day(s, "2030-01-01")
    moved = br.count_day(s, "2026-10-20")
    check("a future date is pulled back without counting today", moved, False)
    check("  ...to today", s["last_counted"], "2026-10-20")
    check("  ...so tomorrow counts again", br.count_day(s, "2026-10-21"), True)

    s = br.fresh_asks()
    s["last_counted"] = "not a date at all"
    br.count_day(s, "2026-10-20")      # "n" sorts after "2": reads as future
    check("an unreadable last date is reset", s["last_counted"], "2026-10-20")


# --------------------------------------------------------- 2. which ask

def at(days, **kw):
    s = br.fresh_asks()
    s["days_used"] = days
    s.update(kw)
    return s


def test_due_ask():
    print("\n2. which ask, when")
    check("nothing before day 12", br.due_ask(at(11), "d", always), None)
    check("day 12 asks for a coffee", br.due_ask(at(12), "d", always),
          (12, "donate"))
    check("day 14 still asks it, if 12 never got shown",
          br.due_ask(at(14), "d", always), (12, "donate"))
    check("once shown, nothing until day 25",
          br.due_ask(at(24, shown=[12]), "d", always), None)
    check("day 25 asks for a review",
          br.due_ask(at(25, shown=[12]), "d", always), (25, "review"))

    check("at most one a day",
          br.due_ask(at(25, shown=[12], last_ask="d"), "d", always), None)
    check("two overdue arrive oldest first",
          br.due_ask(at(30), "d", always), (12, "donate"))
    check("  ...and the second one waits for another day",
          br.due_ask(at(30, shown=[12], last_ask="d"), "d", always), None)
    check("  ...which is the next day",
          br.due_ask(at(31, shown=[12], last_ask="d"), "e", always),
          (25, "review"))

    check("Don't ask again stops the coffee",
          br.due_ask(at(12, opted_out=True), "d", always), None)
    check("  ...and the review as well",
          br.due_ask(at(25, shown=[12], opted_out=True), "d", always), None)
    check("  ...and every ask after it",
          br.due_ask(at(999, shown=[12], opted_out=True), "d", always), None)

    check("every build asks for a review, the standalone exe included",
          br.ask_possible("review"), True)
    check("a kind that cannot be asked is skipped",
          br.due_ask(at(25, shown=[12]), "d", coffee_only), None)
    check("  ...and does not block the next coffee",
          br.due_ask(at(55, shown=[12]), "d", coffee_only), (55, "donate"))

    every = [d for d, _k in br.ASK_SCHEDULE]
    check("all six spent, nothing more ever",
          br.due_ask(at(999, shown=every), "d", always), None)
    check("the schedule the author set",
          br.ASK_SCHEDULE,
          ((12, "donate"), (25, "review"), (55, "donate"),
           (70, "review"), (150, "donate"), (170, "review")))


# ---------------------------------------------------------- 3. the file

def test_file(tmp):
    print("\n3. the file")
    state = br.fresh_asks()
    state.update(days_used=13, last_counted="2026-10-17", shown=[12],
                 opted_out=True, last_ask="2026-10-17")
    br.save_asks(state)
    check("saved and loaded back unchanged", br.load_asks(), state)
    check("no temp file left behind",
          os.path.exists(br.ASKS_PATH + ".tmp"), False)

    with open(br.ASKS_PATH, "w", encoding="utf-8") as fh:
        fh.write("{ this is not json")
    check("a damaged file starts again rather than failing",
          br.load_asks(), br.fresh_asks())

    with open(br.ASKS_PATH, "w", encoding="utf-8") as fh:
        json.dump({"days_used": "lots", "shown": [12, True, "25"],
                   "opted_out": "yes", "last_counted": "2026-10-01"}, fh)
    got = br.load_asks()
    check("a bad count is dropped, not trusted", got["days_used"], 0)
    check("only real day numbers survive in shown", got["shown"], [12])
    check("only a real true opts out", got["opted_out"], False)
    check("the good field next to bad ones is kept", got["last_counted"],
          "2026-10-01")

    with open(br.ASKS_PATH, "w", encoding="utf-8") as fh:
        json.dump({"days_used": 30, "no_donate": True}, fh)
    check("someone who opted out under the old name stays out",
          br.load_asks()["opted_out"], True)

    os.remove(br.ASKS_PATH)
    check("no file at all is a fresh start", br.load_asks(), br.fresh_asks())


def test_problem_report():
    """The way out for a user with a problem rather than an opinion.

    Until this existed the app offered a donation page and the Store's review
    box and nothing else, so a user whose app was broken could only leave a
    review -- which is exactly how the 1.4.2.0 crash was reported, by someone
    who had the traceback on screen and nowhere to send it.

    What is checked is that the draft arrives carrying the answers. An address
    on its own earns "it doesn't work"; an address that brings the version,
    the Windows build and the path to the log earns a report worth reading.
    """
    print("\n4. reporting a problem")
    br.set_language("en")
    facts = br.problem_facts()

    for what, needle in (("the app and its version",
                          "%s %s" % (br.DISPLAY_NAME, br.APP_VERSION)),
                         ("the Windows build", br.windows_build()),
                         ("the language in force", "Language: en"),
                         ("the path to the log", br.LOG_PATH)):
        check("the details carry %s" % what, needle in facts, True)

    # There was a mailto here, and it opened nothing on the first machine it
    # was tried on: a handler was registered for a mail client that was not
    # installed, so os.startfile succeeded and open_link returned True while
    # no window appeared. An address shown on screen cannot fail that way,
    # and it also reaches the webmail users no mailto handler ever could.
    check("no mailto is used at all",
          any(s.startswith("mailto") for s in br.SAFE_SCHEMES), False)
    check("... and the app no longer builds one",
          hasattr(br, "problem_report_link"), False)

    shown = br.T(
        "Please email %s for any problems or feedback. Thank you!\n\n"
        "You can paste these details into the email and attach the log "
        "file, \"activity.log\", which helps me investigate the problem. "
        "The log file should be in the window that just popped up."
        "\n\n%s") % (br.SUPPORT_EMAIL, facts)
    check("the dialog shows the address", br.SUPPORT_EMAIL in shown, True)
    check("... and the details under it", shown.endswith(facts), True)
    check("... and names the log file to attach",
          '"activity.log"' in shown, True)
    check("... and points at the window reveal_log just opened",
          "just popped up" in shown, True)

    # The log path sits on its own line: pasted into an email it is long
    # enough to wrap, and a path wrapped after "Log file:" reads as two
    # separate things.
    check("the log path is on a line of its own",
          "Log file:\n" + br.LOG_PATH in facts, True)

    was = br.PACKAGED
    try:
        br.PACKAGED = True
        check("a Store install says so, since it is a different build",
              "(MS Store)" in br.problem_facts(), True)
        br.PACKAGED = False
        check("... and the loose exe does not claim to be one",
              "(MS Store)" in br.problem_facts(), False)
    finally:
        br.PACKAGED = was

    # The version in a bug report is only useful if it is the version in the
    # file's properties. build.check_app_version refuses a build where these
    # two differ; this is the same claim from the other side.
    import build as appbuild
    check("APP_VERSION matches the version the exe is stamped with",
          br.APP_VERSION, "%d.%d.%d.%d" % appbuild.VERSION)

    # A nonsense scheme must still be refused: the allowlist is what stops a
    # typo here from handing os.startfile something it should not open.
    opened = []
    real = br.os.startfile
    br.os.startfile = lambda t: opened.append(t)
    try:
        check("a bad scheme is refused", br.open_link("javascript:alert(1)"),
              False)
        check("... and nothing was opened", opened, [])
        check("a link the app really uses is accepted",
              br.open_link(br.REVIEW_URL), True)
    finally:
        br.os.startfile = real


def main():
    tmp = tempfile.mkdtemp(prefix="blink-asks-test-")
    br.CONFIG_DIR = tmp
    br.ASKS_PATH = os.path.join(tmp, "asks.json")
    br.LOG_PATH = os.path.join(tmp, "activity.log")
    try:
        test_count_day()
        test_due_ask()
        test_file(tmp)
        test_problem_report()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
