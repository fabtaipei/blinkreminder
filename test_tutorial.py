"""The rules behind the first-run tutorial.

    py test_tutorial.py

Three things are tested here:

  1. THE LESSON.  The first TEACH_COUNT blink reminders carry the
     instruction, the next ordinary one is followed by the strength
     question, and none of it is spent while Windows says nobody can see
     the screen.

  2. THE QUESTION.  Each of its four buttons opens Settings at the control
     it names, changes nothing itself and leaves the card up; "Got it" or
     closing the card ends the question for good.

  3. THE FILE.  A missing or damaged tutorial.json costs at most a second
     lesson; it can never stop the app starting.

No window is opened. The tutorial file and the activity log are pointed at
a temporary directory first, so running this cannot touch the real app's
files, and the App methods are run against a stand-in rather than a real
App, so no Tk root is ever created.
"""

import json
import os
import shutil
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


class Recorder(object):
    """Enough of an App for lesson() and calibrate() to run against."""

    def __init__(self, cfg=None):
        self.tutorial = br.fresh_tutorial()
        self.tutorial_test = False
        self.cfg = dict(cfg or br.DEFAULTS)
        self.saved = 0
        self.applied = []
        self.pulsed = []
        self.idle = []
        self.overlay = self
        self.busy = False
        self.pointed = []
        self.settings = self

    # App
    def keep_tutorial(self):
        self.saved += 1

    def apply(self, cfg):
        self.applied.append(cfg)
        self.cfg = cfg

    # Settings
    def point_at(self, target):
        self.pointed.append(target)

    def when_idle(self, step, settle_ms=400):
        self.idle.append(step)

    def ask_calibration(self):
        pass

    # Overlay
    def pulse(self, cfg):
        self.pulsed.append(cfg)


def test_lesson():
    print("\n1. the lesson")
    app = Recorder()
    br.user_is_available = lambda: True
    plain = br.blink_cfg(app.cfg)
    for n in range(1, br.TEACH_COUNT + 1):
        cfg, ask = br.App.lesson(app, dict(plain))
        if n in (1, br.TEACH_COUNT):
            check("reminder %d is taught" % n, "caption" in cfg, True)
            check("reminder %d is not followed by the question" % n, ask, False)
    check("each taught reminder is counted and saved",
          (app.tutorial["taught"], app.saved),
          (br.TEACH_COUNT, br.TEACH_COUNT))

    cfg, ask = br.App.lesson(app, dict(plain))
    check("the next reminder is an ordinary one", "caption" in cfg, False)
    check("... and is followed by the question", ask, True)

    br.user_is_available = lambda: False
    fresh = Recorder()
    cfg, ask = br.App.lesson(fresh, dict(plain))
    check("nothing is taught while nobody can see the screen",
          ("caption" in cfg, ask, fresh.tutorial["taught"]), (False, False, 0))
    br.user_is_available = lambda: True

    app.tutorial["calibration"] = "done"
    cfg, ask = br.App.lesson(app, dict(plain))
    check("once it is over, a reminder is left alone",
          (cfg == plain, ask), (True, False))

    taught = br.teaching_cfg(dict(plain))
    check("a taught reminder is at least TEACH_OPACITY",
          taught["opacity"] >= br.TEACH_OPACITY, True)
    check("a taught reminder holds long enough to read",
          taught["hold_ms"] >= br.TEACH_HOLD_MS, True)
    check("a taught reminder pulses once", taught["blinks"], 1)
    check("teaching_cfg leaves the config it was given alone",
          "caption" in plain, False)

    word = dict(plain, style="text", message="Blink")
    taught = br.teaching_cfg(word)
    check("the word style shows the caption AS its word, on one line",
          ("caption" in taught, "\n" in taught["message"],
           taught["message"] != "Blink"), (False, False, True))
    dim = br.teaching_cfg(dict(plain, style="dim", opacity=0.1))
    check("a taught dim needs less opacity than a dot",
          dim["opacity"], br.TEACH_OPACITY_DIM)

    check("dark ink on the lime default", br.caption_ink("#bde401"), "#11161C")
    check("white ink on a dark colour", br.caption_ink("#12233f"), "#FFFFFF")
    check("a colour that will not parse gets white", br.caption_ink("lime"),
          "#FFFFFF")
    check("the ink is never the dot's transparent key",
          br.caption_ink("#ffffff") != "#010101", True)


def test_question():
    print("\n2. the question")
    app = Recorder()
    app.tutorial["taught"] = br.TEACH_COUNT
    for target in br.CalibrationCard.TARGETS:
        br.App.calibrate(app, target)
    check("each button opens Settings at its control, changing nothing",
          (app.pointed, app.applied, app.pulsed),
          (list(br.CalibrationCard.TARGETS), [], []))
    check("... and leaves the question open", br.calibration_due(app.tutorial),
          True)

    for answer in ("got it", "closed"):
        app = Recorder()
        app.tutorial["taught"] = br.TEACH_COUNT
        br.App.calibrate(app, answer)
        check("%r ends the question for good, opening nothing" % answer,
              (br.calibration_due(app.tutorial), app.pointed, app.saved),
              (False, [], 1))


def test_file(tmp):
    print("\n3. the file")
    state = br.fresh_tutorial()
    state.update(welcomed=True, taught=3)
    br.save_tutorial(state)
    check("a saved state reads back", br.load_tutorial(), state)

    with open(br.TUTORIAL_PATH, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    check("a damaged file is a fresh start", br.load_tutorial(),
          br.fresh_tutorial())

    with open(br.TUTORIAL_PATH, "w", encoding="utf-8") as fh:
        json.dump({"welcomed": "yes", "taught": -4, "rounds": True,
                   "calibration": "maybe"}, fh)
    check("each bad field falls back on its own", br.load_tutorial(),
          br.fresh_tutorial())

    with open(br.TUTORIAL_PATH, "w", encoding="utf-8") as fh:
        json.dump({"welcomed": True, "taught": "five"}, fh)
    got = br.load_tutorial()
    check("a good field next to a bad one is kept",
          (got["welcomed"], got["taught"]), (True, 0))

    os.remove(br.TUTORIAL_PATH)
    check("no file at all is a fresh start", br.load_tutorial(),
          br.fresh_tutorial())


def main():
    tmp = tempfile.mkdtemp(prefix="blink-tutorial-test-")
    br.CONFIG_DIR = tmp
    br.TUTORIAL_PATH = os.path.join(tmp, "tutorial.json")
    br.LOG_PATH = os.path.join(tmp, "activity.log")
    br.log_event = lambda *a, **k: None
    try:
        test_lesson()
        test_question()
        test_file(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
