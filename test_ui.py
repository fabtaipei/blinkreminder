# -*- coding: utf-8 -*-
"""The two windows that only a real window can test.

    py test_ui.py

Everything else in this project tests logic. These two are tested by being
DRAWN, because what goes wrong with them -- a label that never reaches the
widget, a dialog that never appears -- is invisible to any assertion about
the function that was supposed to produce them.

  1. THE STARTUP BUTTON.  A real SettingsWindow is built and its button read:
     that startup_button_text() reaches the widget, that it fits the slot, and
     that refresh_startup_button() re-reads the state and relabels -- which is
     what happens when the user comes back from the Windows Settings page the
     button sent them to.

  2. THE CRASH DIALOG.  report_startup_failure is called for real, and the
     dialog it opens is found, read and dismissed. Every other test suppresses
     it with BLINK_NO_CRASH_DIALOG, because MessageBoxW is modal and would
     hang the run -- so without this, the one thing a user sees when the app
     dies is the one thing nothing checks. The only evidence anyone had of
     the 1.4.2.0 crash was a dialog; this is that dialog.

Both are real windows from the real code, created on a desktop this process
makes for itself. They cannot reach a real screen, keyboard or foreground: no
window appears, and nothing can take a keystroke from whoever is running it.
If the desktop cannot be created or switched to, this REFUSES to run rather
than drawing on the desktop somebody is using.

Every side effect is stubbed first. A test that writes a Startup shortcut or
opens a browser tab has changed the machine it was meant to be inspecting.
"""

import ctypes
import os
import sys
import threading
import time
from ctypes import byref, wintypes

REPO = os.path.dirname(os.path.abspath(__file__))
# Captures go to a temp directory, never beside this file: a test that leaves
# two PNGs in the repo every time it runs is a test people start skipping.
# The path is printed, so a failure can still be looked at.
OUT = None

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# argtypes on every call: an undeclared 64-bit handle gets truncated to int
# and has broken this project more than once.
user32.CreateDesktopW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR,
                                  ctypes.c_void_p, wintypes.DWORD,
                                  wintypes.DWORD, ctypes.c_void_p)
user32.CreateDesktopW.restype = wintypes.HANDLE
user32.SetThreadDesktop.argtypes = (wintypes.HANDLE,)
user32.SetThreadDesktop.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowDC.argtypes = (wintypes.HWND,)
user32.GetWindowDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
user32.ReleaseDC.restype = ctypes.c_int
user32.PrintWindow.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
user32.PrintWindow.restype = wintypes.BOOL
user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetWindowTextW.restype = ctypes.c_int
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT,
                                ctypes.c_void_p, ctypes.c_void_p)
user32.PostMessageW.restype = wintypes.BOOL
user32.SendMessageW.argtypes = (wintypes.HWND, wintypes.UINT,
                                ctypes.c_void_p, ctypes.c_void_p)
user32.SendMessageW.restype = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes = (wintypes.HDC,)
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = (wintypes.HDC, ctypes.c_int,
                                         ctypes.c_int)
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = (wintypes.HDC, wintypes.HGDIOBJ)
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = (wintypes.HGDIOBJ,)
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = (wintypes.HDC,)
gdi32.DeleteDC.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumThreadWindows.argtypes = (wintypes.DWORD, ENUMPROC, wintypes.LPARAM)
user32.EnumThreadWindows.restype = wintypes.BOOL
user32.EnumChildWindows.argtypes = (wintypes.HWND, ENUMPROC, wintypes.LPARAM)
user32.EnumChildWindows.restype = wintypes.BOOL

GENERIC_ALL = 0x10000000
PW_RENDERFULLCONTENT = 2
WM_CLOSE = 0x0010
BM_CLICK = 0x00F5


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]


gdi32.GetDIBits.argtypes = (wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                            wintypes.UINT, ctypes.c_void_p,
                            ctypes.POINTER(BITMAPINFO), wintypes.UINT)
gdi32.GetDIBits.restype = ctypes.c_int


# ---------------------------------------------------------------- desktop
# Before Tk exists. SetThreadDesktop only affects windows created afterwards,
# and blink_reminder imports tkinter at module level -- so this has to run
# before the import, not before the first window.
desk = user32.CreateDesktopW("BlinkVerify", None, None, 0, GENERIC_ALL, None)
if not desk:
    sys.exit("CreateDesktopW failed: %d" % ctypes.get_last_error())
