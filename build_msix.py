"""
Build Blink Reminder as an MSIX package for the Microsoft Store.

    py build_msix.py                 layout + manifest + assets, and pack if it can
    py build_msix.py --no-build      reuse the last PyInstaller folder build
    py build_msix.py --sign          also sign it, for sideloading on your own PC

Three things the Store needs that a plain .exe does not:

  1. A manifest. AppxManifest.xml declares the identity, the icons and, most
     importantly here, the startup task -- see STARTUP below.
  2. Tile images at fixed sizes. Generated from the same eye that build.py
     draws for the .ico, so the two can never drift apart.
  3. A package. makeappx.exe zips the layout into a signed .msix.

Only the third needs anything installed. Without the Windows SDK this script
still produces a complete, registerable package LAYOUT -- which is all you need
to test on your own machine, because Windows can register a loose folder
directly (see the instructions it prints).

--------------------------------------------------------------------------
STARTUP -- the reason this file exists at all
--------------------------------------------------------------------------
The app's own "Start with Windows" switch writes a shortcut into the user's
Startup folder. A packaged app is not allowed to: the write is redirected into
the package's private store, where Windows never looks. It does not fail, it
does not log, it just silently does nothing -- a tickbox that lies.

Packaged, startup is DECLARED here instead, in the manifest, with Enabled="true".
Note what that does NOT mean: per Microsoft's own StartupTask documentation the
user "must either launch the app at least once, or they must enable startup
functionality for the app on the Startup page in Settings" -- so a fresh install
does not silently start with Windows, and the first launch is what arms it.
After that the switch belongs to the user in Task Manager > Startup apps, and
the app cannot take it back from the DisabledByUser state.
blink_reminder.py detects the packaged build and turns its own switch into a
link to the page that really decides.

--------------------------------------------------------------------------
IDENTITY -- change these before you submit
--------------------------------------------------------------------------
Partner Center reserves your app name and then shows you the exact Identity
Name, Publisher and PublisherDisplayName to paste in. Until then these are
placeholders that work for local sideloading only.
"""

import os
import re
import shutil
import subprocess
import sys

import build as appbuild
import blink_i18n

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dist-msix")
LAYOUT = os.path.join(OUT, "layout")
ASSETS = os.path.join(LAYOUT, "Assets")

# ---- identity ------------------------------------------------------------
# These three are assigned by Partner Center when the product name is reserved,
# and they are not negotiable: the Store rejects any upload whose identity does
# not match, character for character. Copied from
# Partner Center > Blink & Rest Reminder > View product identity.
IDENTITY_NAME = "KennyTechy.BlinkRestReminder"
PUBLISHER = "CN=1AB756B7-EDA5-435A-B4BA-3D72DAA092BE"
PUBLISHER_DISPLAY = "KennyTechy"

# Not used by the build, recorded because they are otherwise only findable by
# logging in. The PFN is what names the app's private data folder inside the
# container -- %LOCALAPPDATA%\Packages\<PFN>\LocalCache\Roaming\BlinkReminder
# -- which is where a packaged install's settings and log actually live.
PACKAGE_FAMILY_NAME = "KennyTechy.BlinkRestReminder_ndvpvnpyhp88g"
STORE_ID = "9NBRV5W24KH5"

# Four parts, and the Store requires the last to be 0 -- it reserves the
# revision field for itself. Taken from build.py so there is one version number.
VERSION = "%d.%d.%d.0" % appbuild.VERSION[:3]

# The name shown on the tile, in the app list and in Task Manager. It appears
# in three places in the manifest and used to be a literal in all three, which
# is three chances to rename two of them.
#
# XML-escaped on the way in. The name no longer carries an ampersand, but the
# escaping stays: a raw "&" in XML starts an entity reference, and makeappx
# would fail with a parser error that says nothing about the name. The next
# rename should not have to rediscover that.
DISPLAY_NAME = "Dry Eyes Blink Reminder Lite"
DESCRIPTION = ("A quiet reminder to blink, and to rest your eyes, "
               "on every screen.")

EXE = "BlinkReminder.exe"          # no space: simpler to quote everywhere
STARTUP_TASK_ID = "BlinkReminderStartup"   # must match blink_reminder.py

