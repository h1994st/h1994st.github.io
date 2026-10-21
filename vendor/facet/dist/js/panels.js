// Full-page panels: <main class="f-panels" data-f-panels> of .f-panel sections, plus an optional
// empty <nav class="f-dots">. The panel filling most of the screen is current: it gets .is-on
// (its .f-reveal text arrives), its video plays and the others pause, its dot is lit, and a
// .f-nav--over stays clear over media panels and turns to glass over .f-panel--plain ones (the
// dots switch to page colors there too).
// A panel with a video should hold a <button data-f-panel-toggle hidden> pause control: it is
// shown while motion is allowed, its label swaps between data-f-pause and data-f-play ("Pause",
// "Play"), and a user's pause sticks. Under reduced motion videos never play and it stays hidden.
// Tracked on scroll, so a fast scroll never skips a panel.
const done = new WeakSet();

export function init(root = document) {
  const off = [];
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  for (const host of root.querySelectorAll("[data-f-panels]")) {
    if (done.has(host)) continue;
    const panels = [...host.querySelectorAll(".f-panel")];
    if (!panels.length) continue;
    done.add(host);
    const nav = document.querySelector(".f-nav--over");
    const dots = document.querySelector("nav.f-dots");
    const buttons = [];
    if (dots) {
      panels.forEach((p, i) => {
        const b = document.createElement("button");
        b.type = "button";
        b.setAttribute("aria-label", p.querySelector("h2")?.textContent.trim() || `${i + 1}`);
        b.addEventListener("click", () =>
          p.scrollIntoView({ behavior: still ? "auto" : "smooth" }),
        );
        dots.append(b);
        buttons.push(b);
      });
    }

    // Each panel's video and its pause control.
    const media = panels.map((p) => ({
      video: p.querySelector("video"),
      btn: p.querySelector("[data-f-panel-toggle]"),
      held: false,
    }));
    const unbind = [];
    for (const m of media) {
      const { video, btn } = m;
      if (!video || !btn || still) continue;
      const label = () => {
        btn.textContent = video.paused
          ? btn.dataset.fPlay || "Play"
          : btn.dataset.fPause || "Pause";
      };
      const toggle = () => {
        m.held = !video.paused;
        if (m.held) video.pause();
        else video.play().catch(() => {});
      };
      video.addEventListener("play", label);
      video.addEventListener("pause", label);
      btn.addEventListener("click", toggle);
      btn.hidden = false;
      label();
      unbind.push(() => {
        video.removeEventListener("play", label);
        video.removeEventListener("pause", label);
        btn.removeEventListener("click", toggle);
        btn.hidden = true;
      });
    }

    host.classList.add("is-ready");
    nav?.classList.add("is-ready");
    let current = -1;
    const update = () => {
      let best = 0;
      let most = -1;
      panels.forEach((p, i) => {
        const r = p.getBoundingClientRect();
        const seen = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
        // Settled: the panel fills more than 55% of the screen.
        p.classList.toggle("is-on", seen > innerHeight * 0.55);
        if (seen > most) [best, most] = [i, seen];
      });
      if (best === current) return;
      current = best;
      media.forEach(({ video, held }, i) => {
        if (!video) return;
        if (i === best && !still && !held) video.play().catch(() => {});
        else video.pause();
      });
      buttons.forEach((b, i) =>
        i === best ? b.setAttribute("aria-current", "step") : b.removeAttribute("aria-current"),
      );
      const plain = panels[best].classList.contains("f-panel--plain");
      nav?.classList.toggle("is-scrolled", plain);
      dots?.classList.toggle("is-over-plain", plain);
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
      unbind.forEach((f) => f());
      buttons.forEach((b) => b.remove());
      host.classList.remove("is-ready");
      nav?.classList.remove("is-ready", "is-scrolled");
      dots?.classList.remove("is-over-plain");
      done.delete(host);
    });
  }
  return () => off.forEach((f) => f());
}
