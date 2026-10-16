// Site search: opens a facet sheet, loads Zola's fuse_json index on first use, ranks pages by
// where the words appear (title, then body), and renders escaped results.
const dialog = document.getElementById("site-search");
const input = dialog?.querySelector("input");
const list = dialog?.querySelector(".site-search-results");
const status = dialog?.querySelector(".site-search-status");
const openers = document.querySelectorAll(".site-search-open");
let index = null;

// One shared promise, so open() and the first keystroke never fetch twice.
function load() {
  index ??= fetch(dialog.dataset.index)
    .then((r) => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    })
    .catch((err) => {
      index = null; // let a later keystroke retry
      throw err;
    });
  return index;
}

function escape(s) {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function score(doc, words) {
  const title = doc.title.toLowerCase();
  const desc = (doc.description ?? "").toLowerCase();
  const body = doc.body.toLowerCase();
  let s = 0;
  for (const w of words) {
    if (title.includes(w)) s += 10;
    else if (desc.includes(w)) s += 5;
    else if (body.includes(w)) s += 1;
    else return 0;
  }
  return s;
}

function snippet(body, word) {
  const i = body.toLowerCase().indexOf(word);
  if (i < 0) return body.slice(0, 140);
  const start = Math.max(0, i - 60);
  return (start ? "…" : "") + body.slice(start, start + 160) + "…";
}

async function run() {
  const q = input.value.trim().toLowerCase();
  list.textContent = "";
  if (!q) return (status.textContent = "");
  const words = q.split(/\s+/);
  let all;
  try {
    all = await load();
  } catch {
    if (input.value.trim().toLowerCase() === q) status.textContent = "Search unavailable";
    return;
  }
  const docs = all
    .map((d) => [score(d, words), d])
    .filter(([s]) => s > 0)
    .sort((a, b) => b[0] - a[0])
    .slice(0, 20);
  // A newer keystroke may have landed while the index loaded.
  if (input.value.trim().toLowerCase() !== q) return;
  status.textContent = docs.length ? `${docs.length} result${docs.length > 1 ? "s" : ""}` : "No results";
  list.innerHTML = docs
    .map(([, d]) => `<li><a href="${escape(d.url)}">${escape(d.title)}</a><p>${escape(snippet(d.body, words[0]))}</p></li>`)
    .join("");
}

function open() {
  dialog.showModal();
  input.focus();
  load().catch(() => {}); // run() reports the failure when someone types
}

if (dialog) {
  for (const b of openers) {
    b.hidden = false;
    b.addEventListener("click", open);
  }
  input.addEventListener("input", run);
  document.addEventListener("keydown", (e) => {
    const t = document.activeElement;
    const typing = t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable);
    if (e.key === "/" && !typing && !dialog.open && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      open();
    }
  });
  dialog.addEventListener("click", (e) => e.target === dialog && dialog.close());

  // Arrows move between the input and the results; Enter on a result follows it.
  dialog.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    const links = [...list.querySelectorAll("a")];
    if (!links.length) return;
    e.preventDefault();
    const at = links.indexOf(document.activeElement);
    const next = e.key === "ArrowDown" ? Math.min(at + 1, links.length - 1) : at - 1;
    (next < 0 ? input : links[next]).focus();
  });
}
