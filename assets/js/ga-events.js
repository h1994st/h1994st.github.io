/**
 *
 * @authors Tom Hu (h1994st@gmail.com)
 * @date    2017-04-11 14:24:56
 * @version 1.0
 */

(function(window, document) {
  function handleOutboundLinkClicks(event) {
    ga('send', 'event', {
      eventCategory: 'Jump',
      eventAction: 'click',
      eventLabel: event.target.dataset.label
    });
  }

  document.querySelectorAll('a[data-label]').forEach(function (element) {
    element.onclick = handleOutboundLinkClicks;
  });
})(window, document);
