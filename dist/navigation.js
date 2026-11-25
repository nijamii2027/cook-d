(() => {
  'use strict';
  const root = document.documentElement;
  const main = document.querySelector('main');
  const footer = document.querySelector('.site-footer');
  const visit = document.getElementById('visit');
  const motion = matchMedia('(prefers-reduced-motion: no-preference)');
  const nativeCurtain = 'CSSViewTransitionRule' in window;
  let pendingURL = null;
  let coverTimer = 0;
  let recoveryTimer = 0;

  function pagePath(url) {
    return url.pathname.replace(/\/index\.html$/, '/').replace(/\/?$/, '/');
  }

  function sectionFor(hash) {
    if (!hash) return null;
    try { return document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch { return null; }
  }

  function letVisitRead() {
    if (!visit || !main || !footer || !motion.matches) return;
    // Release the sticky plate only when its natural and painted positions
    // coincide. A footer link can reach this point at the end of its scroll.
    if (Math.abs(main.getBoundingClientRect().bottom - footer.getBoundingClientRect().top) < 2) {
      main.classList.add('visit-anchor-reading');
      main.style.removeProperty('--visit-cover-delay');
    }
  }

  function resumeFooter() {
    if (!main?.classList.contains('visit-anchor-reading')) return;
    if (visit?.querySelector('.visit-hours[open]')) return;
    // Browser focus can centre a disclosure without scrolling its visitor.
    // Start the incoming footer wherever that focus operation left it.
    const overlap = Math.max(0, root.clientHeight - footer.getBoundingClientRect().top);
    if (overlap > 1) main.style.setProperty('--visit-cover-delay', overlap + 'px');
    main.classList.remove('visit-anchor-reading');
  }

  function clearFooterDelay() {
    if (!visit || !main.style.getPropertyValue('--visit-cover-delay')) return;
    const edge = footer.getBoundingClientRect().top;
    if (edge >= root.clientHeight || edge <= 0) main.style.removeProperty('--visit-cover-delay');
  }

  if (visit) {
    const releaseForScroll = () => {
      if (!visit.querySelector('.visit-hours[open]')) resumeFooter();
    };
    window.addEventListener('wheel', releaseForScroll, { passive: true });
    window.addEventListener('touchmove', releaseForScroll, { passive: true });
    window.addEventListener('keydown', event => {
      if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key) ||
          (event.key === ' ' && !event.target.closest('summary,button,input,textarea,select'))) releaseForScroll();
    });
    window.addEventListener('pointerdown', event => {
      if (event.target === root && event.clientX >= root.clientWidth) releaseForScroll();
    });
    window.addEventListener('scroll', clearFooterDelay, { passive: true });
  }

  function anchorPosition(target) {
    if (!target) return 0;
    const footerTop = footer?.getBoundingClientRect().top;
    const rect = target.getBoundingClientRect();
    const margin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0;
    const padding = parseFloat(getComputedStyle(root).scrollPaddingTop) || 0;
    if (target === visit && main.classList.contains('visit-anchor-reading')) {
      const inset = Math.max(padding, (root.clientHeight - rect.height) / 2);
      return Math.max(0, Math.round(window.scrollY + rect.top - inset));
    }
    let position = window.scrollY + rect.top - margin - padding;
    if (footer && main?.contains(target)) {
      // Once the footer moves over the sticky main, descendant rectangles are
      // offset from normal flow. The last anchor rests above that overlap.
      const shift = Math.max(0, main.getBoundingClientRect().bottom - footerTop);
      const startOfFooter = window.scrollY + footerTop;
      position = Math.min(position - shift, startOfFooter - root.clientHeight);
    }
    return Math.max(0, Math.round(position));
  }

  function focusDestination(target, previous) {
    if (document.activeElement !== previous && document.activeElement !== document.body) return;
    const element = target || document.querySelector('.site-header .brand');
    if (!element) return;
    if (element.tabIndex < 0 && !element.hasAttribute('tabindex')) {
      element.setAttribute('tabindex', '-1');
      element.addEventListener('blur', () => element.removeAttribute('tabindex'), { once: true });
    }
    element.focus({ preventScroll: true });
  }

  function scrollToLink(url, target, skipLink) {
    if (url.href !== location.href) history.pushState(null, '', url.href);
    const previous = document.activeElement;
    if (target === visit && visit) letVisitRead();
    else resumeFooter();
    const arrive = () => {
      if (target === visit && visit) letVisitRead();
      focusDestination(target, previous);
    };
    // The mobile drawer releases its scroll lock during the bubbling phase.
    requestAnimationFrame(() => {
      const top = anchorPosition(target);
      const lenis = window.CookdMotion?.lenis;
      const distance = Math.abs(top - window.scrollY);
      const immediate = !motion.matches || skipLink || distance < 2;
      if (lenis) {
        lenis.scrollTo(top, {
          immediate, force: true,
          duration: Math.min(1.18, .48 + .19 * Math.log1p(distance / window.innerHeight)),
          easing: p => p < .5 ? 4 * p ** 3 : 1 - ((-2 * p + 2) ** 3) / 2,
          onComplete: arrive
        });
      } else {
        window.scrollTo({ top, behavior: immediate ? 'instant' : 'smooth' });
        arrive();
      }
    });
  }

  function clearCurtain() {
    clearTimeout(coverTimer);
    clearTimeout(recoveryTimer);
    pendingURL = null;
    delete root.dataset.cookdCurtain;
  }

  function finishCover() {
    if (!pendingURL) return;
    const destination = pendingURL;
    pendingURL = null;
    clearTimeout(coverTimer);
    try {
      sessionStorage.setItem('cookd-curtain-arrival', JSON.stringify({
        url: destination, until: Date.now() + 10000
      }));
    } catch { /* The link still requests its destination. */ }
    // A canceled or stalled request must give the visitor the page back.
    recoveryTimer = setTimeout(clearCurtain, 2200);
    location.assign(destination);
  }

  function navigateWithFallback(event, url) {
    if (nativeCurtain || !motion.matches || !window.CSS?.registerProperty ||
        !['/', '/menu/'].includes(pagePath(url))) return;
    event.preventDefault();
    if (root.dataset.cookdCurtain === 'cover') return;
    clearCurtain();
    pendingURL = url.href;
    root.dataset.cookdCurtain = 'cover';
    coverTimer = setTimeout(finishCover, 720);
  }

  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
        event.shiftKey || event.altKey) return;
    const link = event.target.closest?.('a[href]');
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || !['https:', 'http:'].includes(url.protocol)) return;
    if (pagePath(url) !== pagePath(location) || url.search !== location.search) {
      navigateWithFallback(event, url);
      return;
    }
    const target = sectionFor(url.hash);
    if (url.hash && !target && url.hash !== '#top') return;
    event.preventDefault();
    clearCurtain();
    scrollToLink(url, target, link.classList.contains('skip-link'));
  }, true);

  document.addEventListener('animationend', event => {
    if (event.target !== root || event.pseudoElement !== '::before' ||
        event.animationName !== 'cookd-curtain') return;
    if (pendingURL) finishCover();
    else if (root.dataset.cookdCurtain === 'reveal') clearCurtain();
  });
  window.addEventListener('pagehide', clearCurtain);
  window.addEventListener('pageshow', event => {
    if (event.persisted) clearCurtain();
  });
  window.addEventListener('popstate', () => {
    clearCurtain();
    if (location.hash !== '#visit') resumeFooter();
    // Relinquish a moving wheel/anchor to native Back/Forward restoration.
    window.CookdMotion?.lenis?.reset();
  });
  motion.addEventListener('change', () => {
    if (pendingURL) finishCover();
    else clearCurtain();
  });

  function alignArrival() {
    const target = sectionFor(location.hash);
    if (!target || !main?.contains(target)) return;
    const lenis = window.CookdMotion?.lenis;
    function place() {
      const top = anchorPosition(target);
      if (Math.abs(window.scrollY - top) < 2) return;
      if (lenis) lenis.scrollTo(top, { immediate: true, force: true });
      else window.scrollTo({ top, behavior: 'instant' });
    }
    if (target === visit) {
      // Native fragment alignment may already have moved the footer over the
      // sticky main. Uncover it before releasing the section into normal flow.
      if (!main.classList.contains('visit-anchor-reading')) place();
      letVisitRead();
    }
    place();
  }

  // Correct the browser's initial deep-link position before the new snapshot
  // and once native fragment positioning and scroll restoration have finished.
  // History traversals retain the visitor's saved reading position.
  if (location.hash && performance.getEntriesByType('navigation')[0]?.type === 'navigate') {
    window.addEventListener('pagereveal', alignArrival, { once: true });
    window.addEventListener('pageshow', () => requestAnimationFrame(alignArrival), { once: true });
  }
})();
