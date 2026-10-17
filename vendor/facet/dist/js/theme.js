// Theme toggle: dark → light → auto. Persists to localStorage["facet-theme"]; auto (follow the
// system) is the default, for a missing or unknown value.
// This module runs after first paint, so a page that wants the saved theme without a flash puts
// the one-line snippet from the README in its <head>; init() then only labels the toggles.
// setTheme dispatches facet:theme ({theme}) on document, which analytics reports.
const KEY = "facet-theme";
const ORDER = ["dark", "light", "auto"];
const LABEL = { dark: "Dark", light: "Light", auto: "Auto" };
const done = new WeakSet();
const valid = (value) => (ORDER.includes(value) ? value : null);

function show(value) {
  document.documentElement.dataset.theme = value;
  for (const b of document.querySelectorAll("[data-f-theme-toggle]")) {
    b.textContent = LABEL[value];
    b.setAttribute("aria-label", `Theme: ${LABEL[value]}`);
  }
}

export function setTheme(value) {
  const theme = valid(value) || "auto";
  show(theme);
  document.dispatchEvent(new CustomEvent("facet:theme", { detail: { theme } }));
  try {
    localStorage.setItem(KEY, theme);
  } catch {}
}

export function init(root = document) {
  // Only a page with a toggle takes the saved choice; a page without one keeps the data-theme it
  // ships with, since every facet site on one origin shares the key. A bogus saved value is
  // ignored: the page's own data-theme, then auto.
  if (!document.querySelector("[data-f-theme-toggle]")) return () => {};
  let saved = null;
  try {
    saved = valid(localStorage.getItem(KEY));
  } catch {}
  show(saved || valid(document.documentElement.dataset.theme) || "auto");
  const off = [];
  for (const b of root.querySelectorAll("[data-f-theme-toggle]")) {
    if (done.has(b)) continue;
    done.add(b);
    const on = () => {
      const cur = valid(document.documentElement.dataset.theme) || "auto";
      setTheme(ORDER[(ORDER.indexOf(cur) + 1) % ORDER.length]);
    };
    b.addEventListener("click", on);
    off.push(() => {
      b.removeEventListener("click", on);
      done.delete(b);
    });
  }
  return () => off.forEach((f) => f());
}
