// Both copies advance as one track. The second is only a visual continuation;
// the accessible list and the manually scrollable static version have one copy.
(() => {
  const figure = document.querySelector('[data-food-procession]');
  if (!figure) return;
  const viewport = figure.querySelector('.tasting-window');
  const cycle = figure.querySelector('.tasting-cycle');
  const arrow = figure.querySelector('.tasting-squiggle');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let visible = false;
  let warmed = false;
  let duplicate;

  // Both animations share the plate track's clock. Line up the deepest point
  // of the gesture with a dish centre passing underneath the drawn arrowhead.
  function alignPoint() {
    if (!arrow || motion.matches) return;
    const count = cycle.children.length;
    const pitch = cycle.getBoundingClientRect().width / count;
    const matrix = arrow.getScreenCTM();
    if (!pitch || !matrix) return;
    const tip = new DOMPoint(9, 37).matrixTransform(matrix).x;
    const firstCentre = viewport.getBoundingClientRect().left + cycle.firstElementChild.getBoundingClientRect().width / 2;
    const phase = .29 + (tip - firstCentre) / pitch;
    figure.style.setProperty('--dish-beat', 'calc(var(--dish-crossing) / ' + count + ')');
    figure.style.setProperty('--point-phase', -(phase - Math.floor(phase)));
  }
  if (arrow) {
    arrow.addEventListener('animationend', event => {
      if (event.animationName === 'tasting-ink' && event.target.matches('.tasting-tip')) {
        figure.setAttribute('data-arrow-written', '');
      }
    });
    if ('ResizeObserver' in window) new ResizeObserver(alignPoint).observe(figure);
    else window.addEventListener('resize', alignPoint, {passive: true});
    document.fonts?.ready.then(alignPoint);
  }

  function warm() {
    if (warmed) return;
    warmed = true;
    cycle.querySelectorAll('img').forEach(img => { img.loading = 'eager'; });
  }

  function sync() {
    if (motion.matches) {
      figure.removeAttribute('data-loop');
      figure.removeAttribute('data-moving');
      viewport.tabIndex = 0;
      return;
    }
    viewport.removeAttribute('tabindex');
    if (!duplicate && warmed) {
      alignPoint();
      duplicate = cycle.cloneNode(true);
      duplicate.setAttribute('aria-hidden', 'true');
      duplicate.querySelectorAll('img').forEach(img => { img.alt = ''; });
      cycle.parentElement.append(duplicate);
    }
    if (duplicate && !figure.hasAttribute('data-loop')) viewport.scrollLeft = 0;
    figure.toggleAttribute('data-loop', Boolean(duplicate));
    figure.toggleAttribute('data-moving', visible && !document.hidden);
  }

  if ('IntersectionObserver' in window) {
    const ahead = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      ahead.disconnect();
      warm();
      sync();
    }, { rootMargin: '450px 0px' });
    ahead.observe(figure);
    new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }).observe(figure);
  } else {
    visible = true;
    warm();
  }
  motion.addEventListener('change', () => { alignPoint(); sync(); });
  document.addEventListener('visibilitychange', sync);
  sync();
})();

