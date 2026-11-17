// facet's optional behavior. Importing this file initializes every module once the page has
// parsed: <script type="module" src=".../dist/js/facet.js">. Each module initializes the elements
// that opt in with a data-f-* attribute, skips elements it has already initialized, and returns a
// cleanup function. Imported statically, so the whole graph loads with the page and every module
// is running by the time the load event fires (a chain of dynamic imports finished later, so
// early input, such as a deck's arrow keys, was lost).
import * as analytics from "./analytics.js";
import * as theme from "./theme.js";
import * as liquid from "./liquid.js";
import * as scrollspy from "./scrollspy.js";
import * as nav from "./nav.js";
import * as autoplay from "./autoplay.js";
import * as story from "./story.js";
import * as panels from "./panels.js";
import * as deck from "./deck.js";
import * as typewriter from "./typewriter.js";
import * as variants from "./variants.js";

const modules = {
  analytics,
  theme,
  liquid,
  scrollspy,
  nav,
  autoplay,
  story,
  panels,
  deck,
  typewriter,
  variants,
};

// Initializes every module under root. One module that throws is reported and skipped, so the
// others still run. Returns a function that undoes this call; calling it again does nothing.
export function init(root = document) {
  const cleanups = [];
  for (const [name, m] of Object.entries(modules)) {
    try {
      cleanups.push(m.init(root));
    } catch (err) {
      console.error(`facet: the ${name} module failed to initialize.`, err);
    }
  }
  let undone = false;
  return () => {
    if (undone) return;
    undone = true;
    cleanups.forEach((f) => typeof f === "function" && f());
  };
}

// Undoes the initialization that importing this file ran.
export let cleanup = () => {};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => (cleanup = init()), { once: true });
} else {
  cleanup = init();
}
