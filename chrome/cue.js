// Draws one reminder over the page: a dot, a word, or a dim.
//
// Injected into the tab in front when a reminder is due, and loaded by the
// settings page for its previews. It must never get in the way, which on a
// web page means four things:
//   - clicks and keys pass straight through (pointer-events: none, and
//     nothing in it can take focus);
//   - the page cannot restyle it, nor it the page (a closed shadow root,
//     and every property set inline as !important);
//   - it sits above everything, fullscreen video included (the top layer,
//     as a manual popover, where the browser supports one);
//   - it reads nothing from the page and leaves nothing behind.

(() => {
  if (globalThis.__blinkReminderCue) return;

  let current = null;
  let shown = null;      // the frame being faded, for the end-to-end test

  function css(el, props) {
    for (const [k, v] of Object.entries(props)) el.style.setProperty(k, v, "important");
  }

  // Where the cue sits, as flexbox alignment of a full-viewport frame.
  const ALIGN = {
    center: ["center", "center"],
    "top-left": ["flex-start", "flex-start"],
    "top-right": ["flex-start", "flex-end"],
    "bottom-left": ["flex-end", "flex-start"],
    "bottom-right": ["flex-end", "flex-end"],
  };

  function build(p) {
    const host = document.createElement("blink-reminder-cue");
    host.setAttribute("aria-hidden", "true");
    css(host, {
      all: "initial", display: "block", position: "fixed", inset: "0",
      width: "100vw", height: "100vh", "max-width": "none", "max-height": "none",
      margin: "0", padding: "0", border: "0", background: "transparent",
      overflow: "hidden", "pointer-events": "none", "z-index": "2147483647",
      "user-select": "none",
    });

    const root = host.attachShadow({ mode: "closed" });
    const frame = document.createElement("div");
    const [vertical, horizontal] = ALIGN[p.corner] || ALIGN.center;
    css(frame, {
      position: "fixed", inset: "0", display: "flex", direction: "ltr",
      "align-items": vertical, "justify-content": horizontal,
      padding: p.corner === "center" ? "0" : `${p.margin}px`,
      "box-sizing": "border-box", "pointer-events": "none",
    });
    // The fade runs on this frame, not on the host. The host's `all: initial
    // !important` -- its armour against the page's stylesheets -- fixes its
    // opacity at 1, and an animation cannot override an !important value:
    // the first build drew every cue at full strength. Inside the closed
    // shadow root no page style can reach, so this one needs no armour.
    frame.style.opacity = "0";
    const cue = document.createElement("div");
    css(cue, { "pointer-events": "none", flex: "none" });

    if (p.style === "dim") {
      css(frame, { padding: "0", background: p.colour });
    } else if (p.style === "dot") {
      // A share of the viewport's SHORT side, as the desktop sizes it against
      // the screen's: the same share of a phone-shaped window and a wide one.
      const d = Math.max(4, Math.round(p.dotPct / 100 * Math.min(innerWidth, innerHeight)));
      css(cue, { width: `${d}px`, height: `${d}px`, "border-radius": "50%",
                 background: p.colour });
      frame.append(cue);
    } else {
      cue.textContent = p.message;
      css(cue, {
        color: p.colour, "font-size": `${p.fontSize}px`, "font-weight": "600",
        "font-family": 'system-ui, "Segoe UI Variable", "Segoe UI", sans-serif',
        "line-height": "1.2", "white-space": "nowrap", "max-width": "100vw",
        overflow: "hidden", "text-overflow": "ellipsis",
      });
      frame.append(cue);
    }
    root.append(frame);
    return { host, frame };
  }

  function show(host) {
    // The top layer, where supported: above every z-index on the page, and
    // above an element in fullscreen too, which no z-index can reach.
    const top = typeof host.showPopover === "function";
    if (top) host.setAttribute("popover", "manual");
    (top ? document.documentElement
         : document.fullscreenElement || document.documentElement).append(host);
    if (top) host.showPopover();
  }

  function remove(host) {
    try {
      if (host.matches(":popover-open")) host.hidePopover();
    } catch { /* never shown as a popover */ }
    host.remove();
  }

  globalThis.__blinkReminderCue = async function (p) {
    if (current) remove(current);
    // The corner dot steps aside for the length of the reminder, so the two
    // are never on screen at once -- as the desktop's indicator does.
    const span = (2 * p.fade + p.hold) * p.blinks + p.gap * (p.blinks - 1);
    globalThis.__blinkReminderDot?.suppress(span + 400);
    const { host, frame } = build(p);
    current = host;
    shown = frame;
    show(host);
    // Fades are motion; someone who has asked for less of it gets a cut.
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fade = (from, to) => frame.animate([{ opacity: from }, { opacity: to }],
      { duration: still ? 0 : p.fade, fill: "forwards" }).finished;
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    try {
      for (let i = 0; i < p.blinks && current === host; i++) {
        await fade(0, p.opacity);
        await wait(p.hold);
        await fade(p.opacity, 0);
        if (i < p.blinks - 1) await wait(p.gap);
      }
    } finally {
      // Whatever happened, nothing is left on the page.
      remove(host);
      if (current === host) current = null;
    }
  };

  // What is on screen now. Read only by the end-to-end test, from this
  // script's own isolated world -- the page cannot see it.
  globalThis.__blinkReminderCue.state = () => current && {
    opacity: Number(getComputedStyle(shown).opacity),
    open: current.matches(":popover-open"),
    events: getComputedStyle(current).pointerEvents,
  };
})();