# The language the app is WRITTEN in, which needs no entry in the translation
# table and so cannot be derived from it. en-gb rather than en-us: the copy is
# British throughout -- "colour", "centre".
BASE_LANGUAGE = "en-gb"


def supported_languages():
    """Every language the app actually speaks, base first.

    Read from blink_i18n rather than typed here. These two lists have to be
    identical -- a language declared in the manifest and missing from the
    table is the Store advertising something the app cannot do, and the user
    who believed it leaves the review -- and the only way to keep two lists
    identical is to have one list.
    """
    return [BASE_LANGUAGE] + sorted(blink_i18n.STRINGS)

def xml_attr(text):
    """Escape a string for use inside an XML attribute or element."""
    from xml.sax.saxutils import escape
    return escape(text, {'"': "&quot;", "'": "&apos;"})


MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:uap5="http://schemas.microsoft.com/appx/manifest/uap/windows10/5"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  IgnorableNamespaces="uap uap5 rescap">

  <Identity Name="%(identity)s"
            Publisher="%(publisher)s"
            Version="%(version)s"
            ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>%(display)s</DisplayName>
    <PublisherDisplayName>%(publisher_display)s</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
  </Properties>

  <Dependencies>
    <!-- 17763 is 1809, the Store's own floor for MSIX; uap5:StartupTask needs
         only 16299. MaxVersionTested tracks the SDK actually used to pack,
         because a package tested against an older release is held in that
         release's quirks mode on everything newer. -->
    <TargetDeviceFamily Name="Windows.Desktop"
                        MinVersion="10.0.17763.0"
                        MaxVersionTested="10.0.26100.0" />
  </Dependencies>

  <Resources>
    <!-- Every language the APP itself speaks. The Store reads this to fill
         in "Supported languages" and to decide whose search results this can
         appear in. GENERATED by supported_languages() from the table in
         blink_i18n, so it cannot fall behind what the app was translated
         into. No .pri file is involved: a full-trust Win32 app carries its
         own strings, and this element is a declaration, not a resource
         index. (Note for editors: a double hyphen is illegal inside an XML
         comment, and makeappx reports it as a parser error with no line
         number worth reading.) -->
