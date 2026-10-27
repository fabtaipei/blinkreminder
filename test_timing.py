"""The rules behind WHEN a reminder happens, and how fast it may pulse.

    py test_timing.py

Four things are tested here:

  1. THE CLOCK.  Breaks land on a boundary counted from midnight, recomputed
     from the clock every time, so drift, sleep and a laptop shut overnight
     cannot walk them out of step.

  2. THE SCHEDULE.  One blink timer exists at a time, a pending one is always
     cancelled before a new one is set, and a pause sets none at all. Above
     all: fire() re-arms itself even when the reminder it was running threw,
     which is the bug its own finally clause was written for.

  3. THE SNOOZE.  A snooze ends. Resuming early cancels the original job, so
     it cannot fire at the half-hour mark and restart the clock from there.

  4. THE FLASH CEILING.  A repeating pulse cannot cycle faster than
     MIN_PULSE_CYCLE_MS however the numbers are set -- WCAG 2.3.1 is "no more
     than three flashes in any one second" and Store Policy 11.3.2 forbids
     products that cause discomfort. Applied where pulse configs are built,
     so a hand-edited config.json cannot get round it either.

No window is opened and no Tk root is created: the App methods under test are
run against a stand-in that records after() calls instead of running an event
loop. The activity log is pointed at a temporary directory first, so running
this cannot touch the real app's files.
"""

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
LOG = []


def check(what, got, want):
    if got == want:
        print("  ok    %s" % what)
    else:
        FAILURES.append(what)
        print("  FAIL  %s\n          got %r, want %r" % (what, got, want))


class FakeClock(object):
    """A fixed wall clock, so a boundary test has one right answer.

    Only the two functions blink_reminder asks of the time module, because a
    stand-in that silently answers everything is a stand-in that hides the
    day someone starts calling something else.
    """

    def __init__(self, hour, minute, second):
        self.at = (hour, minute, second)
        self.ticks = 0.0

    def localtime(self):
        hour, minute, second = self.at
        class T(object):
            tm_hour = hour
            tm_min = minute
            tm_sec = second
        return T()

    def monotonic(self):
        return self.ticks

    def strftime(self, fmt, *a):
        return "fake-time"


class FakeRoot(object):
    """Records after()/after_cancel() instead of running a Tk event loop."""

    def __init__(self):
        self.jobs = {}
        self.cancelled = []
        self.n = 0

    def after(self, ms, fn=None):
        self.n += 1
        token = "job%d" % self.n
        self.jobs[token] = (ms, fn)
        return token

    def after_cancel(self, token):
        self.cancelled.append(token)
        self.jobs.pop(token, None)

    # -- what a test wants to ask afterwards ---------------------------------
    def pending(self):
        """(ms, ...) for every job still armed, in the order they were set."""
        return [ms for ms, _fn in self.jobs.values()]


class Ticker(object):
    """Enough of an App for schedule(), fire(), snooze() and heartbeat()."""

    def __init__(self, **over):
        self.root = FakeRoot()
        self.cfg = dict(br.DEFAULTS)
        self.cfg.update(over)
        self.paused = False
        self.timer = None
        self.break_timer = None
        self.snooze_job = None
        self.last_fire = 0.0
        self.last_beat = 0.0
        self.pulses = []
        self.idle = []
        self.raise_on_pulse = False
        # fire() reaches the overlay through self.overlay; being our own
        # overlay keeps the stand-in to one object.
        self.overlay = self
        self.busy = False

    # -- App methods under test, bound to this stand-in ----------------------
    def schedule(self):
        return br.App.schedule(self)

    def schedule_break(self):
        return br.App.schedule_break(self)

    def fire(self):
        return br.App.fire(self)

    def snooze(self, minutes):
        return br.App.snooze(self, minutes)

    def wake(self):
        return br.App.wake(self)

    def cancel_snooze(self):
        return br.App.cancel_snooze(self)

    def heartbeat(self):
        return br.App.heartbeat(self)

    # -- App collaborators, stubbed ------------------------------------------
    def lesson(self, cfg):
        return cfg, False

    def when_idle(self, step, settle_ms=400):
        self.idle.append(step)

    def ask_calibration(self):
        pass

    def check_asks(self):
        pass

    # -- Overlay -------------------------------------------------------------
    def pulse(self, cfg):
        if self.raise_on_pulse:
            raise RuntimeError("the reminder blew up mid-pulse")
        self.pulses.append(cfg)

    def interrupt(self):
        pass


def errors():
    return [d for k, d in LOG if k == "ERROR"]


