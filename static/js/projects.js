// The /projects/ page: a filter over the cards, a cursor spotlight and tilt on
// hover, each card's micro-animation (.pj-play), and a detail sheet that opens
// from a card and morphs out of it where view transitions are supported.
// Opening a card puts its id in the URL hash, so /projects/#cairn opens it.
(function () {
	const root = document.querySelector(".projects");
	if (!root) return;
	root.classList.add("pj-js");

	const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
	const fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
	const transition = (update) =>
		document.startViewTransition && !reduce ? document.startViewTransition(update) : (update(), null);
	const cards = [...root.querySelectorAll(".pj-card")];

	// Hover: spotlight follows the cursor, the card tilts a little toward it.
	for (const card of cards) {
		card.addEventListener("pointermove", (e) => {
			if (e.pointerType !== "mouse") return;
			const r = card.getBoundingClientRect();
			const x = e.clientX - r.left;
			const y = e.clientY - r.top;
			card.style.setProperty("--mx", x + "px");
			card.style.setProperty("--my", y + "px");
			if (!reduce) {
				card.style.setProperty("--ry", ((x / r.width - 0.5) * 5).toFixed(2) + "deg");
				card.style.setProperty("--rx", ((0.5 - y / r.height) * 5).toFixed(2) + "deg");
			}
		});
		card.addEventListener("pointerenter", (e) => {
			if (e.pointerType === "mouse") card.classList.add("pj-hot", "pj-play");
		});
		card.addEventListener("pointerleave", () => {
			card.classList.remove("pj-hot", "pj-play");
			card.style.setProperty("--rx", "0deg");
			card.style.setProperty("--ry", "0deg");
		});
	}

	// Touch screens have no hover: play each animation while its card is in view.
	if (!fine && "IntersectionObserver" in window) {
		const io = new IntersectionObserver(
			(entries) => entries.forEach((e) => e.target.classList.toggle("pj-play", e.isIntersecting)),
			{ threshold: 0.7 },
		);
		cards.forEach((c) => io.observe(c));
	}

	// Filter: counts, a sliding pill, and an animated reflow.
	const filter = root.querySelector(".pj-filter");
	const buttons = [...filter.querySelectorAll("button")];
	const pill = filter.querySelector(".pj-pill");
	const projects = cards.filter((c) => c.dataset.tags !== "all");
	const matches = (card, f) => f === "all" || card.dataset.tags.split(" ").some((t) => t === f || t === "all");
	for (const b of buttons) {
		b.querySelector("span").textContent = projects.filter((c) => matches(c, b.dataset.f)).length;
	}
	const movePill = () => {
		const b = filter.querySelector("[aria-pressed=true]");
		pill.style.width = b.offsetWidth + "px";
		pill.style.transform = `translateX(${b.offsetLeft}px)`;
	};
	for (const b of buttons) {
		b.addEventListener("click", () => {
			buttons.forEach((x) => x.setAttribute("aria-pressed", x === b));
			movePill();
			cards.forEach((c, i) => (c.style.viewTransitionName = "pj-c" + i));
			const t = transition(() => cards.forEach((c) => (c.hidden = !matches(c, b.dataset.f))));
			t?.finished.then(() => cards.forEach((c) => (c.style.viewTransitionName = "")));
		});
	}
	filter.hidden = false;
	movePill();
	addEventListener("resize", movePill);

	// Detail sheet.
	const dialog = root.querySelector(".pj-dialog");
	const sheet = dialog.querySelector(".pj-sheet");
	let from = null;

	function open(card) {
		from = card;
		cards.forEach((c) => (c.style.viewTransitionName = ""));
		card.style.viewTransitionName = "pj-open";
		transition(() => {
			card.style.viewTransitionName = "";
			const top = card.querySelector(".pj-top").cloneNode(true);
			const scroll = document.createElement("div");
			scroll.className = "pj-scroll";
			scroll.append(card.querySelector("template.pj-detail").content.cloneNode(true));
			scroll.querySelector(".pj-d-title").id = "pj-sheet-title";
			const close = document.createElement("button");
			close.type = "button";
			close.className = "pj-close";
			close.setAttribute("aria-label", "Close");
			close.textContent = "✕";
			close.addEventListener("click", shut);
			sheet.replaceChildren(close, top, scroll);
			sheet.style.setProperty("--brand", card.style.getPropertyValue("--brand"));
			sheet.style.viewTransitionName = "pj-open";
			dialog.showModal();
			top.classList.add("pj-play");
		});
		history.replaceState(null, "", "#" + card.id);
	}

	function shut() {
		if (!dialog.open) return;
		const card = from;
		const t = transition(() => {
			sheet.style.viewTransitionName = "";
			dialog.close();
			if (card && !card.hidden) card.style.viewTransitionName = "pj-open";
		});
		const done = () => card && (card.style.viewTransitionName = "");
		t ? t.finished.then(done) : done();
		history.replaceState(null, "", location.pathname + location.search);
	}

	dialog.addEventListener("cancel", (e) => {
		e.preventDefault();
		shut();
	});
	dialog.addEventListener("click", (e) => {
		if (e.target === dialog) shut();
	});

	for (const card of cards) {
		if (!card.querySelector("template.pj-detail")) continue;
		card.dataset.detail = "";
		const hint = document.createElement("button");
		hint.type = "button";
		hint.className = "pj-hint";
		hint.textContent = "Details →";
		hint.setAttribute("aria-label", "Details: " + card.querySelector("h2").textContent.trim());
		hint.setAttribute("aria-haspopup", "dialog");
		card.append(hint);
		card.addEventListener("click", (e) => {
			if (!e.target.closest("a")) open(card);
		});
	}

	const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
	if (target && target.dataset.detail !== undefined) open(target);
})();
