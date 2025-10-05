/**
 *
 * @authors Tom Hu (h1994st@gmail.com)
 * @date    2017-04-11 14:24:56
 * @version 1.0
 */

(function(window, document) {
  function handleOutboundLinkClicks(event) {
    ga('send', 'event', {
      eventCategory: 'Click',
      eventAction: event.target.dataset.label,
      eventLabel: navigator.userAgent
    });
  }

  document.querySelectorAll('a[data-label]').forEach(function (element) {
    element.onclick = handleOutboundLinkClicks;
  });

  ga('send', 'event', {
    eventCategory: 'Visit',
    eventAction: 'Loaded',
    eventLabel: 'Datetime: ' + (new Date()).toString() + ', UA: ' + navigator.userAgent
  });
})(window, document);
