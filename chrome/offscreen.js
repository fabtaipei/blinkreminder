// The reminder sounds, made rather than recorded.
//
// The desktop plays Windows' own files from C:\Windows\Media, which are
// Microsoft's to ship and not ours, so each of the four is synthesised here
// to the same character as the one it is named after. No file, nothing
// fetched: the whole sound is a handful of oscillators.
//
// A web page may not play a sound unprompted, which is why this runs in an
// offscreen document rather than in the cue itself.

chrome.runtime.onMessage.addListener((msg) => {
  if (msg && msg.target === "offscreen" && msg.type === "chime") {
    play(msg.name, msg.volume);
  }
  return false;
});

// (frequency, level, seconds, delay before it starts). Struck and left to
// decay, which is what every one of these is: a short, pitched tap.
const VOICES = {
  // One clean tap, high and brief. The desktop's default.
  ding: [[880, 1, 0.45, 0]],
  // Three notes at once -- a major chord, which reads as softer than a
  // single tone at the same loudness.
  chord: [[523.25, 0.8, 1.1, 0], [659.25, 0.7, 1.1, 0], [783.99, 0.6, 1.1, 0]],
  // A bell: a fundamental and two quieter partials above it.
  chime: [[880, 1, 1.4, 0], [1760, 0.3, 0.7, 0], [2637, 0.12, 0.35, 0]],
  // Two notes, the second a fifth above: the shape of a notification.
  notify: [[659.25, 0.9, 0.3, 0], [987.77, 0.9, 0.5, 0.13]],
};

function play(name, volume = 0.6) {
  const voices = VOICES[name] || VOICES.ding;
  const ctx = new AudioContext();
  const now = ctx.currentTime;
  const master = ctx.createGain();
  // Squared, as the desktop's volume is: loudness is not linear in
  // amplitude, so a linear slider spends its top half sounding the same.
  master.gain.value = 0.35 * volume * volume;
  master.connect(ctx.destination);

  let longest = 0;
  for (const [freq, level, decay, delay] of voices) {
    const at = now + delay;
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    env.gain.setValueAtTime(0, at);
    env.gain.linearRampToValueAtTime(level, at + 0.006);
    env.gain.exponentialRampToValueAtTime(0.0001, at + decay);
    osc.connect(env).connect(master);
    osc.start(at);
    osc.stop(at + decay + 0.05);
    longest = Math.max(longest, delay + decay);
  }
  setTimeout(() => ctx.close(), (longest + 0.4) * 1000);
}
