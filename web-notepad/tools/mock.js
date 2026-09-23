(() => {
  const KEY = '__mockdb', ch = new BroadcastChannel('mockdb');
  const load = () => JSON.parse(localStorage.getItem(KEY) || '{}');
  const save = (all) => localStorage.setItem(KEY, JSON.stringify(all));
  const listeners = new Set();
  const snap = () => ({ docs: Object.entries(load()).filter(([k]) => k.startsWith('notes/')).map(([k, v]) => ({ id: k.slice(6), exists: true, data: () => v })), metadata: { fromCache: false, hasPendingWrites: false } });
  const notify = () => { const s = snap(); listeners.forEach(fn => fn(s)); };
  ch.onmessage = () => notify();
  const leases = {};
  const ref = (path) => ({ id: path.split('/').pop(), path,
    async get() { const v = load()[path]; return { id: path.split('/').pop(), exists: v !== undefined, data: () => v }; },
    async acquire({ holder, ttlMs = 30000 }) {
      const now = Date.now(), L = JSON.parse(localStorage.getItem('__leases') || '{}');
      if (L[path] && L[path].until > now && L[path].holder !== holder) return { acquired: false };
      L[path] = { holder, until: now + ttlMs }; localStorage.setItem('__leases', JSON.stringify(L));
      return { acquired: true, holder };
    },
    onSnapshot(next) { const fn = () => { const v = load()[path]; next({ id: path.split('/').pop(), exists: v !== undefined, data: () => v }); }; listeners.add(fn); setTimeout(fn, 20); return () => listeners.delete(fn); },
    async set(d) { const all = load(); all[path] = JSON.parse(JSON.stringify(d)); save(all); notify(); ch.postMessage(1); },
    async delete() { const all = load(); delete all[path]; save(all); notify(); ch.postMessage(1); } });
  const db = { doc: ref, collection: (c) => ({ doc: (id) => ref(c + '/' + (id || Math.random().toString(36).slice(2, 12))),
    async get() { return { docs: Object.entries(load()).filter(([k]) => k.startsWith(c + '/')).map(([k, v]) => ({ id: k.slice(c.length + 1), exists: true, data: () => v })) }; },
    onSnapshot(next) { listeners.add(next); setTimeout(() => next(snap()), 30); return () => listeners.delete(next); } }) };
  window.__downloads = [];
  const downloads = { async save(r) { window.__downloads.push({ filename: r.filename, data: String(r.data) }); return { status: 'saved' }; } };
  window.claude = { use: async (n) => n === 'db' ? db : n === 'downloads' ? downloads : null };
})();
