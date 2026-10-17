// A Copy button on every code block (facet's .f-code-copy style).
for (const pre of document.querySelectorAll(".f-prose pre")) {
  if (pre.querySelector(".f-code-copy")) continue;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "f-code-copy";
  btn.textContent = "Copy";
  btn.setAttribute("aria-label", "Copy code");
  btn.addEventListener("click", async () => {
    // Clone without Giallo's line-number spans; lines are separated by text-node newlines.
    const clone = (pre.querySelector("code") || pre).cloneNode(true);
    for (const ln of clone.querySelectorAll(".giallo-ln, .f-code-copy")) ln.remove();
    let label = "Copied";
    try {
      await navigator.clipboard.writeText(clone.textContent);
    } catch {
      label = "Copy failed";
    }
    btn.textContent = label;
    btn.setAttribute("aria-label", label);
    setTimeout(() => {
      btn.textContent = "Copy";
      btn.setAttribute("aria-label", "Copy code");
    }, 1500);
  });
  pre.style.position = "relative";
  pre.append(btn);
}