def kinds(kind):
    return [d for k, d in LOG if k == kind]


def test_clock():
    print("\n1. the clock")
    real = br.time
    try:
        # 10:07:30 with a 30-minute break: the last boundary was 10:00, so
        # 7m30s has gone and 22m30s is left. Worked out by hand on purpose --
        # a test that recomputes the implementation proves only that it is
        # self-consistent.
        br.time = FakeClock(10, 7, 30)
        check("22m30s left of a 30-minute break at 10:07:30",
              br.seconds_to_next_break(30), 1350)
        check("a 15-minute break at the same moment has 7m30s left",
              br.seconds_to_next_break(15), 450)
        check("exactly on the boundary gives a whole interval, never 0",
              br.seconds_to_next_break(30) > 0, True)

        br.time = FakeClock(10, 30, 0)
        check("standing exactly on 10:30, the next 30 is a full 30 away",
              br.seconds_to_next_break(30), 1800)

        # Anchored to MIDNIGHT, not to the hour. 7 does not divide 60, so an
        # hour-anchored version would produce a short gap at the top of every
        # hour. Rather than assert one hand-worked number, walk the day and
        # insist every boundary it points at is a whole number of steps from
        # midnight -- which is the property the docstring actually claims.
        step = 7
        off_grid = []
        for hour in range(24):
            for minute in (0, 13, 41, 59):
                br.time = FakeClock(hour, minute, 0)
                left = br.seconds_to_next_break(step)
                landing = (hour * 60 + minute) * 60 + left
                if landing % (step * 60):
                    off_grid.append((hour, minute, left))
        check("a 7-minute step lands only on midnight-anchored boundaries",
              off_grid, [])

        for step in (5, 10, 15, 20, 30, 60):
            for hour in (0, 9, 13, 23):
                for minute in (0, 1, 29, 59):
                    br.time = FakeClock(hour, minute, 0)
                    left = br.seconds_to_next_break(step)
                    if not 0 < left <= step * 60:
                        check("%dmin step at %02d:%02d is inside its interval"
                              % (step, hour, minute), left, "0 < n <= %d"
                              % (step * 60))
                        break
        check("every step at every tested moment lands inside its interval",
              True, True)

        br.time = FakeClock(10, 7, 30)
        check("0 minutes cannot divide by zero; it clamps to 1",
              0 < br.seconds_to_next_break(0) <= 60, True)
        check("a negative is clamped the same way",
              0 < br.seconds_to_next_break(-5) <= 60, True)
    finally:
        br.time = real


def test_schedule():
    print("\n2. the schedule")
    app = Ticker(interval_seconds=45)
    app.schedule()
    check("a blink is armed at the configured interval, in ms",
          app.root.pending(), [45000])

    first = app.timer
    app.schedule()
    check("scheduling again cancels the pending one first",
          app.root.cancelled, [first])
    check("... and leaves exactly one armed", len(app.root.pending()), 1)

    paused = Ticker()
    paused.schedule()
    paused.paused = True
    paused.schedule()
    check("a paused app arms nothing", paused.root.pending(), [])
    check("... and its timer handle is cleared, not left dangling",
          paused.timer, None)

    # The bug fire()'s finally clause exists for: an exception on the way to
    # the screen used to skip schedule(), so reminders stopped for the life of
    # the process and the log said nothing about why.
    boom = Ticker(interval_seconds=45)
    boom.raise_on_pulse = True
    boom.fire()
    check("a reminder that throws is written down", len(errors()), 1)
    check("... and the next one is still armed",
          boom.root.pending(), [45000])
    check("... and nothing reached the screen", boom.pulses, [])

    ok = Ticker(interval_seconds=45)
    ok.fire()
    check("an ordinary reminder reaches the screen once", len(ok.pulses), 1)
    check("... and re-arms at the interval", ok.root.pending(), [45000])

    # A break on screen wins, but the blink it displaced is owed, not lost.
    busy = Ticker(interval_seconds=45)
    busy.busy = True
    busy.fire()
    check("a blink landing inside a break is pushed out, not dropped",
          busy.root.pending(), [br.BLINK_RETRY_MS])
    check("... and does not pulse on top of the break", busy.pulses, [])

    off = Ticker(break_enabled=False)
    off.schedule_break()
    check("breaks switched off arm no break timer", off.root.pending(), [])


