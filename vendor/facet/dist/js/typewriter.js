// Typewriter: <span data-f-type='["meow", "hi", "purr"]'>meow</span> types each phrase in turn,
// one character at a time (50 ms each, or data-f-type-speed), holds it (2500 ms, or
// data-f-type-hold), clears it and types the next, looping. The element's own text is the still
// state: shown first (and, if it is one of the phrases, the loop continues from it), kept under
// reduced motion, and restored by cleanup. It waits while the tab is hidden or the element is off
// screen. Put it inside an aria-hidden wrapper next to the real value in visually hidden text:
// screen readers should never hear the typing.
const done = new WeakSet();
const segmenter =
  typeof Intl !== "undefined" && Intl.Segmenter
    ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
    : null;
const graphemes = (s) =>
  segmenter ? Array.from(segmenter.segment(s), (g) => g.segment) : Array.from(s);

function phrasesOf(el) {
  try {
    const value = JSON.parse(el.dataset.fType);
    if (Array.isArray(value) && value.length && value.every((v) => typeof v === "string")) {
      return value;
    }
  } catch {}
  console.warn("facet: data-f-type needs a JSON array of strings; leaving the text as is.", el);
  return null;
}

export function init(root = document) {
  const off = [];
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return () => {};
  for (const el of root.querySelectorAll("[data-f-type]")) {
    if (done.has(el)) continue;
    const phrases = phrasesOf(el);
    if (!phrases) continue;
    done.add(el);
    const speed = Number(el.dataset.fTypeSpeed) || 50;
    const hold = Number(el.dataset.fTypeHold) || 2500;
    const original = el.textContent;
    let p = phrases.indexOf(original.trim());
    let chars = graphemes(original);
    let i = chars.length;
    let timer = 0;
    let visible = false;
    let stopped = false;
    const running = () => visible && !document.hidden;
    const schedule = () => {
      timer = setTimeout(step, i < chars.length ? speed : hold);
    };
    function step() {
      timer = 0;
      if (!running()) return;
      if (i < chars.length) {
        i += 1;
        el.textContent = chars.slice(0, i).join("");
      } else {
        p = (p + 1) % phrases.length;
        chars = graphemes(phrases[p]);
        i = 0;
        el.textContent = "";
      }
      schedule();
    }
    const resume = () => {
      if (!stopped && running() && !timer) schedule();
    };
    const io = new IntersectionObserver((entries) => {
      if (stopped) return;
      const entry = entries[entries.length - 1];
      visible = entry.isIntersecting;
      // "1" while on screen, "0" off it: the tests wait on this before moving the clock.
      el.dataset.fTypeOn = visible ? "1" : "0";
      resume();
    });
    io.observe(el);
    document.addEventListener("visibilitychange", resume);
    off.push(() => {
      stopped = true;
      clearTimeout(timer);
      io.disconnect();
      document.removeEventListener("visibilitychange", resume);
      el.textContent = original;
      delete el.dataset.fTypeOn;
      done.delete(el);
    });
  }
  return () => off.forEach((f) => f());
}