if not user32.SetThreadDesktop(desk):
    sys.exit("SetThreadDesktop failed: %d -- refusing to draw on the real "
             "desktop" % ctypes.get_last_error())
print("private desktop: BlinkVerify (nothing below can reach a real screen)")

sys.path.insert(0, REPO)
import blink_reminder as br          # noqa: E402  (must follow the switch)
from PIL import Image                # noqa: E402

FAILURES = []


def check(what, got, want):
    if got == want:
        print("  ok    %s" % what)
    else:
        FAILURES.append(what)
        print("  FAIL  %s\n          got %r, want %r" % (what, got, want))


def capture(hwnd, path):
    """Draw a window into a PNG, sized from GetWindowRect rather than from Tk.

    The bitmap MUST be created from the WINDOW dc, not from the memory dc. A
    fresh memory dc holds a 1x1 monochrome bitmap, so CreateCompatibleBitmap
    against it hands back a monochrome bitmap and every capture comes out pure
    black -- which looks exactly like a window that failed to draw, and sent
    the first version of this hunting DWM instead of its own bug.

    Three draw calls are tried in order anyway, because which one works
    depends on how a given window paints, and the result is inspected rather
    than trusted: the first that puts a non-black pixel on the bitmap wins. A
    capture routine that cannot tell a blank frame from a real one proves
    nothing about the window it was pointed at.
    """
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return None, (w, h), "empty rect"

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h          # negative: top-down rows
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    PRF_FULL = 0x0000001E   # NONCLIENT | CLIENT | ERASEBKGND | CHILDREN
    attempts = (("PrintWindow+RENDERFULLCONTENT", PW_RENDERFULLCONTENT, False),
                ("PrintWindow", 0, False),
                ("WM_PRINT", PRF_FULL, True))
    for name, flag, use_wm_print in attempts:
        win_dc = user32.GetWindowDC(hwnd)
        mem_dc = gdi32.CreateCompatibleDC(win_dc)
        bmp = gdi32.CreateCompatibleBitmap(win_dc, w, h)
        old = gdi32.SelectObject(mem_dc, bmp)
        if use_wm_print:
            user32.SendMessageW(hwnd, 0x0317,          # WM_PRINT
                                ctypes.c_void_p(mem_dc),
                                ctypes.c_void_p(flag))
        else:
            user32.PrintWindow(hwnd, mem_dc, flag)
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem_dc, bmp, 0, h, buf, byref(bmi), 0)
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, win_dc)
        rgb = img.convert("RGB")
        if rgb.getbbox() is not None and max(rgb.getextrema())[1] > 0:
            rgb.save(path)
            return path, (w, h), name
    return None, (w, h), "every method returned black"


def windows_of_thread(tid):
    found = []

    @ENUMPROC
    def cb(hwnd, _lp):
        name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, name, 256)
        found.append((hwnd, name.value))
        return True

    user32.EnumThreadWindows(tid, cb, 0)
    return found


def child_texts(hwnd):
    out = []

    @ENUMPROC
    def cb(child, _lp):
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(child, cls, 256)
        txt = ctypes.create_unicode_buffer(1024)
        user32.GetWindowTextW(child, txt, 1024)
        out.append((cls.value, txt.value, child))
        return True

    user32.EnumChildWindows(hwnd, cb, 0)
    return out


def stub_side_effects(tmp):
    """Nothing this probe does may touch the machine it runs on."""
    br.CONFIG_DIR = tmp
    br.CONFIG_PATH = os.path.join(tmp, "config.json")
    br.LOG_PATH = os.path.join(tmp, "activity.log")
    br.ASKS_PATH = os.path.join(tmp, "asks.json")
    br.TUTORIAL_PATH = os.path.join(tmp, "tutorial.json")
    # Only what would reach OUTSIDE this process is stubbed. The savers are
    # left real on purpose: their paths are in tmp, writing there is the point
    # of the round-trip check, and a stubbed save cannot prove a setting
    # survives being written and read back.
    br.open_link = lambda *a, **k: None        # no browser, no ms-settings
    br.sync_startup = lambda *a, **k: None     # no Startup shortcut
    br.set_startup = lambda *a, **k: False     # nor from App.apply
    br.set_taskbar_identity = lambda *a, **k: None


