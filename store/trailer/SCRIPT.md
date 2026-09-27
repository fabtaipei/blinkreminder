# Trailer

`trailer-1920x1080.mp4` — about 6.3 seconds, silent, 1920×1080.

| Time | What happens | Caption |
|---|---|---|
| 0.0s | The real desktop, with nothing on it | none |
| ~0.5s | The blink reminder: one dot, centred | `Caption: blink reminder` |
| ~3.1s | The break reminder: the whole screen dims | `Caption: break reminder` |
| ~6.3s | End | none |

The background is the real desktop of the main screen, with no staged backdrop.
To keep the taskbar out, the recording is the largest 16:9 area centred on the
screen that stays above it: 1664×936, scaled up 1.154× to 1920×1080. The
captions are added after the scaling, so they stay sharp. Captions start with
"Caption:" so viewers don't mistake them for text the app puts on screen. There is no
end card: the Store listing already shows the name.

**Colour, strength and dot size** come from the user's own app settings at
recording time (`colour`/`opacity`/`dot_size`, `break_colour`/`break_opacity`
in `config.json`). **Timing** is the trailer's own: one pulse per reminder, held
long enough to read on video.

## Rebuilding

`maketrailer4.py` (session scratchpad), with `shots.py` beside it. It:

- refuses to record if the capture monitor has real windows on it
- waits out the user's :00/:30 break
- draws reminders on the capture monitor only
- rejects and re-records any take where the user's own running copy of the app
  fires mid-recording
- aligns captions to the pulses as detected in the footage
- measures the finished file to confirm the dot is centred

Microsoft's trailer validator rejects a video with no audio stream, so the
file carries a silent AAC track.
