// Analytics: <html data-f-ga4="G-XXXXXXXXXX"> loads Google Analytics 4 and sends one config,
// which records the page view (enhanced measurement in GA4 adds scrolls, outbound clicks and
// downloads). Nothing loads without a valid ID or when the browser sends Global Privacy Control.
// data-f-event="name" on any element sends that event on click, with link_url for links and
// label from data-f-label. Theme switches send theme_change. It runs once per page, whatever
// init is given; a blocked gtag script breaks nothing else.
const ID = /^G-[A-Z0-9]+$/;
const NAME = /^[a-z][a-z0-9_]{0,39}$/;
const warned = new Set();
let loaded = false;
let listening = false;

const gtag = (...args) => window.gtag(...args);

function onClick(e) {
  const el = e.target instanceof Element ? e.target.closest("[data-f-event]") : null;
  if (!el) return;
  const name = el.dataset.fEvent;
  if (!NAME.test(name)) {
    if (!warned.has(name)) {
      warned.add(name);
      console.warn(`facet: data-f-event "${name}" is not a GA4 event name; nothing sent.`, el);
    }
    return;
  }
  const params = {};
  const link = el.closest("a[href]");
  if (link) params.link_url = link.href;
  if (el.dataset.fLabel) params.label = el.dataset.fLabel;
  gtag("event", name, params);
}

function onTheme(e) {
  gtag("event", "theme_change", { theme: e.detail.theme });
}

export function init() {
  const id = document.documentElement.dataset.fGa4;
  if (!id || !ID.test(id) || navigator.globalPrivacyControl === true) return () => {};
  if (!loaded) {
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag =
      window.gtag ||
      function () {
        window.dataLayer.push(arguments);
      };
    gtag("js", new Date());
    gtag("config", id);
    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`;
    document.head.append(script);
  }
  if (listening) return () => {};
  listening = true;
  document.addEventListener("click", onClick);
  document.addEventListener("facet:theme", onTheme);
  return () => {
    document.removeEventListener("click", onClick);
    document.removeEventListener("facet:theme", onTheme);
    listening = false;
  };
}
