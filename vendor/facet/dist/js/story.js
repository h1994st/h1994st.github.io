// Scroll story: <div class="f-story" data-f-story> with .f-story__stage img[data-step] and
// .f-story__step sections. The active step is the last one whose top has passed a reading line:
// the middle of the screen on wide screens; on phones (pinned band on top), 30% of the way down
// the area under the band. Checked on every scroll, so a fast scroll never skips a step.
const PHONE = "(max-width: 720px)";

const done = new WeakSet();

export function init(root = document) {
  const off = [];
  const phone = matchMedia(PHONE);
  for (const story of root.querySelectorAll("[data-f-story]")) {
    if (done.has(story)) continue;
    const pin = story.querySelector(".f-story__pin");
    const steps = [...story.querySelectorAll(".f-story__step")];
    const imgs = [...story.querySelectorAll(".f-story__stage img[data-step]")];
    const count = story.querySelector(".f-story__count");
    if (!pin || !steps.length) continue;
    done.add(story);
    story.classList.add("is-ready");
    let current = -1;
    const show = (i) => {
      steps.forEach((s, j) => s.classList.toggle("is-on", i === j));
      imgs.forEach((im) => im.classList.toggle("is-on", +im.dataset.step === i));
      if (count) count.textContent = `${i + 1} / ${steps.length}`;
    };
    const update = () => {
      const band = pin.getBoundingClientRect().bottom;
      const line = phone.matches ? band + (innerHeight - band) * 0.3 : innerHeight * 0.5;
      let i = 0;
      steps.forEach((s, j) => {
        if (s.getBoundingClientRect().top < line) i = j;
      });
      if (i !== current) show((current = i));
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
    off.push(() => {
      removeEventListener("scroll", update);
      removeEventListener("resize", update);
      story.classList.remove("is-ready");
      done.delete(story);
    });
  }
  return () => off.forEach((f) => f());
}
