// A Copy button on every code block (facet's .f-code-copy style).
for (const pre of document.querySelectorAll(".f-prose pre")) {
  if (pre.querySelector(".f-code-copy")) continue;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "f-code-copy";
  btn.textContent = "Copy";
  btn.setAttribute("aria-label", "Copy code");
  btn.addEventListener("click", async () => {
    const code = pre.querySelector("code") || pre;
    try {
      await navigator.clipboard.writeText(code.innerText);
      btn.textContent = "Copied";
    } catch {
      btn.textContent = "Press ⌘C";
    }
    setTimeout(() => (btn.textContent = "Copy"), 1500);
  });
  pre.style.position = "relative";
  pre.append(btn);
}
