// Deck: <main class="f-deck" data-f-deck> holding a .f-deck__stage (caps, a board of
// [data-f-piece] elements, a bar) and .f-deck__slide sections, each with data-f-slide JSON. The
// data format is documented on the reference site (index.html, "Behavior").
// Each slide is a full-page scroll stop; ←/→, Space and the bar's buttons move one slide. Only the
// current caption is reachable: the others are inert.
// All data is read and checked before the page is touched: a deck with bad data is left in its
// no-JS form (stacked slides with their captions) and a warning names the problem.
const nums = (v, n) => Array.isArray(v) && v.length >= n && v.every(Number.isFinite);
const SHAPES = { at: 2, beam: 3, box: 4 };

function readData(slides, pieceEls) {
  const states = slides.map((s, i) => {
    const st = JSON.parse(s.dataset.fSlide || "{}");
    if (!st || typeof st !== "object" || Array.isArray(st))
      throw new Error(`slide ${i + 1}: data-f-slide is not an object`);
    for (const [id, v] of Object.entries(st)) {
      if (!v || typeof v !== "object") throw new Error(`slide ${i + 1}: "${id}" is not an object`);
      for (const [k, n] of Object.entries(SHAPES))
        if (k in v && !nums(v[k], n))
          throw new Error(`slide ${i + 1}: "${id}.${k}" needs ${n} numbers`);
    }
    return st;
  });
  const froms = pieceEls.map((p) => {
    if (!p.dataset.fFrom) return null;
    const from = JSON.parse(p.dataset.fFrom);
    if (!nums(from, 2)) throw new Error(`piece "${p.dataset.fPiece}": data-f-from needs numbers`);
    return from;
  });
  return { states, froms };
}

const done = new WeakSet();

export function init(root = document) {
  const off = [];
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  for (const deck of root.querySelectorAll("[data-f-deck]")) {
    if (done.has(deck)) continue;
    const slides = [...deck.querySelectorAll(".f-deck__slide")];
    const caps = deck.querySelector(".f-deck__caps");
    if (!slides.length || !caps) continue;
    const pieceEls = [...deck.querySelectorAll("[data-f-piece]")];
    let data;
    try {
      data = readData(slides, pieceEls);
    } catch (err) {
      console.warn("facet deck: bad slide data, showing the slides as plain sections.", err);
      continue;
    }
    done.add(deck);
    const { states, froms } = data;
    const fromOf = new Map(pieceEls.map((p, i) => [p, froms[i]]));
    const pieces = Object.fromEntries(pieceEls.map((p) => [p.dataset.fPiece, p]));
    const count = deck.querySelector(".f-deck__count");
    const progress = deck.querySelector(".f-deck__progress");

    // Move each caption into the stage, keeping the nodes so cleanup can put them back.
    const moved = slides.map((s) => {
      const cap = document.createElement("div");
      cap.className = "f-deck__cap";
      const nodes = [...s.childNodes];
      cap.append(...nodes);
      caps.append(cap);
      return { cap, nodes };
    });
    caps.setAttribute("aria-live", "polite");

    const place = (p, [l, t, w, h]) => {
      p.style.left = `${l}%`;
      p.style.top = `${t}%`;
      if (w !== undefined) p.style.width = `${w}%`;
      if (h !== undefined) p.style.height = `${h}%`;
    };
    const vertical = (p) => p.classList.contains("f-deck__beam--v");
    const grow = (p, len) => (vertical(p) ? (p.style.height = len) : (p.style.width = len));
    const start = {};
    for (const [id, p] of Object.entries(pieces)) {
      const first = states.find((s) => s[id])?.[id] || {};
      const from = fromOf.get(p);
      if (first.beam) start[id] = first.beam.slice(0, 2);
      if (from) place(p, from);
      else if (first.at) place(p, first.at);
      else if (first.box) place(p, first.box);
      if (first.beam) {
        place(p, start[id]);
        grow(p, "0%");
      }
    }

    const apply = (i) => {
      const s = states[i];
      for (const [id, p] of Object.entries(pieces)) {
        const st = s[id];
        if (!st) {
          p.style.opacity = 0;
          if (start[id]) {
            place(p, start[id]);
            grow(p, "0%");
          }
          continue;
        }
        p.style.opacity = st.fade ? 0 : 1;
        if (st.c) p.style.setProperty("--c", st.c);
        if (st.at) place(p, st.at);
        if (st.box) place(p, st.box);
        if (st.beam) {
          start[id] = st.beam.slice(0, 2);
          place(p, start[id]);
          grow(p, `${st.beam[2]}%`);
        }
        // A lit piece (the target) fills with its color.
        if (st.lit) {
          p.style.setProperty("--fill", st.c);
          p.style.setProperty("--ring", st.c);
        } else {
          p.style.removeProperty("--fill");
          p.style.removeProperty("--ring");
        }
      }
      moved.forEach(({ cap }, j) => {
        cap.classList.toggle("is-on", j === i);
        cap.inert = j !== i;
      });
      if (count) count.textContent = `${i + 1} / ${slides.length}`;
      progress?.style.setProperty("--p", `${((i + 1) / slides.length) * 100}%`);
    };

    deck.classList.add("is-ready");
    let current = -1;
    const top0 = () => slides[0].getBoundingClientRect().top + scrollY;
    const height = () => slides[0].offsetHeight || innerHeight;
    const update = () => {
      const i = Math.round((scrollY - top0()) / height());
      const clamped = Math.max(0, Math.min(slides.length - 1, i));
      if (clamped !== current) apply((current = clamped));
    };
    const go = (d) => {
      const i = Math.max(0, Math.min(slides.length - 1, current + d));
      scrollTo({ top: top0() + i * height(), behavior: still ? "auto" : "smooth" });
    };
    const key = (e) => {
      if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.target.closest?.("input, textarea, select, [contenteditable]")) return;
      const d =
        e.key === "ArrowRight" || (e.key === " " && !e.shiftKey)
          ? 1
          : e.key === "ArrowLeft" || (e.key === " " && e.shiftKey)
            ? -1
            : 0;
      if (!d) return;
      if (e.key === " " && e.target.closest?.("button, a")) return;
      e.preventDefault();
      go(d);
    };
    const prev = deck.querySelector("[data-f-deck-prev]");
    const next = deck.querySelector("[data-f-deck-next]");
    const back = () => go(-1);
    const fwd = () => go(1);
    prev?.addEventListener("click", back);
    next?.addEventListener("click", fwd);
    addEventListener("keydown", key);
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();

    off.push(() => {
      prev?.removeEventListener("click", back);
      next?.removeEventListener("click", fwd);
      removeEventListener("keydown", key);
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
      moved.forEach(({ cap, nodes }, j) => {
        slides[j].append(...nodes);
        cap.remove();
      });
      caps.removeAttribute("aria-live");
      deck.classList.remove("is-ready");
      done.delete(deck);
    });
  }
  return () => off.forEach((f) => f());
}
