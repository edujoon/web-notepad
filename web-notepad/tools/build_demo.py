import json, re, hashlib, time, sys
from pathlib import Path
sys.dont_write_bytecode = True
from build_app import build as build_app

root = Path(__file__).resolve().parents[1]
clean = build_app()
usage = (root / 'USAGE.md').read_text(encoding='utf-8').rstrip('\n')
version = hashlib.md5(usage.encode()).hexdigest()[:10]
build = int(time.time() * 1000)   # 최신 판 구분용 (오래된 창이 덮어쓰지 못하게)
def js_str(t):
    return json.dumps(t, ensure_ascii=False).replace('</script>', '<\\/script>')
demo = '''
<script>
/* 체험용 데모 전용 코드 — 배포용 파일에는 들어가지 않아요.
   1분마다 메모를 처음 상태(USAGE 안내 메모 한 장)로 되돌립니다.
   앱 복제는 배포용 빌드에 포함된, 복제 기능을 제거한 자체 포함 HTML을 그대로 사용합니다. */
(() => {
  'use strict';
  const PERIOD = window.__DEMO_PERIOD_MS || 60 * 1000;
  const HOME = 'demo-home';
  const HOLDER = 'demo-' + Math.random().toString(36).slice(2, 10);
  const USAGE = %USAGE%;
  const VERSION = %VER%;  /* 안내문이 바뀌면 다음 주기를 기다리지 않고 바로 되돌려요 */
  const BUILD = %BUILD%;  /* 이 창이 몇 번째 판인지. 더 새 판이 돌고 있으면 이 창은 손을 떼요 */
  window.__WEB_NOTEPAD_USAGE__ = USAGE;
  const $ = (id) => document.getElementById(id);
  let db = null, timer = 0, last = 0, lastVer = null, lastBuild = 0, stale = false;

  /* ---------- 1분마다 처음 상태로 ---------- */
  function notice() {
    const bar = $('status');
    if (!bar || $('demoNote')) return;
    const el = document.createElement('span');
    el.id = 'demoNote';
    el.textContent = '체험용 메모장이라 1분마다 처음 상태로 돌아가요';
    el.style.color = 'var(--carbon)';
    bar.insertBefore(el, bar.querySelector('.sync'));
  }
  const schedule = (ms) => { if (stale) return; clearTimeout(timer); timer = setTimeout(run, Math.max(1000, ms)); };
  function stepAside() {
    stale = true; clearTimeout(timer);
    const el = document.getElementById('demoNote');
    if (el) el.textContent = '새 버전이 나왔어요. 새로고침해 주세요';
  }
  async function reset(now) {
    const snap = await db.collection('notes').get();
    await db.doc('notes/' + HOME).set({ name: '웹 메모장 사용 가이드', body: USAGE, createdAt: 0, updatedAt: now, by: 'demo-reset' });
    for (const d of snap.docs) if (d.id !== HOME) { try { await db.doc('notes/' + d.id).delete(); } catch {} }
  }
  async function run() {
    if (!db) return;
    try {
      if (stale) return;
      const now = Date.now();
      if (lastBuild === BUILD && last && now - last < PERIOD - 500) { schedule(last + PERIOD - now); return; }
      const lock = await db.doc('meta/demo-lock').acquire({ holder: HOLDER, ttlMs: 20000 });
      if (!lock.acquired) { schedule(15000 + Math.random() * 15000); return; }
      const meta = await db.doc('meta/demo').get();
      const d = meta.exists ? (meta.data() || {}) : {};
      const seen = Number(d.lastReset) || 0, bld = Number(d.build) || 0;
      if (bld > BUILD) { stepAside(); return; }
      if (bld === BUILD && seen && Date.now() - seen < PERIOD - 500) { last = seen; lastBuild = bld; schedule(seen + PERIOD - Date.now()); return; }
      await reset(Date.now());
      await db.doc('meta/demo').set({ lastReset: Date.now(), build: BUILD, usageVersion: VERSION, by: HOLDER });
      setTimeout(() => { if (db) reset(Date.now()).catch(() => {}); }, 5000);
    } catch { schedule(30000); }
  }

  /* 안내문 안의 "바로가기" 링크가 해당 제목으로 이동하게 (체험용에서만) */
  function anchors() {
    const slug = (t) => t.trim().toLowerCase().replace(/[^\\p{L}\\p{N}\\s-]/gu, '').replace(/\\s+/g, '-');
    document.addEventListener('click', (e) => {
      const a = e.target.closest && e.target.closest('#md a[href^="#"]');
      if (!a) return;
      e.preventDefault(); e.stopPropagation();
      const want = decodeURIComponent(a.getAttribute('href').slice(1));
      const box = $('rendered');
      const h = [...document.querySelectorAll('#md h1, #md h2, #md h3, #md h4')].find((x) => slug(x.textContent) === want);
      if (h && box) box.scrollTop += h.getBoundingClientRect().top - box.getBoundingClientRect().top - 12;
    }, true);
  }

  (async () => {
    anchors();
    const hasClaude = !!(window.claude && window.claude.use);
    if (!hasClaude) return;
    try { db = await window.claude.use('db'); } catch { db = null; }
    if (!db) return;
    notice();
    db.doc('meta/demo').onSnapshot((s) => {
      const d = s.exists ? (s.data() || {}) : {};
      last = Number(d.lastReset) || 0;
      lastVer = d.usageVersion || d.readmeVersion || null;
      lastBuild = Number(d.build) || 0;
      if (lastBuild > BUILD) { stepAside(); return; }
      schedule(lastBuild !== BUILD ? 300 : last ? last + PERIOD - Date.now() : 1000);
    }, () => schedule(60000));
  })();
})();
</script>
'''.replace('%USAGE%', js_str(usage)).replace('%VER%', js_str(version)).replace('%BUILD%', str(build))
assert clean.count('</body>') == 1
output = root / 'demo' / 'notepad-demo.html'
output.write_text(clean.replace('</body>', demo + '</body>'), encoding='utf-8')
print('안내문 판 번호:', version)
print('체험용 파일 생성:', output, len(clean.replace('</body>', demo + '</body>')), '바이트')