%(resources)s
  </Resources>

  <Applications>
    <Application Id="App"
                 Executable="%(exe)s"
                 EntryPoint="Windows.FullTrustApplication">
      <!-- A neutral plate, not the mark's own colour. The tile is the one place
           the background is ours to choose, and a dark one lets the warm core
           of the mark do the work exactly as it does on a dark title bar. -->
      <uap:VisualElements
          DisplayName="%(display)s"
          Description="%(description)s"
          BackgroundColor="#2B2B2B"
          Square150x150Logo="Assets\\Square150x150Logo.png"
          Square44x44Logo="Assets\\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\\Wide310x150Logo.png"
                         Square71x71Logo="Assets\\Square71x71Logo.png"
                         Square310x310Logo="Assets\\Square310x310Logo.png" />
      </uap:VisualElements>
      <Extensions>
        <!-- The whole point. Enabled="true" starts with Windows on a fresh
             install; after that the user owns it in Task Manager. -->
        <uap5:Extension Category="windows.startupTask"
                        Executable="%(exe)s"
                        EntryPoint="Windows.FullTrustApplication">
          <uap5:StartupTask TaskId="%(task)s"
                            Enabled="true"
                            DisplayName="%(display)s" />
        </uap5:Extension>
      </Extensions>
    </Application>
  </Applications>

  <Capabilities>
    <!-- Every Win32 app in the Store declares this. It is a restricted
         capability, so Partner Center asks what you need it for: "packaged
         desktop application" is the answer, and it is granted as a matter of
         course for exactly this case. -->
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
"""

# (filename, width, height). Square sizes come with a scale-200 twin so the
# icon stays sharp on a 200% display, which is most laptops now.
TILES = [
    ("StoreLogo.png", 50, 50),
    ("StoreLogo.scale-200.png", 100, 100),
    ("Square44x44Logo.png", 44, 44),
    ("Square44x44Logo.scale-200.png", 88, 88),
    # The unplated variant is what the taskbar and Start's app list use. Without
    # it Windows falls back to the plated one and draws your icon on a coloured
    # square that fights the taskbar.
    ("Square44x44Logo.targetsize-24_altform-unplated.png", 24, 24),
    ("Square44x44Logo.targetsize-48_altform-unplated.png", 48, 48),
    ("Square71x71Logo.png", 71, 71),
    ("Square150x150Logo.png", 150, 150),
    ("Square150x150Logo.scale-200.png", 300, 300),
    ("Square310x310Logo.png", 310, 310),
    ("Wide310x150Logo.png", 310, 150),
    ("Wide310x150Logo.scale-200.png", 620, 300),
]


def draw_eye(w, h):
    """The app's own mark, centred in any rectangle.

    Imported rather than redrawn -- this was the third copy of the artwork.
    A wide tile gets the mark centred at its full height rather than stretched
    to fill, because a stretched logo is the thing that makes a Store listing
    look like it was thrown together.
    """
    from PIL import Image
    import blink_reminder

    if w == h:
        return blink_reminder.app_icon(w)
    side = min(w, h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.alpha_composite(blink_reminder.app_icon(side),
                        ((w - side) // 2, (h - side) // 2))
    return img


def make_assets():
    os.makedirs(ASSETS, exist_ok=True)
    for name, w, h in TILES:
        draw_eye(w, h).save(os.path.join(ASSETS, name), format="PNG")
    print("assets:   %d tile images in %s" % (len(TILES), ASSETS))


def render_manifest():
    """The manifest as text. The ONLY place the substitution dict is written.

    make_manifest writes this to disk; the tests parse it. When they each built
    their own dict the test silently fell behind the template -- adding the
    display name to the manifest broke a suite that was checking the manifest.
    """
    return MANIFEST % {
        "resources": "\n".join('    <Resource Language="%s" />' % xml_attr(code)
                               for code in supported_languages()),
        "identity": IDENTITY_NAME,
        "publisher": PUBLISHER,
        "publisher_display": PUBLISHER_DISPLAY,
        "version": VERSION,
        "exe": EXE,
        "task": STARTUP_TASK_ID,
        "display": xml_attr(DISPLAY_NAME),
        "description": xml_attr(DESCRIPTION),
    }


def make_manifest():
    body = render_manifest()
    path = os.path.join(LAYOUT, "AppxManifest.xml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    print("manifest: %s  (identity %s, version %s)"
          % (path, IDENTITY_NAME, VERSION))
    print("languages: %s" % ", ".join(supported_languages()))
    return path


def find_sdk_tool(name):
    """Newest Windows SDK copy of a tool, or None.

    The SDK installs one copy per version under bin/<version>/<arch>/, and the
    versions sort as text well enough because they are all 10.0.x.y.
    """
    roots = [os.path.join(os.environ.get(v, ""), "Windows Kits", "10", "bin")
             for v in ("ProgramFiles(x86)", "ProgramFiles")]
    found = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for version in sorted(os.listdir(root), reverse=True):
            for arch in ("x64", "x86"):
                cand = os.path.join(root, version, arch, name)
                if os.path.exists(cand):
                    found.append(cand)
    return found[0] if found else None


def make_layout(folder):
    """Copy the PyInstaller folder build in, renaming the exe."""
    if os.path.isdir(LAYOUT):
        shutil.rmtree(LAYOUT)
    shutil.copytree(folder, LAYOUT)
    src = os.path.join(LAYOUT, appbuild.NAME + ".exe")
    if os.path.exists(src):
        os.replace(src, os.path.join(LAYOUT, EXE))
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _d, fs in os.walk(LAYOUT) for f in fs)
    print("layout:   %s  (%.1f MB)" % (LAYOUT, total / 1e6))


def pack():
    makeappx = find_sdk_tool("makeappx.exe")
    msix = os.path.join(OUT, "BlinkReminder-%s.msix" % VERSION)
    if makeappx is None:
        return None, msix
    if os.path.exists(msix):
        os.remove(msix)
    result = subprocess.run([makeappx, "pack", "/o", "/d", LAYOUT, "/p", msix])
    if result.returncode != 0:
        sys.exit("makeappx failed with %d" % result.returncode)
    print("packed:   %s  (%.1f MB)" % (msix, os.path.getsize(msix) / 1e6))
    return msix, msix


def sign(msix):
    """Self-sign, for installing on your own machine. Not for the Store.

    The Store signs your upload with its own certificate; you never sign a
    submission yourself. This exists only so you can install the package here
    and check that the startup task really appears in Task Manager.
    """
    signtool = find_sdk_tool("signtool.exe")
    if signtool is None:
        print("sign:     skipped, no signtool.exe")
        return
    pfx = os.path.join(OUT, "dev-cert.pfx")
    if not os.path.exists(pfx):
        print("sign:     skipped, no %s" % pfx)
        print("          make one (PowerShell, as you):")
        print('            $c = New-SelfSignedCertificate -Type Custom '
              '-Subject "%s" `' % PUBLISHER)
        print('                 -KeyUsage DigitalSignature -FriendlyName '
              '"Blink Reminder dev" `')
        print('                 -CertStoreLocation "Cert:\\CurrentUser\\My" `')
        print('                 -TextExtension '
              '@("2.5.29.37={text}1.3.6.1.5.5.7.3.3","2.5.29.19={text}")')
        print('            $p = ConvertTo-SecureString -String "blink" '
              '-Force -AsPlainText')
        print('            Export-PfxCertificate -cert $c -FilePath "%s" '
              '-Password $p' % pfx)
        return
    subprocess.run([signtool, "sign", "/fd", "SHA256", "/a",
                    "/f", pfx, "/p", "blink", msix], check=False)
    print("sign:     signed with %s" % pfx)


def check_manifest_matches_app():
    """The task id lives in two files. Catch a drift here, not at submission."""
    src = os.path.join(HERE, "blink_reminder.py")
    with open(src, encoding="utf-8") as fh:
        found = re.search(r'STARTUP_TASK_ID\s*=\s*"([^"]+)"', fh.read())
    if found and found.group(1) != STARTUP_TASK_ID:
        sys.exit("TaskId mismatch: manifest %r vs blink_reminder.py %r"
                 % (STARTUP_TASK_ID, found.group(1)))


def main():
    check_manifest_matches_app()
    os.makedirs(OUT, exist_ok=True)

    if "--no-build" in sys.argv:
        folder = appbuild.ARTIFACTS["folder"]
        if not os.path.isdir(folder):
            sys.exit("no folder build at %s -- run without --no-build" % folder)
        # Refusing rather than warning. --no-build exists to save a minute, and
        # a minute is never worth packaging yesterday's code into something you
        # are about to upload to a store under your own name.
        state = dict((k, s) for k, s, _d in appbuild.freshness())["folder"]
        if state != "fresh":
            sys.exit("the folder build is %s -- drop --no-build and rebuild"
                     % state)
    else:
        folder = appbuild.build(onefile=False)

    make_layout(folder)
    make_assets()
    make_manifest()
    # The layout is a copy of the folder build plus assets, so it is exactly as
    # fresh as the source that went into it.
    appbuild.record_build("msix-layout", appbuild.source_fingerprint())
    appbuild.report_freshness()
    msix, wanted = pack()
    if msix and "--sign" in sys.argv:
        sign(msix)

    print()
    if msix is None:
        print("No makeappx.exe on this machine, so no .msix was produced.")
        print("The layout above is complete and is all you need to TEST:")
        print()
        print("  1. Settings > System > For developers > Developer Mode: on")
        print("  2. PowerShell:")
        print("       Add-AppxPackage -Register '%s'"
              % os.path.join(LAYOUT, "AppxManifest.xml"))
        print("  3. Check Task Manager > Startup apps for 'Blink Reminder'.")
        print("     That entry IS the fix -- it is what the in-app switch")
        print("     could never create.")
        print("  4. Remove it again with:")
        print("       Get-AppxPackage *%s* | Remove-AppxPackage" % IDENTITY_NAME)
        print()
        print("To produce the .msix you upload to the Store, install the")
        print("Windows SDK (winget install Microsoft.WindowsSDK) and re-run.")
    else:
        print("Next: reserve the name in Partner Center, paste the Identity")
        print("Name, Publisher and PublisherDisplayName it gives you into the")
        print("constants at the top of this file, re-run, and upload %s."
              % os.path.basename(wanted))


if __name__ == "__main__":
    main()
