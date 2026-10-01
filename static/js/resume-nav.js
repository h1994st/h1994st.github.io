// Section nav for /resume/ (templates/resume.html). Narrow screens: the bar
// sticks under the site nav. Wide screens: the bar stays put and a sidebar
// copy is shown once it has scrolled away. Either way, the section in view
// is marked with aria-current="location".
(function () {
	"use strict";

	const nav = document.querySelector(".rs-nav");
	if (!nav) return;

	const root = nav.closest(".resume");
	const siteNav = document.getElementById("site-nav");
	const wideQuery = window.matchMedia("(min-width: 1200px)");
	const links = Array.from(root.querySelectorAll(".rs-nav a, .rs-side a"));
	const sections = Array.from(nav.querySelectorAll("a"))
		.map((a) => document.getElementById(decodeURIComponent(a.hash.slice(1))))
		.filter(Boolean);
	if (!sections.length) return;

	let stick = 0;
	let offset = 0;
	let current = null;

	// The site nav itself only sticks on wider screens; sit just below it
	// there, and at the top of the viewport otherwise.
	function measure() {
		stick = 0;
		if (siteNav) {
			const style = getComputedStyle(siteNav);
			if (style.position === "sticky" || style.position === "fixed") {
				stick = (parseFloat(style.top) || 0) + siteNav.offsetHeight + 8;
			}
		}
		const barH = wideQuery.matches ? 0 : nav.offsetHeight;
		root.style.setProperty("--rs-stick", stick + "px");
		root.style.setProperty("--rs-nav-h", barH + "px");
		offset = stick + barH;
	}

	function update() {
		root.classList.toggle(
			"rs-side-on",
			wideQuery.matches && nav.getBoundingClientRect().bottom <= stick,
		);

		let next = sections[0];
		const doc = document.documentElement;
		if (window.innerHeight + window.scrollY >= doc.scrollHeight - 2) {
			next = sections[sections.length - 1];
		} else {
			for (const s of sections) {
				if (s.getBoundingClientRect().top - offset <= 32) next = s;
			}
		}
		if (next === current) return;
		current = next;

		for (const a of links) {
			if (a.hash.slice(1) === current.id) {
				a.setAttribute("aria-current", "location");
				// Keep the active link visible when the bar scrolls sideways.
				if (a.parentElement === nav && nav.scrollWidth > nav.clientWidth) {
					nav.scrollTo({
						left: a.offsetLeft - (nav.clientWidth - a.offsetWidth) / 2,
						behavior: "smooth",
					});
				}
			} else {
				a.removeAttribute("aria-current");
			}
		}
	}

	let queued = false;
	function onScroll() {
		if (queued) return;
		queued = true;
		requestAnimationFrame(() => {
			queued = false;
			update();
		});
	}

	measure();
	update();
	window.addEventListener("scroll", onScroll, { passive: true });
	window.addEventListener("resize", () => {
		measure();
		current = null;
		update();
	});
})();
