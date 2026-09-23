# Store screenshots

Upload in this order. Partner Center shows them in upload order and the first
one is the only one many people ever see.

| # | File | What it shows |
|---|------|---------------|
| 1 | 01-blink-cue.png | The blink cue: the amber dot over a window someone is reading |
| 2 | 02-look-away.png | The separate look-away break, as a word, on a dark app |
| 3 | 03-dim.png | The same break as a whole-screen dim |
| 4 | 04-running-quietly.png | The tray indicator and its countdown, nothing else happening |
| 5 | 05-settings.png | The settings panel, entire: both reminders, both preview buttons |

All are 1440x810 PNG with a caption strip, well inside the Store's limits
(1366x768 minimum, 50 MB each).

## Why these, and not the old ones

The previous set opened on the settings panel, used two near-identical pictures
of it, and showed the product actually working only in the third image -- which
was a capture of a BBC article, complete with BBC branding and press photographs
of identifiable musicians, on a commercial listing.

The dot in that shot was also green, because it was a capture of the developer's
own saved config rather than of the product. The shipped default is amber, the
same amber as the icon, which is what these show.

## Regenerating

    py makeshots.py        (in the session scratchpad, with shots.py beside it)

Everything in the frames is drawn by the app's own classes, captured off the
composited desktop -- a click-through layered window cannot be screenshotted any
other way. The backdrop is drawn by the script, so no third-party content can
end up in a frame. See the docstrings in shots.py for the rest.

## Captions

They are burned into the images rather than left to Partner Center's caption
field, which is a tooltip almost nobody opens. Three of these shots do not
survive without one: a dimmed window reads as a disabled window, and a 20px
pill in the corner of a screen reads as nothing at all.
