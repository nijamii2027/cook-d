(() => {
  'use strict';

  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const { gsap, ScrollTrigger, Lenis } = window;
  let lenis = null;
  let context = null;
  let prepare = null;
  let refreshFrame = 0;

  function refresh() {
    if (refreshFrame) return;
    refreshFrame = requestAnimationFrame(() => {
      refreshFrame = 0;
      prepare?.();
      lenis?.resize();
      ScrollTrigger?.refresh();
    });
  }

  window.CookdMotion = {
    get reduced() { return preference.matches; },
    get lenis() { return lenis; },
    refresh
  };

  function enable() {
    if (!gsap || preference.matches) return;
    if (ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
    const registered = new WeakSet();
    const triggered = new Set();
    const activeTweens = new Set();

    function animate(targets, mode) {
      if (!targets.length) return;
      const mask = mode === 'mask';
      const settings = mask
        ? { clipPath: 'inset(0 0 17% 0)', y: 9 }
        : { opacity: .54, y: mode === 'enter' ? 14 : 20 };

      // Reverting the finished tween restores any inline transform the designer set.
      const tween = gsap.from(targets, {
        ...settings,
        duration: mask ? .86 : .72,
        ease: 'power3.out',
        stagger: targets.length > 1 ? { each: Math.min(.062, .24 / targets.length) } : 0,
        onComplete() {
          activeTweens.delete(tween);
          tween.revert();
        }
      });
      activeTweens.add(tween);
    }

    function watch(target, mode, targets = [target]) {
      if (registered.has(target)) return;
      registered.add(target);
      const bounds = target.getBoundingClientRect();
      if (bounds.bottom <= 0 || !bounds.width || !bounds.height) {
        // Hidden content can be registered after opening via refresh().
        if (!bounds.width || !bounds.height) registered.delete(target);
        return;
      }
      if (bounds.top < window.innerHeight) {
        animate(targets, mode);
        return;
      }
      if (!ScrollTrigger) return;
      let trigger;
      trigger = ScrollTrigger.create({
        trigger: target,
        start: 'top 99%',
        once: true,
        onEnter() {
          triggered.delete(trigger);
          animate(targets, mode);
        }
      });
      triggered.add(trigger);
    }

    prepare = () => {
      const entrances = [...document.querySelectorAll('[data-enter]')].filter(target =>
        !registered.has(target) && target.getBoundingClientRect().width
      );
      for (const target of entrances) registered.add(target);
      const visible = entrances.filter(target => {
        const rect = target.getBoundingClientRect();
        return rect.bottom > 0 && rect.top < window.innerHeight;
      });
      animate(visible, 'enter');
      for (const target of document.querySelectorAll('[data-stagger]')) {
        const children = [...target.children].filter(child => !child.matches('[data-enter]'));
        watch(target, 'stagger', children);
      }
      for (const target of document.querySelectorAll('[data-reveal]')) {
        if (target.parentElement?.closest('[data-stagger]')) continue;
        watch(target, target.dataset.reveal);
      }
    };

    // Keep direct touch and keyboard scrolling native. Section links use this instance.
    if (Lenis) {
      lenis = new Lenis({ lerp: .15, smoothWheel: true, syncTouch: false, autoRaf: false });
      if (ScrollTrigger) lenis.on('scroll', ScrollTrigger.update);
    }

    const tick = seconds => lenis?.raf(seconds * 1000);
    if (lenis) gsap.ticker.add(tick);
    context = () => {
      prepare = null;
      gsap.ticker.remove(tick);
      for (const trigger of triggered) trigger.kill();
      for (const tween of activeTweens) tween.revert();
      lenis?.destroy();
      lenis = null;
      context = null;
    };
    prepare();
  }

  function updatePreference() {
    context?.();
    enable();
    refresh();
  }

  function start() {
    updatePreference();
    preference.addEventListener('change', updatePreference);
    window.addEventListener('pageshow', refresh);
    window.addEventListener('load', refresh, { once: true });
    document.fonts?.ready.then(refresh);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
