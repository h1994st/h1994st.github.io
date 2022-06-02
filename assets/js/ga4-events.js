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
    element.onclick = handleOutboundLinkClicks
  });

  gtag('event', 'page_view', {
    event_category: 'Loaded',
    user_agent: navigator.userAgent,
    value: 'Datetime: ' + (new Date()).toString()
  });
})(window, document);