def test_snooze():
    print("\n3. the snooze")
    app = Ticker()
    app.snooze(30)
    check("a snooze pauses", app.paused, True)
    check("... arms a wake 30 minutes out, in ms",
          app.root.jobs[app.snooze_job][0], 30 * 60000)
    check("... and arms no blink while paused",
          [ms for ms in app.root.pending() if ms != 30 * 60000], [])

    first = app.snooze_job
    app.snooze(30)
    check("snoozing again cancels the first wake, leaving no orphan",
          first in app.root.cancelled, True)

    app.wake()
    check("waking resumes", app.paused, False)
    check("... cancels its own wake job, so the original mark cannot fire",
          app.snooze_job, None)
    check("... and arms the blink again", app.root.pending(), [45000])


def test_flash_ceiling():
    print("\n4. the flash ceiling")
    base = dict(br.DEFAULTS)

    one = br.limit_flash_rate(dict(base, blinks=1, hold_ms=0, fade_ms=0,
                                   gap_ms=0))
    check("a single pulse cannot flash at a rate, so its gap is left alone",
          (one["blinks"], one["gap_ms"]), (1, 0))

    strobe = br.limit_flash_rate(dict(base, blinks=2, hold_ms=0, fade_ms=0,
                                      gap_ms=0))
    cycle = 2 * strobe["fade_ms"] + strobe["hold_ms"] + strobe["gap_ms"]
    check("three zeros and a repeat cannot build a strobe",
          cycle >= br.MIN_PULSE_CYCLE_MS, True)
    check("... and the gap is what was lengthened, exactly to the floor",
          strobe["gap_ms"], br.MIN_PULSE_CYCLE_MS)
    check("... while the look the user tuned is untouched",
          (strobe["hold_ms"], strobe["fade_ms"]), (0, 0))

    sharp = dict(base, blinks=3, hold_ms=150, fade_ms=60, gap_ms=0)
    limited = br.limit_flash_rate(dict(sharp))
    check("the Sharp preset is raised to the floor, not past it",
          2 * limited["fade_ms"] + limited["hold_ms"] + limited["gap_ms"],
          br.MIN_PULSE_CYCLE_MS)

    roomy = dict(base, blinks=2, hold_ms=800, fade_ms=700, gap_ms=150)
    check("a cycle already slow enough is not touched at all",
          br.limit_flash_rate(dict(roomy)), roomy)

    check("blinks are capped",
          br.limit_flash_rate(dict(base, blinks=999))["blinks"], br.MAX_BLINKS)
    check("... and floored at one",
          br.limit_flash_rate(dict(base, blinks=0))["blinks"], 1)
    check("a negative count cannot invert the loop",
          br.limit_flash_rate(dict(base, blinks=-3))["blinks"], 1)

    # The ceiling lives where pulse configs are BUILT, which is what stops a
    # hand-edited config.json from getting round the spinboxes.
    hand_edited = dict(base, blinks=4, hold_ms=0, fade_ms=0, gap_ms=0)
    built = br.blink_cfg(hand_edited)
    check("blink_cfg applies the ceiling to a hand-edited config",
          2 * built["fade_ms"] + built["hold_ms"] + built["gap_ms"]
          >= br.MIN_PULSE_CYCLE_MS, True)
    check("... and leaves the caller's own dict alone",
          hand_edited["gap_ms"], 0)


def test_heartbeat():
    print("\n5. the heartbeat")
    real = br.time
    try:
        clock = FakeClock(10, 0, 0)
        br.time = clock
        app = Ticker()
        app.last_beat = 0.0
        clock.ticks = br.HEARTBEAT_S
        del LOG[:]
        app.heartbeat()
        check("a punctual beat is not worth writing down",
              kinds("stalled"), [])
        check("... and the next beat is always armed",
              app.root.pending(), [br.HEARTBEAT_S * 1000])

        app = Ticker()
        app.last_beat = 0.0
        clock.ticks = br.HEARTBEAT_S + br.STALL_TOLERANCE_S + 120
        del LOG[:]
        app.heartbeat()
        check("a beat that came back late is recorded as a stall",
              len(kinds("stalled")), 1)
        check("... and the heartbeat still re-arms",
              app.root.pending(), [br.HEARTBEAT_S * 1000])
    finally:
        br.time = real


def main():
    tmp = tempfile.mkdtemp(prefix="blink-timing-test-")
    br.CONFIG_DIR = tmp
    br.LOG_PATH = os.path.join(tmp, "activity.log")
    # Recorded rather than silenced: several checks here are about what the
    # app writes down when something goes wrong.
    br.log_event = lambda kind, detail="": LOG.append((kind, detail))
    try:
        test_clock()
        del LOG[:]
        test_schedule()
        del LOG[:]
        test_snooze()
        del LOG[:]
        test_flash_ceiling()
        test_heartbeat()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
