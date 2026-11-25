(() => {
  'use strict';
  if (!('IntersectionObserver' in window)) return;

  const root = document.documentElement;
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  // Opt in before first paint, including a direct visit to #story.
  if (!preference.matches) root.classList.add('story-pen-ready');

  function mount() {
    const word = document.querySelector('.story-inkword');
    const paths = [...(word?.querySelectorAll('.story-ink-stroke') ?? [])];
    if (!paths.length) {
      root.classList.remove('story-pen-ready');
      return;
    }

    const lengths = paths.map(path => Number(path.dataset.length));
    const bodyLength = lengths.slice(0, -1).reduce((a, b) => a + b, 0);
    let duration = 0;
    const strokes = paths.map((path, index) => {
      const dot = index === paths.length - 1;
      if (dot) duration += 58; // Lift off the y flourish to dot the i.
      const time = dot ? 70 : 1150 * lengths[index] / bodyLength;
      const stroke = { path, start: duration, duration: time, last: -1 };
      duration += time;
      return stroke;
    });

    let playedThisVisit = false;
    let frame = 0;
    let began;

    function resetInk(ready) {
      cancelAnimationFrame(frame);
      began = undefined;
      root.classList.toggle('story-pen-ready', ready);
      for (const stroke of strokes) {
        stroke.last = -1;
        stroke.path.style.removeProperty('opacity');
        stroke.path.style.removeProperty('stroke-dashoffset');
      }
    }

    function draw(now) {
      if (began === undefined) began = now;
      const elapsed = now - began;
      if (elapsed >= duration) {
        resetInk(false);
        return;
      }
      for (const stroke of strokes) {
        if (elapsed < stroke.start || stroke.last === 1) continue;
        const phase = Math.min(1, (elapsed - stroke.start) / stroke.duration);
        if (stroke.last === phase) continue;
        stroke.path.style.opacity = '1';
        stroke.path.style.strokeDashoffset = String(1 - phase);
        stroke.last = phase;
      }
      frame = requestAnimationFrame(draw);
    }

    const entryRatio = .12;
    const observer = new IntersectionObserver(entries => {
      if (preference.matches) return;
      for (const entry of entries) {
        if (!entry.isIntersecting || entry.intersectionRatio === 0) {
          if (playedThisVisit) resetInk(true);
          playedThisVisit = false;
        } else if (!playedThisVisit && entry.intersectionRatio >= entryRatio) {
          playedThisVisit = true;
          frame = requestAnimationFrame(draw);
        }
      }
    }, { threshold: [0, entryRatio] });

    function syncPreference() {
      observer.disconnect();
      observer.takeRecords();
      playedThisVisit = false;
      resetInk(!preference.matches);
      if (!preference.matches) observer.observe(word);
    }
    preference.addEventListener('change', syncPreference);
    syncPreference();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });
  else mount();
})();
