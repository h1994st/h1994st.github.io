// Liquid hover: a light that follows the pointer on cards, mouse only.
const done = new WeakSet();

export function init(root = document) {
  const off = [];
  for (const host of root.querySelectorAll("[data-f-liquid]")) {
    const cards = host.matches(".f-card") ? [host] : [...host.querySelectorAll(".f-card")];
    for (const card of cards) {
      if (done.has(card)) continue;
      done.add(card);
      const enter = (e) => e.pointerType === "mouse" && card.classList.add("is-hot");
      const leave = () => card.classList.remove("is-hot");
      const move = (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--f-lx", `${e.clientX - r.left}px`);
        card.style.setProperty("--f-ly", `${e.clientY - r.top}px`);
      };
      card.addEventListener("pointerenter", enter);
      card.addEventListener("pointerleave", leave);
      card.addEventListener("pointermove", move);
      off.push(() => {
        card.removeEventListener("pointerenter", enter);
        card.removeEventListener("pointerleave", leave);
        card.removeEventListener("pointermove", move);
        card.classList.remove("is-hot");
        done.delete(card);
      });
    }
  }
  return () => off.forEach((f) => f());
}
