(() => {
  "use strict";

  const menu = document.querySelector(".menu-page");
  if (!menu) return;

  const bar = menu.querySelector(".menu-jump");
  const nav = bar.querySelector("nav");
  const links = [...nav.querySelectorAll("a[href^='#']")];
  const sections = links.map(link => document.getElementById(link.hash.slice(1)));
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let selected = -1;
  let scheduled = false;

  function updateCategory() {
    scheduled = false;
    const readingLine = bar.getBoundingClientRect().bottom + 30;
    let current = 0;
    for (let i = 1; i < sections.length; i += 1) {
      if (sections[i].getBoundingClientRect().top > readingLine) break;
      current = i;
    }
    if (selected === current) return;
    selected = current;
    links.forEach((link, i) => {
      if (i === current) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    if (nav.scrollWidth <= nav.clientWidth) return;
    const link = links[current];
    const rect = link.getBoundingClientRect();
    const box = nav.getBoundingClientRect();
    if (rect.left >= box.left + 2 && rect.right <= box.right - 2) return;
    nav.scrollTo({
      left: nav.scrollLeft + rect.left - box.left - (nav.clientWidth - link.offsetWidth) / 2,
      behavior: reducedMotion.matches ? "instant" : "smooth"
    });
  }

  function scheduleUpdate() {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(updateCategory);
    }
  }

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate, { passive: true });
  window.addEventListener("pageshow", scheduleUpdate);
  updateCategory();

  menu.addEventListener("toggle", event => {
    if (event.target.tagName === "DETAILS") {
      window.CookdMotion?.refresh?.();
      scheduleUpdate();
    }
  }, true);

  // Keep only the kitchen action a visitor can see playing.
  if ("IntersectionObserver" in window) {
    const sprites = [...menu.querySelectorAll(".cookd-sprite")];
    const visibleSprites = new Set();
    function updateSprites() {
      for (const sprite of sprites) {
        const running = visibleSprites.has(sprite) && !document.hidden && !reducedMotion.matches;
        sprite.style.animationPlayState = running ? "running" : "paused";
      }
    }
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) visibleSprites.add(entry.target);
        else visibleSprites.delete(entry.target);
      }
      updateSprites();
    }, { rootMargin: "40px" });
    sprites.forEach(sprite => observer.observe(sprite));
    document.addEventListener("visibilitychange", updateSprites);
    reducedMotion.addEventListener("change", updateSprites);
  }

  const { gsap, ScrollTrigger } = window;
  if (!gsap || !ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);

  gsap.matchMedia().add("(prefers-reduced-motion: no-preference)", () => {
    menu.querySelectorAll(".menu-section > h2").forEach(heading => {
      gsap.from(heading, {
        "--rule-reveal": 0, duration: .78, ease: "power2.out",
        scrollTrigger: { trigger: heading, start: "top 91%", once: true }
      });
    });

    // An editorial crop opens along the platter. The food itself eases into
    // a level serving position while all of its description remains readable.
    menu.querySelectorAll(".dish-picture").forEach((picture, i) => {
      const nearLeft = i % 2 === 0;
      const photo = picture.querySelector("img");
      gsap.timeline({ scrollTrigger: { trigger: picture, start: "top 93%", once: true } })
        .fromTo(picture, {
          clipPath: nearLeft ? "inset(0% 14% 0% 0% round 12% 24% 24% 12%)" : "inset(0% 0% 0% 14% round 24% 12% 12% 24%)"
        }, { clipPath: "inset(0% 0% 0% 0% round 0%)", duration: .82, ease: "power2.out", clearProps: "clipPath" }, 0)
        .from(photo, {
          xPercent: nearLeft ? 6 : -6, yPercent: 3, rotation: nearLeft ? 4 : -4,
          scale: 1.09, duration: 1.04, ease: "power3.out", clearProps: "transform"
        }, 0);
    });

    // Each row of the bakery display settles onto the shelf as it enters view.
    ScrollTrigger.batch(menu.querySelectorAll(".bake-picture img"), {
      start: "top 92%", once: true, interval: .08,
      onEnter: batch => gsap.fromTo(batch, { y: 18, rotation: -3.2 }, {
        y: 0, rotation: 0, stagger: .07, duration: .77, ease: "power3.out", clearProps: "transform"
      })
    });

    const pass = menu.querySelector(".menu-coffee-pass");
    const coffeeCups = pass.querySelectorAll(".menu-coffee-orders img");
    gsap.timeline({ scrollTrigger: { trigger: pass, start: "top 90%", once: true } })
      .from(coffeeCups[0], { xPercent: -38, rotation: -6, duration: .65, ease: "power2.out" }, 0)
      .from(coffeeCups[1], { xPercent: 38, rotation: 5, duration: .72, ease: "power3.out" }, .17)
      .fromTo(pass, { "--coffee-steam": 0 }, { "--coffee-steam": 1, duration: .6 }, .4);
  });
})();
