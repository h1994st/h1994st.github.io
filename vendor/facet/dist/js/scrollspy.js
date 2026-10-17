// Scroll spy: the link whose section top has passed 30% of the viewport is current and gets
// aria-current="location"; at the bottom of a scrolled page the last link is, so a short last
// section still gets its turn. When the nav scrolls along its inline axis (the .f-toc chip bar below
// 1024px), a change of current link also scrolls the nav itself, never the page, so the link is
// fully in view with a little room on each side for the neighboring chips to peek in. The scroll is
// smooth, or instant under prefers-reduced-motion. It waits while the reader works the bar: for 1s
// after a pointerdown, wheel or touchmove on it, then catches up. It reads positions from the
// layout boxes, so it works in LTR and RTL; a link wider than the bar keeps its start edge in view.
// A desktop sidebar (overflow visible) is never scrolled.
const done = new WeakSet();
const PEEK = 40; // px of room beside the current chip, at most a quarter of the bar
const HOLD = 1000; // ms to wait after the reader touches the bar

// a.hash is percent-encoded (#安装 reads as #%E5%AE%89%E8%A3%85); ids are not.
const idOf = (a) => {
  const raw = a.hash.slice(1);
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
};

const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

export function init(root = document) {
  const off = [];
  for (const nav of root.querySelectorAll("[data-f-scrollspy]")) {
    if (done.has(nav)) continue;
    done.add(nav);
    const links = [...nav.querySelectorAll('a[href^="#"]')];
    const targets = links.map((a) => document.getElementById(idOf(a)));
    let last = -1;
    let holdUntil = 0;
    let timer = 0;
    const follow = (a, instant) => {
      clearTimeout(timer);
      const wait = holdUntil - performance.now();
      if (wait > 0) {
        timer = setTimeout(() => follow(a, instant), wait);
        return;
      }
      const s = getComputedStyle(nav);
      if (!/auto|scroll/.test(s.overflowX) || nav.scrollWidth <= nav.clientWidth + 1) return;
      const start = nav.getBoundingClientRect().left + nav.clientLeft;
      const peek = Math.min(PEEK, nav.clientWidth / 4);
      const lo = start + peek;
      const hi = start + nav.clientWidth - peek;
      const r = a.getBoundingClientRect();
      let d = r.left < lo ? r.left - lo : r.right > hi ? r.right - hi : 0;
      if (r.width > hi - lo) d = s.direction === "rtl" ? r.right - hi : r.left - lo;
      if (Math.abs(d) < 1) return;
      nav.scrollTo({
        left: nav.scrollLeft + d,
        behavior: instant || still() ? "auto" : "smooth",
      });
    };
    const update = () => {
      let cur = 0;
      targets.forEach((t, i) => {
        if (t && t.getBoundingClientRect().top < innerHeight * 0.3) cur = i;
      });
      // A short last section can never reach that line: at the bottom of a scrolled page it is current.
      const end = document.documentElement.scrollHeight - innerHeight;
      if (scrollY > 0 && scrollY >= end - 2 && targets.at(-1)) cur = links.length - 1;
      links.forEach((a, i) =>
        i === cur ? a.setAttribute("aria-current", "location") : a.removeAttribute("aria-current"),
      );
      if (cur !== last && links[cur]) follow(links[cur], last < 0);
      last = cur;
    };
    const hold = () => {
      holdUntil = performance.now() + HOLD;
    };
    const touch = ["pointerdown", "wheel", "touchmove"];
    for (const t of touch) nav.addEventListener(t, hold, { passive: true });
    addEventListener("scroll", update, { passive: true });
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      for (const t of touch) nav.removeEventListener(t, hold);
      clearTimeout(timer);
      done.delete(nav);
    });
  }
  return () => off.forEach((f) => f());
}
