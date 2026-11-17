// Autoplay: <video data-f-autoplay muted loop playsinline poster="…"> plays muted while it is on
// screen and pauses when it leaves. Under reduced motion it never plays: the poster stays.
// An optional <button data-f-autoplay-toggle aria-controls="video-id" hidden> is shown while the
// video is on screen as a pause/play control (labels from data-f-pause / data-f-play); a user's
// pause sticks.
const done = new WeakSet();

export function init(root = document) {
  const off = [];
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  for (const video of root.querySelectorAll("video[data-f-autoplay]")) {
    if (done.has(video)) continue;
    video.muted = true;
    if (still) {
      video.pause();
      continue;
    }
    done.add(video);
    const btn = video.id
      ? document.querySelector(`[data-f-autoplay-toggle][aria-controls="${video.id}"]`)
      : null;
    let userPaused = false;
    let visible = false;
    const label = () => {
      if (!btn) return;
      btn.textContent = video.paused ? btn.dataset.fPlay || "Play" : btn.dataset.fPause || "Pause";
    };
    const sync = () => {
      if (visible && !userPaused) video.play().catch(() => {});
      else video.pause();
    };
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (btn) btn.hidden = !visible;
      sync();
    });
    io.observe(video);
    video.addEventListener("play", label);
    video.addEventListener("pause", label);
    const toggle = () => {
      userPaused = !video.paused;
      if (userPaused) video.pause();
      else video.play().catch(() => {});
    };
    if (btn) btn.addEventListener("click", toggle);
    off.push(() => {
      io.disconnect();
      video.removeEventListener("play", label);
      video.removeEventListener("pause", label);
      if (btn) {
        btn.removeEventListener("click", toggle);
        btn.hidden = true;
      }
      done.delete(video);
    });
  }
  return () => off.forEach((f) => f());
}
