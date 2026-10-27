"""Launch the BUILT app and prove it actually starts.

    py smoke_launch.py              the one-file exe in dist/
    py smoke_launch.py --onedir     the folder build in dist-dir/

This is the check that was missing when 1.4.2.0 shipped. Everything else in
this project runs against SOURCE, on a machine with every library installed --
which is the one environment where a packaging bug cannot appear. The exe was
excluding a Pillow extension the icon had started needing, so the app died on
launch for every user, and nothing in the build or the test suite was looking
at the thing that was actually broken.

It needs no knowledge of Pillow, fonts or exclusions. It starts the artifact,
waits for the app to write its own "start" line, and fails if that line never
comes or if anything was logged as an ERROR. Any future "the package is
missing something" bug fails here the same way, including the ones nobody has
thought of yet.

WHAT IT WILL NOT DO
  - It will not run while a copy of the app is already running. The loser of
    the single-instance check shows an "already running" DIALOG, so a smoke
    test that ignored this would put a window on the author's screen and then
    report a false failure.
  - It will not touch the real settings or log. The child gets its own APPDATA
    in a temporary directory, seeded so that nothing is due: a very long
    interval, breaks off, and a tutorial already marked as seen. A first run
    would otherwise open the welcome card -- a real window, on a real screen.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build as appbuild
import blink_reminder as br

# How long to wait for the app to say it started. Generous: a one-file exe
# unpacks itself into %TEMP% first, and a cold CI runner is slow.
START_TIMEOUT_S = 60
# How long to watch it after it starts, to catch something that dies a moment
# later rather than immediately.
SETTLE_S = 5


def artifact(onedir):
    """The exe to launch, and a clear refusal if it is missing or stale."""
    if onedir:
        path = os.path.join(appbuild.ARTIFACTS["folder"],
                            appbuild.NAME + ".exe")
        kind = "folder"
    else:
        path = appbuild.ARTIFACTS["exe"]
        kind = "exe"
    if not os.path.exists(path):
        sys.exit("no build at %s\n  run: py build.py%s"
                 % (path, " --onedir" if onedir else ""))
    state = dict((k, s) for k, s, _d in appbuild.freshness()).get(kind)
    if state != "fresh":
        # Refusing rather than warning. A smoke test that passes against
        # yesterday's exe is worse than no smoke test: it reports confidence
        # in a file nobody is about to ship.
        sys.exit("the %s build is %s -- rebuild before smoke testing it"
                 % (kind, state))
    return path


def already_running():
    """True if any copy of the app is up, under any of its names.

    Asked of the image name rather than of the mutex: the mutex is held by the
    app, and opening it from here to look would be one more thing that can go
    wrong in a test whose whole job is to be trustworthy.
    """
    out = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                         capture_output=True, text=True).stdout.lower()
    return [name for name in ("blinkreminder.exe",
                              appbuild.NAME.lower() + ".exe")
            if name in out]


def sandbox():
    """A private APPDATA, seeded so a launch has nothing to show anybody.

    Written with the app's OWN save functions rather than by hand-rolling
    JSON, so a seed file can never drift from the shape the app expects --
    which would make this test fail for a reason that is not the app's fault.
    """
    root = tempfile.mkdtemp(prefix="blink-smoke-")
    cfg_dir = os.path.join(root, br.APP_NAME)
    os.makedirs(cfg_dir, exist_ok=True)

    real = (br.CONFIG_DIR, br.CONFIG_PATH, br.TUTORIAL_PATH, br.ASKS_PATH,
            br.LOG_PATH)
    try:
        br.CONFIG_DIR = cfg_dir
        br.CONFIG_PATH = os.path.join(cfg_dir, "config.json")
        br.TUTORIAL_PATH = os.path.join(cfg_dir, "tutorial.json")
        br.ASKS_PATH = os.path.join(cfg_dir, "asks.json")
        br.LOG_PATH = os.path.join(cfg_dir, "activity.log")

        cfg = dict(br.DEFAULTS)
        # Nothing may reach the screen during the test. A day-long interval
        # and no breaks means the only thing the app does is start.
        cfg.update(interval_seconds=86400, break_enabled=False,
                   sound_enabled=False, start_with_windows=False)
        br.save_config(cfg)

        seen = br.fresh_tutorial()
        seen.update(welcomed=True, taught=br.TEACH_COUNT, calibration="done")
        br.save_tutorial(seen)
    finally:
        (br.CONFIG_DIR, br.CONFIG_PATH, br.TUTORIAL_PATH, br.ASKS_PATH,
         br.LOG_PATH) = real
    return root, os.path.join(cfg_dir, "activity.log")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def stop(proc):
    """Kill the whole tree, and wait for it to actually be gone.

    /T because a one-file build is a launcher plus a child: killing the
    launcher alone leaves the child holding the single-instance mutex, and the
    next launch -- this test's next run, or the author's -- loses the check and
    shows an "already running" dialog.
    """
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                   capture_output=True)
    for _ in range(40):
        if not already_running():
            return True
        time.sleep(0.25)
    return False


def smoke(onedir=False):
    exe = artifact(onedir)
    running = already_running()
    if running:
        sys.exit("%s is already running, so this test cannot launch a copy."
                 "\n  The loser of the single-instance check opens a dialog;"
                 " refusing instead."
                 "\n  Quit it from the tray icon (right-click > Quit), then"
                 " run this again." % ", ".join(running))

    root, log = sandbox()
    env = dict(os.environ)
    # The app reads CONFIG_DIR from APPDATA at import time, so this is the one
    # lever that moves its whole state -- settings, tutorial, asks and log.
    env["APPDATA"] = root
    # A startup crash shows a modal dialog, which no script can dismiss: the
    # run would hang for the full timeout and then be reported as "never
    # started" instead of as the error it actually hit. The log line is
    # written either way, and the log is what this test reads.
    env["BLINK_NO_CRASH_DIALOG"] = "1"
    print("launching: %s" % exe)
    print("sandbox:   %s" % root)

    proc = None
    try:
        proc = subprocess.Popen([exe], env=env, cwd=os.path.dirname(exe))
        started, deadline = False, time.monotonic() + START_TIMEOUT_S
        while time.monotonic() < deadline:
            if "  start " in read(log):
                started = True
                break
            if proc.poll() is not None:
                break
            time.sleep(0.25)

        body = read(log)
        if not started:
            why = ("it exited with code %s" % proc.poll()
                   if proc.poll() is not None
                   else "it never wrote one in %ds" % START_TIMEOUT_S)
            sys.exit("\n%s\nFAILED: no start line in the log -- %s.\n"
                     "  The log it did write is above. An ERROR line there is"
                     " the cause;\n  an empty log means it died before"
                     " logging, which is a missing\n  dependency or a broken"
                     " exe rather than a bug in the app."
                     % (body.strip() or "(the log is empty)", why))

        # Started is not the same as surviving. Watch a little longer, because
        # a tray icon that appears and then vanishes is still a broken launch.
        time.sleep(SETTLE_S)
        if proc.poll() is not None:
            sys.exit("\n%s\nFAILED: it started and then exited with code %s"
                     " within %ds."
                     % (read(log).strip(), proc.poll(), SETTLE_S))

        body = read(log)
        errors = [line for line in body.splitlines() if "  ERROR " in line]
        if errors:
            sys.exit("\n%s\nFAILED: it started but logged %d error(s), listed"
                     " above.\n  A packaged app that logs an ERROR on a clean"
                     " launch is not a clean launch."
                     % ("\n".join(errors), len(errors)))

        print("\n%s" % body.strip())
        print("\nPASSED: it started, logged no errors, and was still running"
              " %ds later." % SETTLE_S)
    finally:
        if proc is not None and proc.poll() is None:
            if not stop(proc):
                print("WARNING: a copy may still be running; check the tray.")
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    smoke(onedir="--onedir" in sys.argv)
