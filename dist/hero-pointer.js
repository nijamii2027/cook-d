(() => {
  "use strict";
  const pointer = document.querySelector(".hero-pointer");
  const target = document.querySelector(".hero-pointer-target");
  if (!pointer || !target) return;

  const axis = pointer.querySelector(".hero-pointer-axis");
  const stroke = pointer.querySelector("animate");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  let scheduled = 0;

  function aim() {
    scheduled = 0;
    const start = pointer.getBoundingClientRect();
    const along = axis.getBoundingClientRect();
    const end = target.getBoundingClientRect();
    // The caption tilts independently of the wordmark. Subtract its rotation
    // so the extended tip points at the same patch of ink at every size.
    const caption = Math.atan2(along.y - start.y, along.x - start.x);
    const direction = Math.atan2(end.y - start.y, end.x - start.x);
    pointer.style.setProperty("--pointer-bearing", (direction - caption) + "rad");
  }
  function queueAim() {
    if (!scheduled) scheduled = requestAnimationFrame(aim);
  }
  const resize = new ResizeObserver(queueAim);
  [pointer.parentElement, target.parentElement, target.closest(".hero-type")].forEach(element => resize.observe(element));
  window.addEventListener("resize", queueAim, { passive: true });
  document.fonts?.ready.then(queueAim);
  queueAim();

  function setMotion() {
    if (reduced.matches) stroke.endElement?.();
    else stroke.beginElement?.();
  }
  reduced.addEventListener("change", setMotion);
  if (!reduced.matches) setMotion();
})();
