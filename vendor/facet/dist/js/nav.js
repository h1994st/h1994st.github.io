// Nav over a cover: <nav class="f-nav f-nav--over" data-f-nav-cover="#cover"> stays clear while
// the cover fills the screen and turns to glass (.is-scrolled) once less than 12% of it is visible.
// The clear state only applies once this adds .is-ready, so without JS the nav is plain glass.
// Tracked on scroll, so a fast scroll or a jump never leaves the nav in the wrong state.
const done = new WeakSet();

export function init(root = document) {
  const off = [];
  for (const nav of root.querySelectorAll("[data-f-nav-cover]")) {
    if (done.has(nav)) continue;
    const cover = document.querySelector(nav.dataset.fNavCover);
    if (!cover) continue;
    done.add(nav);
    nav.classList.add("is-ready");
    const update = () => {
      const r = cover.getBoundingClientRect();
      const seen = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
      nav.classList.toggle("is-scrolled", seen < r.height * 0.12);
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
      nav.classList.remove("is-ready", "is-scrolled");
      done.delete(nav);
    });
  }
  return () => off.forEach((f) => f());
}
