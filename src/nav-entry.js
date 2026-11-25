// The fallback destination starts its reveal before the first painted frame.
try {
  if (!('CSSViewTransitionRule' in window) && CSS.registerProperty) {
    const key = 'cookd-curtain-arrival';
    const arrival = JSON.parse(sessionStorage.getItem(key));
    sessionStorage.removeItem(key);
    if (arrival && arrival.url === location.href && Date.now() < arrival.until &&
        matchMedia('(prefers-reduced-motion: no-preference)').matches) {
      document.documentElement.dataset.cookdCurtain = 'reveal';
      // The animation finishes transparent even if the deferred script fails.
      setTimeout(() => {
        if (document.documentElement.dataset.cookdCurtain === 'reveal') {
          delete document.documentElement.dataset.cookdCurtain;
        }
      }, 1500);
    }
  }
} catch { /* Storage may be unavailable in private or embedded browsing. */ }
