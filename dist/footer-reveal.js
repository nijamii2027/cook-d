(() => {
  'use strict';
  const footer = document.querySelector('.site-footer');
  const page = footer?.previousElementSibling;
  if (page?.tagName !== 'MAIN' || !('ResizeObserver' in window)) return;

  function syncHeight() {
    const height = page.getBoundingClientRect().height;
    if (!height) return;
    page.style.setProperty('--footer-preceding-height', height + 'px');
    page.classList.add('footer-cover-ready');
  }

  const size = new ResizeObserver(syncHeight);
  size.observe(page, { box: 'border-box' });
  syncHeight();

  // Browsers can regard a tabbed-to link as already visible inside the sticky
  // page, even when the incoming opaque footer is over its rendered position.
  // Retreat to the link's natural document position in that case.
  function revealTarget(target, alignStart = false) {
    if (!target || !page.contains(target) || page.classList.contains('hours-reading-flow')) return;
    const edge = footer.getBoundingClientRect().top;
    const shift = page.getBoundingClientRect().bottom - edge;
    const rect = target.getBoundingClientRect();
    // The decorative wave extends above the opaque footer. Keep newly focused
    // controls clear of that leading edge as well as the footer rectangle.
    const wave = getComputedStyle(footer, '::after');
    const waveLead = wave.backgroundImage !== 'none' ? parseFloat(wave.height) || 0 : 0;
    if (shift < 1 || rect.bottom <= Math.max(0, edge - waveLead)) return;
    const current = window.scrollY;
    const destination = current + rect.top - shift -
      (alignStart ? 12 : Math.max(16, (window.innerHeight - rect.height) * .42));
    const top = Math.max(0, Math.min(destination, current - shift));
    // Lenis keeps its wheel target in sync with a keyboard or anchor jump.
    const smoothScroll = window.CookdMotion?.lenis;
    if (smoothScroll) smoothScroll.scrollTo(top, { immediate: true, force: true });
    else window.scrollTo({ top, behavior: 'instant' });
  }

  // Let native fragment navigation measure the page in normal flow. Once the
  // footer covers the sticky main, descendant rectangles are shifted by exactly
  // the reveal distance. A later hashchange cannot recover that displacement.
  footer.addEventListener('click', event => {
    if (page.classList.contains('hours-reading-flow')) return;
    if (event.defaultPrevented || event.button !== 0 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const link = event.target.closest('a[href]');
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href);
    if (!url.hash || url.origin !== location.origin || url.pathname !== location.pathname || url.search !== location.search) return;
    let id;
    try { id = decodeURIComponent(url.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target || !page.contains(target) || page.getBoundingClientRect().bottom - footer.getBoundingClientRect().top < 1) return;

    page.classList.remove('footer-cover-ready');
    requestAnimationFrame(() => {
      // Preserve the browser's URL, focus and history handling, including when
      // clicking the current fragment generates no hashchange event.
      if (!event.defaultPrevented && location.hash === url.hash) {
        target.scrollIntoView({ block: 'start', behavior: 'instant' });
        window.CookdMotion?.lenis?.scrollTo(window.scrollY, { immediate: true, force: true });
      }
      syncHeight();
    });
  });

  document.addEventListener('focusin', event => {
    const element = event.target;
    if (page.contains(element) && element.matches(':focus-visible')) {
      requestAnimationFrame(() => {
        if (document.activeElement === element) revealTarget(element);
      });
    }
  });

  function revealHash() {
    const hash = location.hash.slice(1);
    if (!hash) return;
    let id;
    try { id = decodeURIComponent(hash); } catch { return; }
    requestAnimationFrame(() => revealTarget(document.getElementById(id), true));
  }
  window.addEventListener('hashchange', revealHash);
  window.addEventListener('pageshow', syncHeight);
})();
