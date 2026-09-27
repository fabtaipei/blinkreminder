"""
Build a standalone Blink Reminder.exe.

    py build.py

Produces dist/Blink Reminder.exe, a single file with no dependency on Python
being installed. Everything it needs (the icon, the version resource) is
generated here, so the repo stays down to two source files.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# The FILE name: deliberately without the ampersand. "&" is legal in a Windows
# filename but it is a separator in cmd, a metacharacter in a URL, and a
# reliable source of quoting bugs in anything that touches the path as text.
NAME = "Dry Eyes Blink Reminder Lite"
# The name people read, and the name reserved in Partner Center. The MSIX
# DisplayName is matched against that reservation character for character --
# copy it exactly, trailing punctuation and all, rather than retyping it.
DISPLAY = "Dry Eyes Blink Reminder Lite"
VERSION = (1, 1, 3, 0)
ICON = os.path.join(HERE, "build", "app.ico")
VERSION_FILE = os.path.join(HERE, "build", "version.txt")
ENTRY = os.path.join(HERE, "blink_reminder.py")
BUILD_INFO = os.path.join(HERE, "build", "BUILD_INFO.json")

# What PyInstaller must NOT bundle. Its analysis is deliberately conservative
# -- it would rather ship a megabyte nobody needs than miss an import -- so
# everything below was measured inside a built .msix, confirmed unreachable
# from this app's own imports, and confirmed harmless to remove by running the
# app and the full suite afterwards. Compressed sizes are what each one cost
# in the 21.04MB package of 1.1.2.0.
EXCLUDES = (
    # Never referenced. Large scientific/UI stacks Pillow and the stdlib can
    # drag in through optional code paths.
    "numpy", "scipy", "pandas", "matplotlib", "pytest", "setuptools",
    "pip", "unittest", "pydoc_data", "PIL.ImageQt", "PyQt5", "PySide2",

    # AVIF decoder, 4.39MB. The app draws its icon with ImageDraw and reads
    # nothing but its own PNGs; it has never opened an AVIF file.
    "PIL.AvifImagePlugin",

    # FreeType text rendering, 1.07MB. Every string the app draws goes through
    # a Tk canvas, not Pillow. Excluding PIL.ImageFont itself would break the
    # build -- ImageDraw imports it at module level -- but the C extension
    # underneath is only imported under TYPE_CHECKING and lazily inside the
    # text functions, so dropping it leaves shape drawing untouched.
    "PIL._imagingft",

    # OpenSSL, 2.19MB across libcrypto-3.dll and libssl-3.dll, pulled in as a
    # binary dependency of these two extensions. The app opens no sockets and
    # imports neither -- see the privacy policy, which promises exactly that.
    # hashlib itself is deliberately NOT excluded: it falls back to CPython's
    # built-in digests when _hashlib is missing, and random imports it.
    "ssl", "_ssl", "_hashlib",
)

# What each build produces, and where. Named here so --check can ask about an
# artifact without rebuilding it, and so nothing has to remember these paths.
ARTIFACTS = {
    "exe": os.path.join(HERE, "dist", NAME + ".exe"),
    "folder": os.path.join(HERE, "dist-dir", NAME),
    "msix-layout": os.path.join(HERE, "dist-msix", "layout"),
}


def source_fingerprint():
    """SHA-256 of the app's source, which is what "which version is this?" means.

    The app is one file, so one hash is the whole answer. Deliberately NOT
    including build.py: changing how the exe is packaged does not change what
    the app does, and a fingerprint that moves for unrelated reasons trains you
    to ignore it.

    Hashed from the bytes on disk rather than from a version number, because a
    version number only changes when someone remembers to change it -- which is
    exactly the failure this is here to catch.
    """
    with open(ENTRY, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def in_use(path):
    """True if a built artifact is locked, which on Windows means it is running.

    Asked by trying to open it for writing rather than by enumerating
    processes: that is the same question the build is about to ask the
    filesystem, so it cannot disagree with reality, and it needs no extra API.
    Windows lets you READ a running exe but never write to a mapped image.
    """
    try:
        with open(path, "r+b"):
            return False
    except PermissionError:
        return True
    except OSError:
        return False


def refuse_if_running(onefile):
    """Stop before PyInstaller does, with an error that names the cause.

    Left to itself PyInstaller fails halfway through clearing the output
    directory and reports "PermissionError: [WinError 5] Access is denied" on
    some file inside _internal/PIL -- a file nobody has heard of, raised from
    inside shutil, with no mention of the app being open. Every minute spent
    reading that traceback is a minute spent on the wrong problem.
    """
    exe = (ARTIFACTS["exe"] if onefile
           else os.path.join(ARTIFACTS["folder"], NAME + ".exe"))
    if os.path.exists(exe) and in_use(exe):
        sys.exit(
            "\n%s is running, so this build cannot overwrite it."
            "\n  Quit it from the tray icon (right-click > Quit), then build"
            " again."
            "\n  The copy you are running is from the PREVIOUS build."
            % exe)


def read_build_info():
    try:
        with open(BUILD_INFO, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def record_build(kind, fingerprint):
    """Remember what source went into an artifact, so --check can compare."""
    info = read_build_info()
    info[kind] = {
        "source_sha256": fingerprint,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "path": ARTIFACTS.get(kind, ""),
    }
    os.makedirs(os.path.dirname(BUILD_INFO), exist_ok=True)
    with open(BUILD_INFO, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=2)


def freshness():
    """(kind, state, detail) for every artifact. state is fresh/stale/missing."""
    now = source_fingerprint()
    info = read_build_info()
    rows = []
    for kind, path in ARTIFACTS.items():
        if not os.path.exists(path):
            rows.append((kind, "missing", "not built"))
            continue
        rec = info.get(kind)
        if not rec:
            # It exists but predates this bookkeeping, so its provenance is
            # genuinely unknown. Unknown is reported as stale on purpose: the
            # whole point is to never ship something you cannot vouch for.
            rows.append((kind, "stale", "built before builds were stamped"))
        elif rec.get("source_sha256") != now:
            rows.append((kind, "stale",
                         "built %s from source %s"
                         % (rec.get("built_at", "?"),
                            str(rec.get("source_sha256"))[:12])))
        else:
            rows.append((kind, "fresh", "built " + rec.get("built_at", "?")))
    return rows


def report_freshness(header="build freshness"):
    """Print the table, and say whether anything is safe to hand to someone."""
    rows = freshness()
    print("\n%s  (source %s)" % (header, source_fingerprint()[:12]))
    for kind, state, detail in rows:
        mark = {"fresh": "  fresh  ", "stale": "  STALE  ",
                "missing": " missing "}[state]
        print("  %-12s %s %s" % (kind, mark, detail))
    stale = [k for k, s, _d in rows if s == "stale"]
    if stale:
        print("  -> do NOT share %s. Rebuild first." % ", ".join(stale))
    return rows


def make_icon():
    """Bake the app's own mark into the .ico, at every size Windows asks for.

    Imported from the app rather than redrawn here. These were two separate
    drawings with two sets of proportions, which meant the icon on the exe was
    never quite the icon in the window -- a difference nobody would report as a
    bug and everybody would faintly notice.

    Each size is rendered at its own resolution rather than letting Pillow
    downscale one 256px master: the 16px ring needs to be drawn as 16px to
    survive, which is what app_icon's supersampling is for.
    """
    import blink_reminder

    os.makedirs(os.path.dirname(ICON), exist_ok=True)
    sizes = (256, 128, 64, 48, 32, 16)
    frames = [blink_reminder.app_icon(n) for n in sizes]
    frames[0].save(ICON, format="ICO", sizes=[(n, n) for n in sizes],
                   append_images=frames[1:])
    return ICON


def make_version_file():
    """Give the exe real file properties. An unsigned binary with no metadata
    at all is the shape most likely to trip antivirus heuristics.

    Also stamps the source fingerprint into Comments, which is the only part of
    this that travels. A four-part version number changes when someone
    remembers to change it; the hash changes when the code does. Once the exe
    is on someone else's machine that field is the ONLY way either of you can
    answer "which build is this?" -- right-click > Properties > Details.
    """
    vers = "%d, %d, %d, %d" % VERSION
    dotted = "%d.%d.%d.%d" % VERSION
    stamp = "source %s built %s" % (source_fingerprint()[:12],
                                   time.strftime("%Y-%m-%d %H:%M"))
    body = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(%(vers)s),
    prodvers=(%(vers)s),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('Comments', '%(stamp)s'),
         StringStruct('FileDescription', '%(display)s'),
         StringStruct('FileVersion', '%(dotted)s'),
         StringStruct('InternalName', 'BlinkReminder'),
         StringStruct('OriginalFilename', '%(exe)s'),
         StringStruct('ProductName', '%(display)s'),
         StringStruct('ProductVersion', '%(dotted)s')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""" % {"vers": vers, "dotted": dotted, "stamp": stamp,
           # Substituted rather than written out, because these were literals
           # in six places and the rename found every one of them stale.
           "display": DISPLAY, "exe": NAME + ".exe"}
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8") as fh:
        fh.write(body)
    return VERSION_FILE


