(() => {
  "use strict";

  const dishes = [
    ["Singapore Chilli Crab Omurice", "chilli-crab-omurice", "#f6d777"],
    ["Kaya & Shokupan Set", "kaya-shokupan", "#f5c4ac"],
    ["Tea-Smoked Duck Inaniwa Udon", "duck-udon", "#cee1ad"],
    ["Balinese Pork Satay", "pork-satay", "#efbd8b"],
    ["Matcha Almond Salt Bread", "matcha-almond-salt-bread", "#d3e4bd"],
    ["Lao Gan Ma Hot Honey Stracciatella", "stracciatella", "#f6cdaf"]
  ].map(([name, slug, tint]) => ({ name, src: "/media/original/assets/menu/" + slug + ".webp", tint }));
  const wrap = (v, n) => ((v % n) + n) % n;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const mix = (a, b, t) => a + (b - a) * t;
  const smooth = t => t * t * (3 - 2 * t);
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const svgNS = "http://www.w3.org/2000/svg";

  // Schedule work only while this particular drawing is visible.
  function observeMotion(element, paint) {
    let visible = false;
    let frame = 0;
    let last = 0;
    let elapsed = 0;
    function draw(now) {
      frame = 0;
      if (last) elapsed += Math.min(.07, (now - last) / 1000);
      last = now;
      paint(elapsed);
      if (visible && !document.hidden && !reduce.matches) frame = requestAnimationFrame(draw);
    }
    function update() {
      cancelAnimationFrame(frame);
      frame = 0;
      last = 0;
      if (visible && !document.hidden) {
        if (reduce.matches) paint(0);
        else frame = requestAnimationFrame(draw);
      }
    }
    const watcher = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; update(); });
    watcher.observe(element);
    document.addEventListener("visibilitychange", update);
    reduce.addEventListener("change", update);
    paint(0);
    return () => {
      cancelAnimationFrame(frame);
      watcher.disconnect();
      document.removeEventListener("visibilitychange", update);
      reduce.removeEventListener("change", update);
    };
  }

  class FoodScene extends HTMLElement {
    connectedCallback() {
      this.hero = this.closest(".cookd-landing");
      this.input = new AbortController();
      this.model = { position: 0 };
      this.selected = 0;
      this.nextAt = 7;
      this.manual = false;
      this.plates = dishes.map((dish, index) => {
        const plate = document.createElement("div");
        plate.className = "plate-portrait";
        const image = new Image(760, 580);
        image.alt = "";
        image.draggable = false;
        image.decoding = "async";
        if (!index) image.fetchPriority = "high";
        else if (index > 1 && index < dishes.length - 1) image.fetchPriority = "low";
        image.src = dish.src;
        plate.append(image);
        return plate;
      });
      this.replaceChildren(...this.plates);
      this.caption = this.hero.querySelector("[data-plate-name]");
      const opts = { signal: this.input.signal };
      this.hero.addEventListener("wheel", event => this.wheel(event), { ...opts, passive: false });
      this.caption.addEventListener("keydown", event => {
        if (event.ctrlKey || event.altKey || event.metaKey) return;
        let index;
        if (event.key === "ArrowRight") index = this.selected + 1;
        else if (event.key === "ArrowLeft") index = this.selected - 1;
        else if (event.key === "Home" || event.key === "End") {
          const wanted = event.key === "Home" ? 0 : dishes.length - 1;
          const delta = wrap(wanted - this.selected + dishes.length / 2, dishes.length) - dishes.length / 2;
          index = this.selected + delta;
        } else return;
        event.preventDefault();
        if (event.repeat) return;
        this.manual = true;
        this.move(index);
      }, opts);
      this.hero.addEventListener("pointerdown", event => {
        if (event.button || !event.isPrimary || event.target.closest("a,button,input,select,textarea")) return;
        this.drag = { id: event.pointerId, x: event.clientX, y: event.clientY, time: event.timeStamp, active: false };
      }, opts);
      window.addEventListener("pointermove", event => {
        const drag = this.drag;
        if (!drag || event.pointerId !== drag.id) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (!drag.active) {
          if (Math.abs(dy) > 7 && Math.abs(dy) > Math.abs(dx) * 1.08) { this.drag = null; return; }
          if (Math.abs(dx) < 8 || Math.abs(dx) < Math.abs(dy) * 1.2) return;
          drag.active = true;
          this.manual = true;
          this.tween?.kill();
          drag.from = this.model.position;
          drag.index = Math.round(drag.from);
        }
        const delta = clamp(-dx / (this.width * this.spacing), -1, 1);
        this.model.position = clamp(drag.from + delta, drag.index - 1, drag.index + 1);
        this.paint();
      }, opts);
      const finish = event => {
        const drag = this.drag;
        if (!drag || event.pointerId !== drag.id) return;
        this.drag = null;
        if (!drag.active) return;
        const dx = event.clientX - drag.x;
        const speed = Math.abs(dx) / Math.max(1, event.timeStamp - drag.time);
        const commit = event.type !== "pointercancel" &&
          (Math.abs(dx) > clamp(this.width * this.spacing * .14, 30, 68) || (Math.abs(dx) >= 16 && speed > .36));
        this.move(drag.index + (commit ? -Math.sign(dx) : 0));
      };
      window.addEventListener("pointerup", finish, opts);
      window.addEventListener("pointercancel", finish, opts);
      this.resize = new ResizeObserver(() => this.measure());
      this.resize.observe(this);
      this.measure();
      this.stop = observeMotion(this, time => {
        if (!this.manual && !this.drag && !reduce.matches && time >= this.nextAt) {
          this.nextAt = time + 7;
          this.move(this.selected + 1);
        }
      });
    }
    disconnectedCallback() { this.input.abort(); this.stop(); this.resize.disconnect(); this.tween?.kill(); }
    wheel(event) {
      if (event.ctrlKey || event.metaKey || event.altKey || this.drag?.active) return;
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? this.width : 1;
      const x = (event.shiftKey && Math.abs(event.deltaY) > Math.abs(event.deltaX) ? event.deltaY : event.deltaX) * unit;
      const y = event.shiftKey ? 0 : event.deltaY * unit;
      const now = event.timeStamp;
      if (!this.stroke || now - this.stroke.last > 185) {
        this.stroke = { axis: "", sum: 0, reverse: 0, fired: 0 };
      }
      const stroke = this.stroke;
      stroke.last = now;
      // Release at once when the user switches to a vertical scroll; Lenis and
      // the browser keep their ordinary page, touch and pinch-zoom behaviour.
      if (Math.abs(y) > Math.abs(x) * 1.18) {
        if (stroke.axis !== "x" || Math.abs(y) >= 5) {
          stroke.axis = "y";
          stroke.sum = stroke.reverse = 0;
        }
        return;
      }
      if (!x || Math.abs(x) < Math.abs(y) * 1.18) return;
      if (stroke.axis === "y" && Math.abs(x) < 3 * Math.abs(y)) return;
      if (stroke.axis === "y") stroke.fired = 0;
      stroke.axis = "x";
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
      const direction = Math.sign(x);
      if (stroke.fired) {
        // The inertial tail belongs to the original gesture. Only an intentional
        // sweep in the opposite direction can re-arm it before the idle gap.
        if (direction === stroke.fired) { stroke.reverse = 0; return; }
        stroke.reverse += Math.abs(x);
        if (stroke.reverse < 38) return;
      } else {
        stroke.sum += x;
        if (Math.abs(stroke.sum) < (event.deltaMode === 1 ? 16 : 24)) return;
      }
      stroke.fired = direction;
      stroke.reverse = stroke.sum = 0;
      this.manual = true;
      this.move(this.selected + direction);
    }
    measure() {
      this.width = this.clientWidth;
      this.height = this.clientHeight;
      const narrow = this.width < 700;
      this.diameter = Math.min(this.width * (narrow ? .94 : .52), this.height * (narrow ? .685 : .69), 735);
      this.spacing = narrow ? .64 : .415;
      this.centre = narrow ? .617 : .655;
      const title = this.hero.querySelector(".hero-type");
      const wordmark = this.hero.querySelector(".logo-stage");
      if (title && wordmark && this.height) {
        // Bottoms of the o counters in the original, including the wordmark's
        // rotation. Preserve the tall o's rim, with a smaller correction where
        // the foreground only brushes the bottom of the lower o.
        const wordWidth = wordmark.offsetWidth;
        const middle = title.offsetTop + title.offsetHeight / 2;
        const rim = Math.min(6, wordWidth * .009);
        const halfPlate = 290 / 760;
        const dishTop = this.height * this.centre - this.diameter * halfPlate;
        const tallOpening = middle + wordWidth * .081 + rim - dishTop;
        const lowerOpening = middle + wordWidth * .133 + rim - dishTop;
        const clearance = Math.max(0, tallOpening, Math.min(lowerOpening, this.height * .044));
        const trim = Math.min(this.diameter * (narrow ? .08 : .05), clearance);
        this.diameter -= trim;
        this.centre += (clearance - trim * halfPlate) / this.height;
      }
      this.plates.forEach(p => { p.style.width = this.diameter + "px"; });
      this.paint();
    }
    paint() {
      const n = dishes.length;
      const closest = wrap(Math.round(this.model.position), n);
      if (closest !== this.displayed) {
        this.displayed = closest;
        this.label(closest);
      }
      this.plates.forEach((plate, i) => {
        const delta = wrap(i - this.model.position + n / 2, n) - n / 2;
        const depth = Math.abs(delta);
        plate.hidden = depth > 1.8;
        if (plate.hidden) return;
        const x = this.width * (.5 + delta * this.spacing) - this.diameter / 2;
        const y = this.height * (this.centre + Math.min(depth, 1.6) ** 2 * .09) - this.diameter * 290 / 760;
        plate.style.zIndex = String(10 + Math.round(depth * 3));
        plate.style.transform = `translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0) rotate(${(delta * 7.8).toFixed(2)}deg) scale(${(1 - Math.min(depth, 1.6) * .14).toFixed(3)})`;
      });
    }
    label(index) {
      const dish = dishes[index];
      this.hero.style.setProperty("--dish-tint", dish.tint);
      this.caption.textContent = dish.name;
      this.caption.setAttribute("aria-valuenow", String(index + 1));
      this.caption.setAttribute("aria-valuetext", dish.name);
      this.dispatchEvent(new CustomEvent("cookd:dish", { bubbles: true, detail: { ...dish, index, total: dishes.length } }));
    }
    move(index) {
      this.selected = index;
      this.tween?.kill();
      if (reduce.matches || !window.gsap) {
        this.model.position = index;
        this.paint();
      } else {
        const duration = this.manual ? .3 + .33 * Math.min(1, Math.abs(index - this.model.position)) : 1.2;
        this.tween = gsap.to(this.model, { position: index, duration, ease: this.manual ? "power3.out" : "power3.inOut", onUpdate: () => this.paint() });
      }
    }
  }
  if (!customElements.get("food-scene")) customElements.define("food-scene", FoodScene);

  // Highest gently sloped patch on each of the five printed letter outlines,
  // measured in hero-wordmark.svg's 1546 × 586 viewBox (excluding punctuation).
  const perches = [
    { letter: "C", x: 380.5, y: 4.5 },
    { letter: "o", x: 542.5, y: 313.5 },
    { letter: "o", x: 713.5, y: 188.5 },
    { letter: "k", x: 840.5, y: 78.5 },
    { letter: "d", x: 1413.5, y: 31.5 }
  ];
  const firstPerch = 2;

  function shuffledTour(current, previous) {
    // Each bag visits every letter. Choose only routes with achievable spans,
    // including across the bag boundary; do not strand a distant last letter.
    const tours = [];
    function walk(at, used, route) {
      if (route.length === perches.length) {
        tours.push(route);
        return;
      }
      for (let i = 0; i < perches.length; i++) {
        if (used.has(i) || i === at || Math.abs(at - i) > 2) continue;
        if (Math.abs(perches[at].x - perches[i].x) > 725) continue;
        if (!route.length && i === previous) continue;
        walk(i, new Set([...used, i]), [...route, i]);
      }
    }
    walk(current, new Set(), []);
    return tours[Math.floor(Math.random() * tours.length)];
  }

  function playHops(actor, actions) {
    const first = actor.querySelector(".logo-bagel");
    const second = first.cloneNode(false);
    first.after(second);
    const wordWidth = 1546;
    const sheets = { hop: actions.hop.frames, "hop-turn": actions["hop-turn"].frames };
    const hero = actor.closest(".cookd-landing");
    let perch = firstPerch, previous = -1, facing = 1, bag = [], target = firstPerch;
    let phase = "rest", start = 0, length = .64, lastTime = 0;
    let scale = 1, cell = 1, ceiling = -120, parabola = null;
    const rand = (lo, hi) => mix(lo, hi, Math.random());
    const headAboveSole = Math.max(...sheets.hop.map(f => f.anchor[1] - f.bounds[1]));
    const poseAngle = (t, direction) => direction * 3.5 * Math.sin(Math.PI * 2 * t) * Math.sin(Math.PI * t);
    const transformed = (point, origin, direction, angle) => {
      const rad = angle * Math.PI / 180;
      const x = (point[0] - origin[0]) * cell * direction;
      const y = (point[1] - origin[1]) * cell;
      return { x: x * Math.cos(rad) - y * Math.sin(rad), y: x * Math.sin(rad) + y * Math.cos(rad) };
    };

    function trajectory() {
      const from = perches[perch], to = perches[target];
      const distance = Math.abs(to.x - from.x);
      const highLedge = Math.min(from.y, to.y);
      const peak = Math.min(highLedge - 3, Math.max(ceiling, highLedge - clamp(44 + distance * .105, 55, 112)));
      const up = Math.sqrt(from.y - peak), down = Math.sqrt(to.y - peak);
      // One ballistic curve across ledges of different heights; the apex falls
      // earlier when Bagel jumps down, and later when he springs up.
      return { from, to, peak, apex: up / (up + down), gravity: (up + down) ** 2,
        flight: clamp(.53 + Math.hypot(distance, to.y - from.y) / 1220, .62, 1.07) };
    }
    function drawCell(layer, name, frame, weight, foot, direction, angle) {
      if (weight < .001) { layer.style.opacity = "0"; return; }
      const info = sheets[name][frame];
      const origin = transformed(info.anchor, [0, 0], direction, angle);
      if (layer.dataset.sheet !== name) {
        layer.style.backgroundImage = "url('/media/mascot/" + name + ".webp')";
        layer.dataset.sheet = name;
      }
      if (layer.dataset.frame !== String(frame)) {
        layer.style.backgroundPosition = frame % 8 * 100 / 7 + "% " + Math.floor(frame / 8) * 20 + "%";
        layer.dataset.frame = String(frame);
      }
      layer.style.transform = 'translate3d(' + ((foot.x - origin.x) * scale).toFixed(3) + 'px,' +
        ((foot.y - origin.y) * scale).toFixed(3) + 'px,0) rotate(' + angle.toFixed(2) + 'deg) scaleX(' + direction + ')';
      layer.style.opacity = weight.toFixed(3);
    }
    function paint(name, frame, foot, direction, angle = 0) {
      const a = Math.floor(frame), b = Math.min(47, a + 1), f = frame - a;
      drawCell(first, name, a, 1 - f, foot, direction, angle);
      drawCell(second, name, b, f, foot, direction, angle);
    }
    function startHop() {
      phase = "hop";
      parabola = trajectory();
      length = .30 + parabola.flight + .32;
    }
    function advance() {
      start += length;
      if (phase === "hop") {
        previous = perch;
        perch = target;
        phase = "rest";
        length = rand(.30, .67);
      } else if (phase === "turn") {
        facing *= -1;
        startHop();
      } else {
        if (!bag.length) bag = shuffledTour(perch, previous);
        target = bag.shift();
        if (Math.sign(perches[target].x - perches[perch].x) !== facing) {
          phase = "turn";
          length = rand(.61, .76);
        } else startHop();
      }
    }
    function draw(time) {
      lastTime = time;
      if (reduce.matches) { paint("hop", 0, perches[firstPerch], 1); return; }
      while (time >= start + length) advance();
      const age = Math.max(0, time - start);
      if (phase === "rest") { paint("hop", 0, perches[perch], facing); return; }
      if (phase === "turn") { paint("hop-turn", smooth(age / length) * 47, perches[perch], facing); return; }
      if (age <= .30) {
        paint("hop", 14 * clamp(age / .30, 0, 1), perches[perch], facing);
        return;
      }
      const travel = (age - .30) / (length - .62);
      if (travel < 1) {
        const { from, to, peak, apex, gravity } = parabola;
        // Let horizontal momentum build over the last push and resolve as the
        // leading paw reaches forward. Keep the middle of the leap unhurried.
        const end = Math.min(travel, 1 - travel), edge = .15;
        const easedEnd = end < edge ? end * end / edge * (2 - end / edge) : end;
        const forward = travel < .5 ? easedEnd : 1 - easedEnd;
        const foot = { x: mix(from.x, to.x, forward), y: peak + gravity * (travel - apex) ** 2 };
        paint("hop", mix(14, 37, travel), foot, facing, poseAngle(travel, facing));
        return;
      }
      const landing = clamp((age - (length - .32)) / .32, 0, 1);
      paint("hop", mix(37, 47, landing), perches[target], facing);
    }
    function layout() {
      const w = parseFloat(getComputedStyle(actor).width);
      if (!w) return;
      scale = w / wordWidth;
      cell = parseFloat(getComputedStyle(first).width) / scale;
      const reserved = actor.getBoundingClientRect().top - hero.getBoundingClientRect().top;
      // Conservative across the whole rotated word. Including the actor's ink
      // bounds keeps the highest jump under the header on a short screen.
      ceiling = (9 - reserved) / scale + cell * (headAboveSole + .04);
      if (phase === "hop") parabola = trajectory();
      draw(lastTime);
    }
    actor.dataset.ready = "true";
    layout();
    const resize = new ResizeObserver(layout);
    resize.observe(actor);
    resize.observe(hero);
    const stop = observeMotion(actor, draw);
    return () => { stop(); resize.disconnect(); second.remove(); };
  }

  class BagelHop extends HTMLElement {
    async connectedCallback() {
      this.abort = new AbortController();
      const { signal } = this.abort;
      try {
        const [data] = await Promise.all([
          fetch("/media/mascot/hop.json", { signal }).then(res => {
            if (!res.ok) throw new Error("Missing hop registration");
            return res.json();
          }),
          ...["hop", "hop-turn"].map(name => {
            const image = new Image();
            image.src = "/media/mascot/" + name + ".webp";
            return image.decode();
          })
        ]);
        if (this.isConnected && !signal.aborted) this.stop = playHops(this, data.actions);
      } catch { /* The side-profile poster remains planted on its letter. */ }
    }
    disconnectedCallback() {
      this.abort?.abort();
      this.stop?.();
      this.removeAttribute("data-ready");
    }
  }
  if (!customElements.get("bagel-hop")) customElements.define("bagel-hop", BagelHop);

  function makeRibbon(wave) {
    const svg = wave.querySelector("svg");
    const line = wave.querySelector("#counter-wave-baseline");
    const fill = wave.querySelector(".counter-wave__ribbon");
    const text = wave.querySelector(".counter-wave__copy");
    const phrase = wave.querySelector(".counter-wave__fallback").textContent.trim();
    const make = (type, attrs = {}) => {
      const e = document.createElementNS(svgNS, type);
      Object.entries(attrs).forEach(([key, value]) => e.setAttribute(key, value));
      return e;
    };
    let width, height, amplitude, wavelength, tile, start, size, gap, items;
    let time = 0;
    let lastFrame = -1;
    const measure = make("text", { visibility: "hidden", class: "counter-wave__copy" });
    svg.append(measure);
    measure.textContent = phrase;
    function layout() {
      width = Math.max(280, wave.clientWidth);
      height = Math.max(70, wave.clientHeight);
      const small = width < 700;
      amplitude = small ? 5.5 : Math.min(13, height * .12);
      wavelength = small ? 390 : clamp(width * .64, 680, 1040);
      size = small ? clamp(width * .051, 18, 21) : clamp(width * .016, 22, 30);
      gap = small ? 30 : 54;
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      measure.style.fontSize = text.style.fontSize = size + "px";
      const phraseWidth = measure.getComputedTextLength();
      if (!phraseWidth) return;
      tile = phraseWidth + gap;
      start = -tile * 2;
      text.replaceChildren();
      items = [];
      const repeats = Math.ceil(width / tile) + 5;
      for (let i = 0; i < repeats; i++) {
        const phrasePath = make("textPath", { href: "#counter-wave-baseline" });
        phrasePath.textContent = phrase;
        text.append(phrasePath);
        items.push(phrasePath);
      }
      wave.classList.add("is-drawn");
      lastFrame = -1;
      paint(time);
    }
    function paint(seconds) {
      time = seconds;
      if (!items) return;
      const frame = Math.floor(seconds * 30);
      if (frame === lastFrame) return;
      lastFrame = frame;
      const phase = seconds * .57;
      const y = x => height * .5 + amplitude * Math.sin((x / wavelength) * Math.PI * 2 + phase);
      const step = wavelength / 12;
      const slope = x => amplitude * (2 * Math.PI / wavelength) * Math.cos(x / wavelength * 2 * Math.PI + phase);
      const end = width + tile * 2;
      // Cubic Hermite segments share both position and slope at every join.
      // Both edges and the type baseline use the same wave, so their spacing is exact.
      function path(offset, reverse = false, move = true) {
        const from = reverse ? end : start;
        const to = reverse ? start : end;
        const dir = reverse ? -1 : 1;
        let p = (move ? "M" : "L") + from.toFixed(2) + " " + (y(from) + offset).toFixed(2);
        for (let x = from; dir * (to - x) > .001;) {
          const nx = dir > 0 ? Math.min(x + step, to) : Math.max(x - step, to);
          const h = (nx - x) / 3;
          p += "C" + [x + h, y(x) + offset + h * slope(x), nx - h, y(nx) + offset - h * slope(nx), nx, y(nx) + offset].map(v => v.toFixed(2)).join(" ");
          x = nx;
        }
        return p;
      }
      const half = height * .285;
      fill.setAttribute("d", path(-half) + path(half, true, false) + "Z");
      line.setAttribute("d", path(size * .31));
      // Scrolling one whole measured phrase restores an exactly identical arrangement.
      const drift = reduce.matches ? 0 : wrap(seconds * (width < 700 ? 15 : 23), tile);
      items.forEach((node, index) => {
        node.setAttribute("startOffset", (index * tile - drift + gap * .50).toFixed(2));
      });
    }
    const resize = new ResizeObserver(layout);
    resize.observe(wave);
    layout();
    document.fonts?.ready.then(layout);
    observeMotion(wave, paint);
  }

  const wave = document.querySelector(".counter-wave");
  const hero = document.querySelector(".cookd-landing");
  if (wave) makeRibbon(wave);
  if (hero) {
    function parallax() {
      if (reduce.matches) hero.style.removeProperty("--hero-scroll");
      else hero.style.setProperty("--hero-scroll", Math.max(0, -hero.getBoundingClientRect().top).toFixed(2) + "px");
    }
    // Native scroll is also the source of truth while Lenis smooth-scroll is active.
    if (window.ScrollTrigger) ScrollTrigger.create({ trigger: hero, start: "top top", end: "bottom top", onUpdate: parallax, onRefresh: parallax });
    else window.addEventListener("scroll", parallax, { passive: true });
    reduce.addEventListener("change", parallax);
    parallax();
  }
})();
