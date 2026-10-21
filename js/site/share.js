// Share a post: the system share sheet where there is one, else copy the link.
const btn = document.querySelector(".site-share");
const status = document.querySelector(".site-share-status");
btn?.addEventListener("click", async () => {
  const data = { title: document.title, url: location.href };
  if (navigator.share) {
    try {
      await navigator.share(data);
    } catch {}
    return;
  }
  try {
    await navigator.clipboard.writeText(location.href);
    if (status) status.textContent = "Link copied";
  } catch {
    if (status) status.textContent = location.href;
  }
});
