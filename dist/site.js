(() => {
  const header = document.querySelector('.site-header');
  if (!header) return;
  const toggle = header.querySelector('.nav-toggle');
  const menu = header.querySelector('.mobile-nav');
  const scrim = header.querySelector('.nav-scrim');
  const contacts = [...header.querySelectorAll('.nav-contact')];
  let open = false;

  function closeContacts(except, restoreFocus = false) {
    contacts.forEach(contact => {
      if (!contact.open || contact === except) return;
      if (restoreFocus && contact.contains(document.activeElement)) {
        contact.querySelector('summary').focus({ preventScroll: true });
      }
      contact.open = false;
    });
  }

  function setOpen(value, restoreFocus = false) {
    closeContacts();
    open = value;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    menu.inert = !open;
    document.body.classList.toggle('nav-open', open);
    if (open) menu.querySelector('a').focus({ preventScroll: true });
    else if (restoreFocus) toggle.focus({ preventScroll: true });
  }

  toggle.addEventListener('click', () => setOpen(!open));
  scrim.addEventListener('click', () => setOpen(false, true));
  menu.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (link && !link.closest('.nav-contact')) setOpen(false);
  });

  contacts.forEach(contact => {
    contact.addEventListener('toggle', () => {
      if (contact.open) closeContacts(contact);
    });
  });
  document.addEventListener('pointerdown', event => {
    const isControl = event.target.closest('a[href],button,summary,input,textarea,select,[tabindex]');
    closeContacts(event.target.closest('.nav-contact'), !isControl);
  });
  document.addEventListener('focusin', event => {
    closeContacts(event.target.closest('.nav-contact'));
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (contacts.some(contact => contact.open)) {
        event.preventDefault();
        closeContacts(null, true);
        return;
      }
      if (open) {
        event.preventDefault();
        setOpen(false, true);
      }
    }
    if (open && event.key === 'Tab') {
      const items = [...menu.querySelectorAll('a[href],summary')].filter(item => item.getClientRects().length > 0 &&
        (item.matches('summary') || !item.closest('details:not([open])')));
      const last = items.at(-1);
      if (event.shiftKey && document.activeElement === toggle) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); toggle.focus(); }
    }
  });

  matchMedia('(min-width: 761px)').addEventListener('change', event => {
    closeContacts();
    if (event.matches && open) setOpen(false);
  });
  addEventListener('pageshow', () => {
    closeContacts();
    if (open) setOpen(false);
  });
})();