def build(onefile=True):
    """Build the app. onefile=False gives a folder, which is what MSIX wants.

    A one-file exe unpacks itself into %TEMP% on every launch. Inside an MSIX
    package that is a container inside a container: it still runs, but it pays
    the unpack cost every single time for no benefit, since the package already
    IS the single file the user downloads. The folder build starts far faster
    and is what Microsoft's own packaging guidance assumes.
    """
    # Read once, before PyInstaller runs, so the hash stamped into the exe and
    # the hash recorded afterwards are the same hash even if the source is
    # edited mid-build.
    refuse_if_running(onefile)
    fingerprint = source_fingerprint()
    make_icon()
    make_version_file()

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile" if onefile else "--onedir",
        "--windowed",                      # no console window ever appears
        "--name", NAME,
        "--icon", ICON,
        "--version-file", VERSION_FILE,
        "--workpath",
        os.path.join(HERE, "build", "work" if onefile else "work-dir"),
        "--specpath", os.path.join(HERE, "build"),
        "--distpath", os.path.join(HERE, "dist" if onefile else "dist-dir"),
        "--hidden-import", "pystray._win32",  # backend is picked at runtime
        "--collect-submodules", "pystray",
    ]
    for mod in EXCLUDES:
        args += ["--exclude-module", mod]
    args.append(ENTRY)

    print("running:", " ".join(args[1:]))
    result = subprocess.run(args, cwd=HERE)
    if result.returncode != 0:
        sys.exit("PyInstaller failed with %d" % result.returncode)

    if onefile:
        exe = ARTIFACTS["exe"]
        print("\nbuilt: %s  (%.1f MB)"
              % (exe, os.path.getsize(exe) / 1e6))
        record_build("exe", fingerprint)
        report_freshness()
        return exe
    folder = ARTIFACTS["folder"]
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _d, fs in os.walk(folder) for f in fs)
    print("\nbuilt: %s  (%.1f MB in the folder)" % (folder, total / 1e6))
    record_build("folder", fingerprint)
    return folder


if __name__ == "__main__":
    if "--check" in sys.argv:
        # The "am I about to send someone the old app?" command.
        rows = report_freshness("what is currently built")
        sys.exit(1 if any(s == "stale" for _k, s, _d in rows) else 0)
    build(onefile="--onedir" not in sys.argv)
