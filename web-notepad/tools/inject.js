// simulate a host that adds its own bits to the page
new MutationObserver((m, obs) => {
  const de = document.documentElement;
  if (de && !de.hasAttribute('data-theme')) { de.setAttribute('data-theme', 'light'); de.setAttribute('style', 'color-scheme: light'); }
  if (document.head && !document.getElementById('injected-runtime')) {
    const s = document.createElement('script'); s.id = 'injected-runtime'; s.textContent = 'window.__inj = 1'; document.head.appendChild(s);
  }
  if (document.body && !document.getElementById('host-banner')) {
    const d = document.createElement('div'); d.id = 'host-banner'; d.textContent = 'HOST'; document.body.prepend(d); obs.disconnect();
  }
}).observe(document, { childList: true, subtree: true });
