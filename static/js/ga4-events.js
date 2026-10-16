/**
 *
 * @authors Shengtuo Hu (h1994st@gmail.com)
 * @date    2022-06-02 16:29:04
 * @version 1.0
 */

(function(window, document) {
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  gtag('js', new Date());
  gtag('config', 'G-ZMH6NLL7C7');

  function handleOutboundLinkClicks(event) {
    gtag('event', 'stats', {
      event_category: 'Click',
      event_label: event.target.dataset.label,
      value: navigator.userAgent
    });
  }

  document.querySelectorAll('a[data-label]').forEach(function (element) {
    element.onclick = handleOutboundLinkClicks;
    element.target = '_blank';
    element.rel = 'noopener noreferrer';
  });
})(window, document);
