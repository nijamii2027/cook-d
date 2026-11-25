(() => {
  const { gsap, ScrollTrigger } = window;
  if (!gsap || !ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);
  const motion = gsap.matchMedia();
  motion.add('(prefers-reduced-motion: no-preference)', () => {
    const cleanups = [];
    const chapter = document.querySelector('.bakery-edition');
    if (!chapter) return;
    const onScreen = (element, animation) => {
      let visible = false;
      const update = () => animation.paused(!visible || document.hidden);
      const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; update(); });
      observer.observe(element);
      document.addEventListener('visibilitychange', update);
      cleanups.push(() => { observer.disconnect(); document.removeEventListener('visibilitychange', update); });
    };
    const scrub = (trigger, start = 'top bottom', end = 'bottom top') => ({
      trigger, start, end, scrub: .48, invalidateOnRefresh: true
    });
    document.querySelectorAll('.edition-title').forEach(heading => {
      gsap.from(heading.children, {
        yPercent: 25, rotation: -.85, transformOrigin: '10% 80%', stagger: .11, duration: .95, ease: 'power3.out',
        scrollTrigger: {trigger:heading, start:'top 94%', once:true}, clearProps:'transform'
      });
    });
    const print = chapter.querySelector('.bake-print');
    const proof = gsap.timeline({scrollTrigger:scrub(print,'top 94%','bottom 35%')});
    proof.fromTo(print.querySelector('img'), {scale:1.16, xPercent:-2.2, yPercent:1.4}, {scale:1, xPercent:0, yPercent:0, ease:'none'}, 0)
      .fromTo(print.querySelector('.paper-fold'), {scale:3.9}, {scale:1, ease:'power2.out'}, 0);
    gsap.fromTo('.bake-ink-impression',{rotation:-9,yPercent:9},{rotation:-3,yPercent:-3,ease:'none',scrollTrigger:scrub('.bake-layout')});
    gsap.from(chapter.querySelectorAll('.selection-strip figure img'), {
      yPercent:12, rotation:-11, stagger:.1, ease:'power3.out',duration:1.05,clearProps:'transform',
      scrollTrigger:{trigger:'.selection-strip',start:'top 91%',once:true}
    });

    const scene = document.querySelector('[data-coffee-service]');
    const cups = [...scene.querySelectorAll('.service-cup')];
    cups.forEach(cup => {cup.style.left='0';});
    const positions = cups.map(cup => ({
      x:gsap.quickSetter(cup,'x','px'),
      steam:gsap.quickSetter(cup.querySelectorAll('.steam i'),'opacity'),
      rise:gsap.quickSetter(cup.querySelector('.steam'),'y','px')
    }));
    let stageWidth = 0, cupWidth = 0;
    const beat = {time:0};
    const easeSlide = gsap.parseEase('sine.inOut');
    function paintService() {
      const step = beat.time * 3;
      const local = step % 1;
      const advance = (Math.floor(step) + easeSlide(Math.min(1,local/.7))) / 3;
      positions.forEach(({x,steam,rise},i) => {
        // Each cup occupies one place on the counter. All advance by one place, then settle together.
        const progress = (advance + i/3 + .167) % 1;
        x(-cupWidth + (stageWidth+cupWidth)*progress);
        const vapour = Math.max(0,1-Math.abs(progress-.5)*5.5) * (.65 + .32*Math.sin(step*Math.PI*4));
        steam(vapour*.8); rise(-6*vapour);
      });
    }
    const size = new ResizeObserver(() => {
      stageWidth=scene.clientWidth;cupWidth=cups[0].offsetWidth;paintService();
    });
    size.observe(scene);
    cleanups.push(() => {size.disconnect();cups.forEach(cup => {cup.style.removeProperty('left');});});
    onScreen(scene,gsap.to(beat,{time:1,duration:13,paused:true,repeat:-1,ease:'none',onUpdate:paintService}));
    gsap.fromTo('.coffee-panorama',{clipPath:'inset(6% 10% round 100vmax)'},{
      clipPath:'inset(0% 0% round 100vmax)',ease:'power1.out',scrollTrigger:scrub(scene,'top 95%','center 58%')
    });
    gsap.fromTo('.coffee-set-drawing img',{yPercent:7,rotation:-3},{
      yPercent:-3,rotation:1,ease:'none',scrollTrigger:scrub(scene)
    });

    const gallery=document.querySelector('[data-bagel-sequence]');
    gsap.fromTo('.bagel-print img',{scale:1.11,yPercent:-2},{
      scale:1.02,yPercent:0,ease:'none',scrollTrigger:scrub(gallery)
    });
    const printStack=gallery.querySelector('.bagel-proof');
    const sheets=[...printStack.querySelectorAll('.proof-sheet')].reverse();
    const cycle=gsap.timeline({repeat:-1,paused:true});
    // Deal one proof off the top and tuck it behind the other two.
    for (let i=0;i<3;i++) {
      const top=sheets[i], next=sheets[(i+1)%3], last=sheets[(i+2)%3],at=i*3.6;
      cycle.set(top,{zIndex:3,xPercent:0,yPercent:0,rotation:-4},at)
        .set(next,{zIndex:2,xPercent:13,yPercent:1,rotation:10},at)
        .set(last,{zIndex:1,xPercent:-13,yPercent:3,rotation:-12},at)
        .to(top,{xPercent:-75,yPercent:-11,rotation:-22,duration:.57,ease:'power2.inOut'},at+2.2)
        .to(next,{xPercent:0,yPercent:0,rotation:-4,duration:.63,ease:'power2.inOut'},at+2.26)
        .set(top,{zIndex:0},at+2.77)
        .to(top,{xPercent:-13,yPercent:3,rotation:-12,duration:.67,ease:'power2.inOut'},at+2.78)
        .to(last,{xPercent:13,yPercent:1,rotation:10,duration:.68,ease:'power2.inOut'},at+2.8);
    }
    onScreen(gallery,cycle);
    return () => cleanups.forEach(fn=>fn());
  });
})();
