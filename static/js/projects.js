// The /projects/ page: filter chips over the cards, a tilt toward the cursor on hover, each
// card's micro-animation (.site-pj-play), and a detail sheet (facet's .f-sheet) that opens from a
// card. facet's liquid module (data-f-liquid on the grid) adds the hover light and .is-hot.
// Opening a card puts its id in the URL hash, so /projects/#cairn opens it.
(function () {
	const root = document.querySelector(".site-pj-page");
	if (!root) return;

	const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
	const fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
	const cards = [...root.querySelectorAll(".site-pj-card")];

	// Hover (mouse only): play the card's animation and tilt it a little toward the cursor.
	for (const card of cards) {
		card.addEventListener("pointerenter", (e) => {
			if (e.pointerType === "mouse") card.classList.add("site-pj-play");
		});
		card.addEventListener("pointermove", (e) => {
			if (e.pointerType !== "mouse" || reduce) return;
			const r = card.getBoundingClientRect();
			card.style.setProperty("--site-pj-ry", (((e.clientX - r.left) / r.width - 0.5) * 5).toFixed(2) + "deg");
			card.style.setProperty("--site-pj-rx", ((0.5 - (e.clientY - r.top) / r.height) * 5).toFixed(2) + "deg");
		});
		card.addEventListener("pointerleave", () => {
			card.classList.remove("site-pj-play");
			card.style.removeProperty("--site-pj-rx");
			card.style.removeProperty("--site-pj-ry");
		});
	}

	// Touch screens have no hover: play each animation while its card is in view.
	if (!fine && "IntersectionObserver" in window) {
		const io = new IntersectionObserver(
			(entries) => entries.forEach((e) => e.target.classList.toggle("site-pj-play", e.isIntersecting)),
			{ threshold: 0.7 },
		);
		cards.forEach((c) => io.observe(c));
	}

	// Filter chips, with counts. The cards change at once and then glide from their old places
	// (FLIP), so the filter's result is never late.
	const filter = root.querySelector(".site-pj-filter");
	const chips = [...filter.querySelectorAll("button")];
	const projects = cards.filter((c) => c.dataset.tags !== "all");
	const matches = (card, f) => f === "all" || card.dataset.tags.split(" ").some((t) => t === f || t === "all");
	for (const b of chips) {
		b.querySelector("span").textContent = projects.filter((c) => matches(c, b.dataset.filter)).length;
	}
	for (const b of chips) {
		b.addEventListener("click", () => {
			chips.forEach((x) => x.setAttribute("aria-pressed", x === b));
			const before = new Map(cards.filter((c) => !c.hidden).map((c) => [c, c.getBoundingClientRect()]));
			cards.forEach((c) => (c.hidden = !matches(c, b.dataset.filter)));
			if (reduce) return;
			for (const c of cards) {
				if (c.hidden) continue;
				const was = before.get(c);
				const now = c.getBoundingClientRect();
				const frames = was
					? [{ translate: `${was.left - now.left}px ${was.top - now.top}px` }, { translate: "0 0" }]
					: [{ opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1 }];
				c.animate(frames, { duration: 380, easing: "cubic-bezier(0.2, 0.9, 0.3, 1)" });
			}
		});
	}
	filter.hidden = false;

	// Detail sheet: facet's .f-sheet gives the look, the entry animation and the scroll lock.
	const sheet = root.querySelector(".site-pj-sheet");
	const body = sheet.querySelector(".site-pj-sheet-body");

	function open(card) {
		const close = document.createElement("button");
		close.type = "button";
		close.className = "site-pj-close";
		close.setAttribute("aria-label", "Close");
		close.textContent = "✕";
		close.addEventListener("click", shut);
		const top = card.querySelector(".site-pj-top").cloneNode(true);
		top.classList.add("site-pj-play");
		body.replaceChildren(close, top, card.querySelector("template.site-pj-detail").content.cloneNode(true));
		body.querySelector(".site-pj-d-title").id = "site-pj-sheet-title";
		body.style.setProperty("--brand", card.style.getPropertyValue("--brand"));
		if (!sheet.open) sheet.showModal();
		body.parentElement.scrollTop = 0;
		history.replaceState(null, "", "#" + card.id);
	}

	// Closing drops the card from the URL at once (the dialog's close event comes a task later).
	const clearHash = () => location.hash && history.replaceState(null, "", location.pathname + location.search);
	function shut() {
		clearHash();
		sheet.close();
	}

	// Escape closes a modal dialog natively (cancel); a click outside the sheet's box closes it too.
	sheet.addEventListener("click", (e) => {
		const r = sheet.getBoundingClientRect();
		const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
		if (e.target === sheet && !inside) shut();
	});
	sheet.addEventListener("cancel", clearHash);
	sheet.addEventListener("close", clearHash);

	for (const card of cards) {
		if (!card.hasAttribute("data-has-detail")) continue;
		const hint = document.createElement("button");
		hint.type = "button";
		hint.className = "site-pj-hint";
		hint.textContent = "Details →";
		hint.setAttribute("aria-label", "Details: " + card.querySelector("h2").textContent.trim());
		hint.setAttribute("aria-haspopup", "dialog");
		hint.addEventListener("click", () => open(card));
		card.append(hint);
		card.addEventListener("click", (e) => {
			if (!e.target.closest("a, button")) open(card);
		});
	}

	const fromHash = () => {
		const id = decodeURIComponent(location.hash.slice(1));
		const card = id && document.getElementById(id);
		if (card && cards.includes(card) && card.hasAttribute("data-has-detail")) open(card);
	};
	addEventListener("hashchange", fromHash);
	fromHash();
})();
