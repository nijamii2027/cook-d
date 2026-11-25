(() => {
  'use strict';
  const details = document.querySelector('.visit-hours');
  if (!details) return;
  const summary = details.querySelector('summary');
  const panel = details.querySelector('.visit-timetable');
  const content = panel?.querySelector('dl');
  const page = details.closest('main');
  const footer = document.querySelector('.site-footer');
  if (!summary || !content || !page || !footer) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let expanded = details.open;
  let readingFlow = false;
  let offset = 0;
  let animation = 0;
  let compensate = false;

  function holdFlow() {
    if (readingFlow || getComputedStyle(page).position !== 'sticky') return;
    offset = Math.max(0, page.getBoundingClientRect().bottom - footer.getBoundingClientRect().top);
    page.style.setProperty('--hours-cover-offset', `${offset}px`);
    page.classList.add('hours-reading-flow');
    readingFlow = true;
  }

  function restoreCover() {
    if (!readingFlow || expanded || animation) return;
    const footerTop = footer.getBoundingClientRect().top;
    // At the resting position sticky and normal flow coincide. Once the footer
    // fills the screen the main is fully behind it and can safely pin again.
    if (footerTop < window.innerHeight && footerTop > 0) return;
    page.classList.remove('hours-reading-flow');
    page.style.removeProperty('--hours-cover-offset');
    readingFlow = false;
  }

  function toggle(open, immediate = false) {
    cancelAnimationFrame(animation);
    const from = details.open ? panel.getBoundingClientRect().height : 0;
    holdFlow();
    const fromOffset = offset;
    const initialScroll = window.scrollY;
    let requestedScroll = initialScroll;
    compensate = fromOffset > .5;
    // An explicit zero height is in place before native details reveals its body.
    panel.style.height = `${from}px`;
    details.open = true;
    expanded = open;
    summary.setAttribute('aria-expanded', String(open));
    details.dataset.hoursState = open ? 'opening' : 'closing';
    document.documentElement.classList.add('hours-changing');
    const full = content.getBoundingClientRect().height;
    const travel = Math.max(Math.abs((open ? full : 0) - from) / Math.max(1, full), fromOffset ? 1 : 0);
    const duration = immediate || reduced.matches ? 0 : Math.max(110, 360 * Math.sqrt(travel));
    const start = performance.now();

    function update(now) {
      const t = duration ? Math.min(1, Math.max(0,(now - start) / duration)) : 1;
      const eased = t * t * (3 - 2 * t);
      const target = open ? content.getBoundingClientRect().height : 0;
      panel.style.height = `${from + (target - from) * eased}px`;
      if (fromOffset) {
        // Reconcile an existing overlap one frame at a time. Main offset and
        // scroll move together, so the clicked summary stays under the pointer.
        // Let a new wheel, touch, or navigation input take control immediately.
        if (Math.abs(window.scrollY - requestedScroll) > 2) compensate = false;
        offset = fromOffset * (1 - eased);
        page.style.setProperty('--hours-cover-offset', `${offset}px`);
        if (compensate) {
          requestedScroll = Math.max(0, initialScroll - fromOffset + offset);
          const lenis = window.CookdMotion?.lenis;
          if (lenis) lenis.scrollTo(requestedScroll, { immediate:true, force:true });
          else window.scrollTo({top:requestedScroll, behavior:'instant'});
        }
      }
      if (t < 1) { animation = requestAnimationFrame(update); return; }
      animation = 0;
      details.open = open;
      panel.style.removeProperty('height');
      delete details.dataset.hoursState;
      document.documentElement.classList.remove('hours-changing');
      window.CookdMotion?.lenis?.resize();
      restoreCover();
    }
    update(start);
  }

  summary.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0) return;
    event.preventDefault();
    toggle(!expanded);
  });
  // Also support externally opened details, including browser find-in-page.
  details.addEventListener('toggle', () => {
    if (animation || details.open === expanded) return;
    expanded = details.open;
    summary.setAttribute('aria-expanded', String(expanded));
    if (expanded) toggle(true, true);
    else restoreCover();
  });
  const stopCompensating = () => { compensate = false; };
  window.addEventListener('wheel', stopCompensating, {passive:true});
  window.addEventListener('touchstart', stopCompensating, {passive:true});
  window.addEventListener('keydown', stopCompensating);
  window.addEventListener('scroll', restoreCover, {passive:true});
  window.addEventListener('resize', restoreCover);
  reduced.addEventListener('change', () => { if (animation && reduced.matches) toggle(expanded, true); });
  if (expanded) toggle(true, true);
})();
