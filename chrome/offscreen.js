// The chime, made rather than recorded. The desktop app plays Windows' own
// ding.wav, which is Microsoft's to ship and not ours, so this is a short
// bell synthesised on the spot: a fundamental and two quieter partials, each
// struck and left to decay. No file, nothing fetched.

chrome.runtime.onMessage.addListener((msg) => {
  if (msg && msg.target === "offscreen" && msg.type === "chime") chime(msg.volume);
  return false;
});

function chime(volume = 0.6) {
  const ctx = new AudioContext();
  const now = ctx.currentTime;
  const master = ctx.createGain();
  // Squared, as the desktop's volume is: loudness is not linear in amplitude.
  master.gain.value = 0.35 * volume * volume;
  master.connect(ctx.destination);
  for (const [freq, level, decay] of [[880, 1, 1.4], [1760, 0.3, 0.7], [2637, 0.12, 0.35]]) {
    const osc = ctx.createOscillator();
    const env = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    env.gain.setValueAtTime(0, now);
    env.gain.linearRampToValueAtTime(level, now + 0.006);
    env.gain.exponentialRampToValueAtTime(0.0001, now + decay);
    osc.connect(env).connect(master);
    osc.start(now);
    osc.stop(now + decay + 0.05);
  }
  setTimeout(() => ctx.close(), 1800);
}
