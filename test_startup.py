"""Who owns "start with Windows", and what the panel says about it.

    py test_startup.py

Three things are tested here:

  1. THE STATE.  A packaged build reads the startup task's state out of the
     registry and answers on/off. Every way that read can fail answers ON,
     because the manifest declares the task enabled and the opposite default
     would tell a user their reminders are off while they are running.

  2. THE LABEL.  The wide Startup button answers the question the user came
     with -- does it start or not -- rather than naming who owns the decision:
     ON when Windows is starting us, OFF when it is not, and OFF too when an
     unpackaged build's Startup entry has been switched off.

  3. NO TRANSLATION DEBT.  Both labels must be real keys in all 29 languages.
     This fails the day someone "improves" the wording without translating
     it, because T() falls back to the English key and would quietly show
     English to everybody who does not read it.

No window is opened and no Tk root is created: winreg is replaced with a
stand-in, so the states a real machine would take weeks to produce are all
reachable here.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import blink_reminder as br
import blink_i18n

FAILURES = []

ON = "Starting with Windows: ON"
OFF = "Starting with Windows: OFF"


def check(what, got, want):
    if got == want:
        print("  ok    %s" % what)
    else:
        FAILURES.append(what)
        print("  FAIL  %s\n          got %r, want %r" % (what, got, want))


class FakeWinreg(object):
    """Enough of winreg to answer one QueryValueEx, or to fail like winreg.

    packaged_startup_on does a local `import winreg`, so putting this in
    sys.modules is all it takes -- no patching of the module under test.
    """

    HKEY_CURRENT_USER = "HKCU"

    def __init__(self, state=None, raises=None):
        self.state = state
        self.raises = raises
        self.asked = []

    def OpenKey(self, root, path):
        self.asked.append(path)
        if self.raises is not None:
            raise self.raises
        fake = self

        class Key(object):
            def __enter__(self_inner):
                return fake

            def __exit__(self_inner, *exc):
                return False

        return Key()

    def QueryValueEx(self, key, name):
        if self.raises is not None:
            raise self.raises
        return self.state, 4


def with_winreg(fake):
    sys.modules["winreg"] = fake
    return fake


def test_state():
    print("\n1. the state")
    br.PACKAGED = True
    br.PACKAGE_FAMILY = "KennyTechy.BlinkRestReminder_ndvpvnpyhp88g"

    # StartupTaskState: 0 Disabled, 1 DisabledByUser, 2 Enabled,
    # 3 DisabledByPolicy, 4 EnabledByPolicy.
    for state, want, name in ((2, True, "Enabled"),
                              (4, True, "EnabledByPolicy"),
                              (0, False, "Disabled"),
                              (1, False, "DisabledByUser"),
                              (3, False, "DisabledByPolicy")):
        with_winreg(FakeWinreg(state=state))
        check("state %d (%s) reads as %s"
              % (state, name, "on" if want else "off"),
              br.packaged_startup_on(), want)

    fake = with_winreg(FakeWinreg(state=2))
    br.packaged_startup_on()
    check("it asks about this package's own task, by family and task id",
          fake.asked[0].endswith(
              "%s\\%s" % (br.PACKAGE_FAMILY, br.STARTUP_TASK_ID)), True)

    # Every failure answers ON. An undocumented key may move; mislabelling a
    # button is survivable, telling someone their reminders are off is not.
    for raises, why in ((OSError("no such key"), "no key at all"),
                        (OSError("access denied"), "a key it cannot read"),
                        (ValueError("not an int"), "a value that is not a number"),
                        (TypeError("None"), "a value of the wrong type")):
        with_winreg(FakeWinreg(raises=raises))
        check("%s still answers on" % why, br.packaged_startup_on(), True)

    with_winreg(FakeWinreg(state="2"))
    check("a string that is a number is still a number",
          br.packaged_startup_on(), True)

    br.PACKAGED = False
    check("an unpackaged build has no startup task to be on",
          br.packaged_startup_on(), False)


def test_label():
    print("\n2. the label")
    br.set_language("en")

    br.PACKAGED = True
    br.PACKAGE_FAMILY = "KennyTechy.BlinkRestReminder_ndvpvnpyhp88g"
    with_winreg(FakeWinreg(state=2))
    check("packaged and starting: the button reads ON",
          br.startup_button_text(), ON)

    with_winreg(FakeWinreg(state=1))
    check("packaged and switched off by the user: it reads OFF",
          br.startup_button_text(), OFF)

    with_winreg(FakeWinreg(state=0))
    check("packaged and disabled: OFF, without guessing who did it",
          br.startup_button_text(), OFF)

    # Unpackaged, this label is only ever built when the entry IS blocked --
    # otherwise the panel shows a real switch instead.
    br.PACKAGED = False
    check("unpackaged and blocked: OFF is true of that too",
          br.startup_button_text(), OFF)

    with_winreg(FakeWinreg(raises=OSError("gone")))
    br.PACKAGED = True
    check("an unreadable state reads ON, never a false OFF",
          br.startup_button_text(), ON)


def test_no_translation_debt():
    print("\n3. no translation debt")
    for label in (ON, OFF):
        missing = sorted(code for code, table in blink_i18n.STRINGS.items()
                         if label not in table)
        check("%r is translated in every language" % label, missing, [])
    # The two states must not collapse into one string in any language: a
    # table that translated both to the same words would pass the check above
    # and still leave the button unable to say anything.
    same = sorted(code for code, table in blink_i18n.STRINGS.items()
                  if table.get(ON) == table.get(OFF))
    check("ON and OFF say different things in every language", same, [])
    # The state word is the only part that differs, so the subject must be the
    # wording the switch itself uses -- that is what makes the widths safe.
    odd = sorted(code for code, table in blink_i18n.STRINGS.items()
                 if not table[ON].startswith(table["Start with Windows"]))
    check("every translation is built on that language's switch label",
          odd, [])


def main():
    packaged, family = br.PACKAGED, br.PACKAGE_FAMILY
    real_winreg = sys.modules.get("winreg")
    br.log_event = lambda *a, **k: None
    try:
        test_state()
        test_label()
        test_no_translation_debt()
    finally:
        br.PACKAGED, br.PACKAGE_FAMILY = packaged, family
        if real_winreg is not None:
            sys.modules["winreg"] = real_winreg
    print("\n%s" % ("%d FAILURE(S)" % len(FAILURES) if FAILURES
                    else "all checks passed"))
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