(() => {
  'use strict';

  const section = document.getElementById('story');
  const { gsap, ScrollTrigger } = window;
  if (!section || !gsap || !ScrollTrigger || !('IntersectionObserver' in window)) return;
  gsap.registerPlugin(ScrollTrigger);

  function activateArtwork() {
    const poses = [...section.querySelectorAll('.story-panel .story-pose')];
    let active = true;
    const observer = new IntersectionObserver(entries => {
      for (const { target, isIntersecting } of entries) {
        if (!isIntersecting) continue;
        observer.unobserve(target);
        const sprite = target.querySelector('.cookd-sprite');
        const atlas = new Image();
        const url = '/media/mascot/' + sprite.dataset.action + '.webp';
        atlas.onload = () => {
          if (!active) return;
          sprite.style.backgroundImage = "url('" + url + "')";
          target.classList.add('is-inked');
        };
        atlas.src = url;
      }
    }, { rootMargin: '450px 55%' });
    poses.forEach(pose => observer.observe(pose));
    return () => {
      active = false;
      observer.disconnect();
      poses.forEach(pose => {
        pose.classList.remove('is-inked');
        pose.querySelector('.cookd-sprite').style.removeProperty('background-image');
      });
    };
  }

  function coffeeRun() {
    const track = section.querySelector('.story-footway');
    const runner = track.querySelector('.story-courier');
    const pose = runner.querySelector('.story-pose');
    const canvas = pose.querySelector('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return () => {};
    const cell = canvas.width;
    const move = gsap.quickSetter(runner, 'x', 'px');
    const strideTime = .76;
    const sipTime = 1.05;
    // Pixel offsets in the 256px drawing, measured against each planted paw.
    // Once both feet plant the final value holds until the cup is lowered.
    const sipOffsets = [0, -1.5, -3.2, -2.3, 1.5, 6.1, 10.8, 15.4, 20, 24.7, 29.3, 33.9, 38.6, 43.2, 47.8, 52.4, 57.1, 61.7, 66.3, 71, 75.6, 80.2, 84.9, 89.5, 94.1, 95.3, 98.2, 102.1, 106.1, 109.4, 111, 111.1];
    const strideLength = sipOffsets.at(-1);
    let elapsed = 0;
    let from = .5, to = .5, facing = 1, strides = 1;
    let sip, carry;
    let active = true;
    let lastFrame = -1;
    let lastAtlas;
    let lastFacing;
    let width = 0;
    let size = 0;

    const preload = new IntersectionObserver(async ([entry]) => {
      if (!entry.isIntersecting) return;
      preload.disconnect();
      const load = name => {
        const image = new Image();
        image.src = '/media/mascot/' + name + '.webp';
        return image.decode().then(() => image);
      };
      // The first sheet can run by itself on a slow connection. Keep the
      // matching still visible until an entire decoded pose is on the canvas.
      const carryReady = load('sip-run').catch(() => null);
      sip = await load('sip').catch(() => null);
      if (!active || !sip) return;
      render();
      pose.classList.add('is-inked');
      carry = await carryReady;
    }, { rootMargin: '450px' });
    preload.observe(track);

    function measure() {
      width = track.clientWidth;
      size = runner.offsetWidth;
    }

    // Only change direction while the feet are planted after a sip. Take
    // fewer strides near an edge so the entire drawing stays in the frame.
    function planLap() {
      from = to;
      const stride = strideLength * size / (cell * Math.max(1, width - size));
      let room = facing > 0 ? 1 - from : from;
      if (room + 1e-7 < stride) {
        facing = -facing;
        room = 1 - room;
      }
      strides = Math.max(1, Math.min(carry ? 3 : 1, Math.floor(room / stride + 1e-7)));
      to = from + facing * Math.min(room, strides * stride);
    }

    function render() {
      const runTime = strideTime * strides;
      let atlas = sip;
      let frame;
      let distance;
      if (elapsed < strideTime) {
        frame = Math.min(23, Math.floor(elapsed / strideTime * 24));
        distance = sipOffsets[frame];
      } else if (elapsed < runTime) {
        // Join two level carrying strides while the cup is still down, then return
        // to the matching footfall in the sipping atlas.
        atlas = carry;
        const stride = (elapsed - strideTime) / strideTime;
        frame = Math.floor((stride % 1) * 48);
        distance = sipOffsets[24] + (Math.floor(stride) + frame / 48) * strideLength;
      } else {
        frame = Math.min(47, 24 + Math.floor((elapsed - runTime) / sipTime * 24));
        distance = (strides - 1) * strideLength + sipOffsets[Math.min(31, frame)];
      }
      const progress = distance / (strides * strideLength);
      const position = Math.max(0, Math.min(1, from + (to - from) * progress));
      move(position * Math.max(0, width - size));
      if (!atlas || (atlas === lastAtlas && frame === lastFrame && facing === lastFacing)) return;
      ctx.setTransform(facing, 0, 0, 1, facing < 0 ? cell : 0, 0);
      ctx.globalCompositeOperation = 'copy';
      ctx.drawImage(atlas, frame % 8 * cell, Math.floor(frame / 8) * cell, cell, cell, 0, 0, cell, cell);
      lastAtlas = atlas;
      lastFrame = frame;
      lastFacing = facing;
    }
    function tick(_time, deltaMs) {
      if (!sip || document.hidden) return;
      elapsed += Math.min(deltaMs / 1000, .08);
      const duration = strideTime * strides + sipTime;
      if (elapsed >= duration) {
        elapsed -= duration;
        planLap();
      }
      render();
    }

    measure();
    planLap();
    render();
    track.classList.add('is-running');
    const visibility = new IntersectionObserver(([entry]) => {
      gsap.ticker.remove(tick);
      if (entry.isIntersecting) gsap.ticker.add(tick);
    });
    visibility.observe(track);
    const resize = () => { measure(); render(); };
    window.addEventListener('resize', resize, { passive: true });
    return () => {
      active = false;
      visibility.disconnect();
      preload.disconnect();
      window.removeEventListener('resize', resize);
      gsap.ticker.remove(tick);
      track.classList.remove('is-running');
      runner.style.removeProperty('transform');
      pose.classList.remove('is-inked');
    };
  }

  function promises() {
    const reel = section.querySelector('.story-reel');
    const stage = reel.querySelector('.story-reel-window');
    const strip = reel.querySelector('.story-reel-strip');
    const panels = [...strip.children];
    const photo = panel => panel.querySelector('.story-illustration');
    const copy = panel => panel.querySelector('.story-panel-text');
    let timeline = null;
    let resizeFrame = 0;
    let disposed = false;

    const visiblePanels = new IntersectionObserver(entries => {
      for (const { target, isIntersecting } of entries) target.classList.toggle('is-playing', isIntersecting);
    });
    panels.forEach(panel => visiblePanels.observe(panel));

    function layout() {
      resizeFrame = 0;
      reel.classList.add('is-sticky');
      const fits = stage.clientHeight >= 415 && panels.every(panel =>
        panel.querySelector('.story-panel-inner').scrollHeight <= stage.clientHeight + 2
      );
      if (!fits) {
        timeline?.scrollTrigger?.kill();
        timeline?.revert();
        timeline = null;
        reel.classList.remove('is-sticky');
        return;
      }
      if (timeline) return;
      // The sticky window and its document-height parent supply the entire scroll range.
      // No wheel, touch or keyboard events need intercepting, including in reverse.
      timeline = gsap.timeline({
        scrollTrigger: {
          trigger: reel,
          start: 'top top',
          end: () => '+=' + (reel.offsetHeight - stage.offsetHeight),
          scrub: true,
          snap: {
            snapTo(progress) {
              // Only settle a partly crossed panel. Preserve the native reading space on each scene.
              for (const [start, end] of [[.36 / 2.39, 1.02 / 2.39], [1.36 / 2.39, 2.02 / 2.39]]) {
                if (progress > start && progress < end) return progress < (start+end)/2 ? start : end;
              }
              return progress;
            },
            inertia:false, directional:false, delay:.26, duration:{min:.14,max:.38}, ease:'power2.out'
          },
          invalidateOnRefresh: true
        }
      });
      for (let i = 1; i < panels.length; i++) {
        const at = (i - 1) + .36;
        timeline
          .to(strip, { xPercent: -100 * i, duration: .66, ease: 'sine.inOut' }, at)
          .to(photo(panels[i - 1]), { xPercent: 5, rotation: -3, duration: .62, ease: 'sine.inOut' }, at)
          .fromTo(photo(panels[i]), { xPercent: -8, rotation: 4 }, { xPercent: 0, rotation: 0, duration: .75, ease: 'power2.out' }, at)
          .fromTo(copy(panels[i]), { y: 16 }, { y: 0, duration: .59, ease: 'power2.out' }, at + .1);
      }
      timeline.to({}, { duration: .37 }, 2.02);
    }
    function resize() {
      if (!disposed && !resizeFrame) resizeFrame = requestAnimationFrame(layout);
    }

    layout();
    window.addEventListener('resize', resize, { passive: true });
    document.fonts?.ready.then(resize);
    return () => {
      disposed = true;
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(resizeFrame);
      timeline?.scrollTrigger?.kill();
      timeline?.revert();
      visiblePanels.disconnect();
      panels.forEach(panel => panel.classList.remove('is-playing'));
      reel.classList.remove('is-sticky');
    };
  }

  gsap.matchMedia().add('(prefers-reduced-motion: no-preference)', () => {
    const releaseArt = activateArtwork();
    const releaseRun = coffeeRun();
    const releasePromises = promises();
    return () => { releaseArt(); releaseRun(); releasePromises(); };
  });
})();