def pump(root, seconds, until=None):
    """Run the Tk event loop for real, because after() callbacks need one.

    Returns early once `until` is true. A reminder is a chain of after()
    callbacks, so nothing in this file happens without an event loop actually
    turning -- update() rather than mainloop(), so the test keeps control.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        root.update()
        if until is not None and until():
            return True
        time.sleep(0.02)
    return bool(until()) if until is not None else True


def build_app(tmp):
    """One real App, shared by every check below. Building it is the slow part.

    Breaks are switched off here, and the timer App.__init__ already armed is
    CANCELLED rather than just disabled. A break is anchored to the wall clock
    -- on the hour and the half hour, by design -- so it fires straight
    through whatever is being tested, twice an hour, on a schedule no test
    controls.

    It is not hypothetical. CI run 37 ran at about 14:30: a break pulled a
    full-screen dim pane over the dot this file was about to photograph, the
    overlay was busy so the real pulse was skipped, and the capture came back
    as 1024x768 of solid lime. Setting break_enabled alone would not have
    helped, because the timer is armed before any of this can set it.
    """
    stub_side_effects(tmp)
    app = br.App(dict(br.DEFAULTS))
    app.cfg = dict(app.cfg, break_enabled=False)
    app.schedule_break()          # cancels the pending one, arms nothing
    app.root.update_idletasks()
    return app


# ------------------------------------------------ 1. a reminder fires
def test_reminder_fires(app, tmp):
    """The one failure that makes this product worthless, and nothing watched it.

    Not fire() in isolation -- test_timing already drives that against a
    stand-in. This is the whole chain on a real event loop: schedule() arms a
    real after(), Tk fires it, fire() logs and reaches the overlay. A bug
    anywhere along it means a reminder app that reminds nobody, silently, and
    the user's first clue is noticing weeks later that their eyes hurt.
    """
    print("\n1. a reminder actually fires")
    log = os.path.join(tmp, "activity.log")
    app.cfg = dict(app.cfg, interval_seconds=br.MIN_INTERVAL,
                   sound_enabled=False, break_enabled=False)
    before_pulses = app.overlay.pulse_id
    app.last_fire = time.monotonic()
    app.schedule()

    fired = pump(app.root, br.MIN_INTERVAL + 6,
                 lambda: app.overlay.pulse_id > before_pulses)
    check("the timer fired within %ds of being armed" % (br.MIN_INTERVAL + 6),
          fired, True)
    body = ""
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
    check("... and wrote a fire line to the log", "  fire " in body, True)
    check("... and reached the overlay", app.overlay.pulse_id > before_pulses,
          True)
    check("... and armed the next one, so it is not a one-off",
          app.timer is not None or app.overlay.busy, True)
    errs = [l for l in body.splitlines() if "  ERROR " in l]
    check("... with nothing logged as an error", errs, [])

    # Let the pulse finish, or the next check inherits a busy overlay.
    pump(app.root, 6, lambda: not app.overlay.busy)
    app.paused = True
    app.schedule()


# ----------------------------------------------- 2. the overlay draws
def test_overlay_draws(app):
    """Does the reminder put anything on the screen at all?

    pulse() returning is not the same as a pane being drawn: the panes are
    click-through, layered, overrideredirect windows, which is a stack of
    ways to end up with a window that exists and shows nothing. So a pane is
    captured and the pixels are counted.
    """
    print("\n2. the overlay draws something")
    app.paused = False
    # One long, un-faded pulse: there is no point racing a 250ms fade to the
    # shutter. blinks=1 is exempt from the flash ceiling, so hold can be long.
    cfg = br.blink_cfg(dict(app.cfg, style="dot", blinks=1, hold_ms=2500,
                            fade_ms=0, gap_ms=0, sound_enabled=False,
                            opacity=1.0))
    # pulse() returns quietly when the overlay is busy, so without this the
    # next lines photograph whatever reminder got there first and report on
    # that instead. Run 37 did exactly that and blamed the dot for a break.
    before = app.overlay.pulse_id
    app.overlay.pulse(cfg)
    check("the pulse ran rather than being skipped by a busy overlay",
          app.overlay.pulse_id > before, True)
    shown = pump(app.root, 8, lambda: bool(app.overlay.active))
    check("a pane was shown", shown, True)
    if not shown or app.overlay.pulse_id == before:
        return
    pump(app.root, 0.6)
    check("the pane on screen belongs to THIS pulse, not another reminder",
          app.overlay.cfg["style"], "dot")

    pane = app.overlay.active[0]
    path, size, how = capture(int(pane.win.frame(), 16),
                              os.path.join(OUT, "overlay.png"))
    check("the pane covers real screen area (%dx%d)" % size,
          size[0] > 100 and size[1] > 100, True)
    check("something was actually painted on it", path is not None, True)
    if path:
        from PIL import Image as _I
        img = _I.open(path).convert("RGB")
        pixels = list(img.getdata())
        lit = [px for px in pixels if px != (0, 0, 0)]
        check("the painted area is a mark, not the whole screen",
              0 < len(lit) < len(pixels), True)
        # A dot fills pi/4 of its own bounding box, so roughly 79% of the
        # pane. Checked loosely: the point is that a SHAPE was drawn, not a
        # full rectangle (which is what a pane painted with no mark looks
        # like) and not a few stray pixels.
        share = len(lit) / float(len(pixels))
        check("it is dot-shaped (%.0f%% of the pane, a disc is ~79%%)"
              % (share * 100), 0.5 < share < 0.95, True)
        # And it is the colour the config asked for. "Something was painted"
        # would still pass if the reminder drew the wrong thing entirely.
        want = cfg["colour"].lstrip("#")
        want = tuple(int(want[i:i + 2], 16) for i in (0, 2, 4))
        common = max(set(lit), key=lit.count)
        near = all(abs(a - b) <= 8 for a, b in zip(common, want))
        check("it is painted in the configured colour (%s, drew %s)"
              % (cfg["colour"], "#%02x%02x%02x" % common), near, True)
        print("  captured %s %s via %s (%d lit pixels)"
              % (path, size, how, len(lit)))

    pump(app.root, 8, lambda: not app.overlay.busy)
    check("the pulse released the overlay when it finished",
          app.overlay.busy, False)


# ---------------------------------------------------- 3. the button
def test_startup_button(app):
    print("\n3. the Startup button, rendered by the real panel")
    # Forced AFTER construction: the panel decides the label in open(), and
    # this keeps PACKAGED out of App.__init__'s startup handling.
    br.PACKAGED = True
    br.PACKAGE_FAMILY = "KennyTechy.BlinkRestReminder_ndvpvnpyhp88g"
    br.packaged_startup_on = lambda: True

    app.settings.open()
    win = app.settings.win
    win.update_idletasks()
    win.update()
    button = app.settings.tog_startup

    check("the panel built a Button, not the switch",
          button.winfo_class(), "TButton")
    check("it carries the ON label from startup_button_text()",
          button.cget("text"), "Starting with Windows: ON")
    fits = button.winfo_reqwidth() <= br.SettingsWindow.STARTUP_BUTTON_W
    check("it fits the slot (%dpx needed of %dpx)"
          % (button.winfo_reqwidth(), br.SettingsWindow.STARTUP_BUTTON_W),
          fits, True)

    # refresh_startup_button has never executed. Flip the state underneath it
    # and re-run it, the way <Activate> does when the user comes back from
    # the Windows Settings page the button sent them to.
    br.packaged_startup_on = lambda: False
    app.settings.refresh_startup_button()
    win.update_idletasks()
    check("refresh_startup_button re-reads the state and relabels",
          button.cget("text"), "Starting with Windows: OFF")

    br.packaged_startup_on = lambda: True
    app.settings.refresh_startup_button()
    win.update_idletasks()
    check("... and back again", button.cget("text"),
          "Starting with Windows: ON")

    # frame(), not winfo_id(): the frame is the whole window, the id is only
    # the client area, and GetWindowRect on the client leaves the title bar
    # out of the bitmap.
    path, size, how = capture(int(win.frame(), 16),
                              os.path.join(OUT, "panel.png"))
    print("  captured %s %s via %s" % (path, size, how))
    return app


# ------------------------------------------- 4. settings round-trip
def test_settings_roundtrip(app, tmp):
    """Does every setting the panel collects survive being saved and reloaded?

    The expensive failure is not a crash, it is a key that quietly does not
    make the journey: the panel shows it, Save writes the file, and the value
    that comes back is the old one or the default. The user changes a setting,
    it appears to take, and it is gone next launch -- with nothing in the log,
    because nothing went wrong.

    break_message, break_hold_ms and break_fade_ms were stored and written on
    every Save with no control to edit them, which collect()'s own docstring
    calls out. This is the check that would have noticed.
    """
    print("\n4. settings survive a save and a reload")
    panel = app.settings
    before = panel.collect()

    # Driven through a control, not by writing cfg: collect() reading the
    # widget is half of what is under test.
    was = panel._int(panel.v_every, 1)
    panel.v_every.set(was + 7)
    after = panel.collect()
    check("collect() reads the change back off the control",
          after["interval_seconds"] != before["interval_seconds"], True)

    panel.save()
    app.root.update_idletasks()
    check("saving wrote the file", os.path.exists(br.CONFIG_PATH), True)

    reloaded = br.load_config()
    lost = sorted(k for k, v in after.items()
                  if k not in reloaded or reloaded[k] != v)
    check("every key the panel collected came back unchanged", lost, [])
    check("... including the one that was edited",
          reloaded["interval_seconds"], after["interval_seconds"])

    # A damaged file must cost the settings, not the app. Nothing else in the
    # suite covers config.json specifically -- test_asks and test_tutorial
    # cover their own files.
    with open(br.CONFIG_PATH, "w", encoding="utf-8") as fh:
        fh.write("{not json at all")
    fallback = br.load_config()
    check("a damaged config.json falls back instead of raising",
          fallback.get("interval_seconds"), br.DEFAULTS["interval_seconds"])
    check("... and still hands back every key the app expects",
          sorted(set(br.DEFAULTS) - set(fallback)), [])


# ---------------------------------------------------- 5. the dialog
def test_crash_dialog():
    print("\n5. the crash dialog, actually displayed")
    os.environ.pop("BLINK_NO_CRASH_DIALOG", None)
    text = ('Traceback (most recent call last):\n'
            '  File "blink_reminder.py", line 6019, in build_tray\n'
            '    img = app_icon(64)\n'
            "ImportError: cannot import name '_imagingft' from 'PIL'")
    box = {}

    def show():
        box["tid"] = kernel32.GetCurrentThreadId()
        # Blocks until something closes it, which is why it is on a thread.
        br.report_startup_failure(text)
        box["returned"] = True

    worker = threading.Thread(target=show, daemon=True)
    worker.start()

    hwnd = None
    for _ in range(80):
        time.sleep(0.1)
        tid = box.get("tid")
        if tid:
            for h, cls in windows_of_thread(tid):
                if cls == "#32770":          # the dialog class
                    hwnd = h
                    break
        if hwnd:
            break

    check("a dialog actually appeared", bool(hwnd), True)
    if not hwnd:
        return

    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title, 512)
    kids = child_texts(hwnd)
    body = "\n".join(t for _c, t, _h in kids if t and "Static" in _c) or \
           "\n".join(t for _c, t, _h in kids)
    check("it is titled with the app's name", title.value, br.DISPLAY_NAME)
    check("it says the app could not start",
          "could not start" in body, True)
    check("it names the log file so a user can send it",
          br.LOG_PATH in body, True)
    check("it carries the error's own last line",
          "_imagingft" in body, True)

    path, size, how = capture(hwnd, os.path.join(OUT, "crash.png"))
    print("  captured %s %s via %s" % (path, size, how))
    print("  --- the text a user would read ---")
    for line in body.splitlines():
        print("    " + line)

    # Close it: WM_CLOSE first, then the OK button if the box ignores it.
    user32.PostMessageW(hwnd, WM_CLOSE, None, None)
    for _ in range(20):
        time.sleep(0.1)
        if box.get("returned"):
            break
    if not box.get("returned"):
        for _c, _t, child in kids:
            if _c == "Button":
                user32.SendMessageW(child, BM_CLICK, None, None)
        time.sleep(0.5)
    check("it can be dismissed", bool(box.get("returned")), True)


def main():
    global OUT
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="blink-test-ui-")
    OUT = tmp
    try:
        # One App for all four window checks: building it is the slow part,
        # and each check leaves it in a state the next one can use.
        app = build_app(tmp)
        test_reminder_fires(app, tmp)
        test_overlay_draws(app)
        test_startup_button(app)
        test_settings_roundtrip(app, tmp)
        test_crash_dialog()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
