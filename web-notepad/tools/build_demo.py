import json, re, hashlib, time
clean = open('/mnt/user-data/outputs/notepad.html', encoding='utf-8').read()
readme = open('/mnt/user-data/outputs/README.md', encoding='utf-8').read().rstrip('\n')
version = hashlib.md5(readme.encode()).hexdigest()[:10]
build = int(time.time() * 1000)   # 최신 판 구분용 (오래된 창이 덮어쓰지 못하게)
def js_str(t):
    return json.dumps(t, ensure_ascii=False).replace('</script>', '<\\/script>')
demo = '''
<script>
/* 체험용 데모 전용 코드 — 배포용 파일(메모장-웹앱.html)에는 들어가지 않아요.
   1) 1분마다 메모를 처음 상태(README 한 장)로 되돌리기
   2) 앱 복제 버튼과 안내 창 (배포용 파일 원본을 그대로 품고 있다가 건네줘요) */
(() => {
  'use strict';
  const PERIOD = window.__DEMO_PERIOD_MS || 60 * 1000;
  const HOME = 'demo-home';
  const HOLDER = 'demo-' + Math.random().toString(36).slice(2, 10);
  const README = %README%;
  const VERSION = %VER%;  /* 안내문이 바뀌면 다음 주기를 기다리지 않고 바로 되돌려요 */
  const BUILD = %BUILD%;  /* 이 창이 몇 번째 판인지. 더 새 판이 돌고 있으면 이 창은 손을 떼요 */
  const APP_FILE = %APP%;
  const PROMPT = '첨부한 HTML 파일을 수정하지 말고 그대로 아티팩트로 게시해줘. 실시간 동기화용 db 기능과 파일 저장용 downloads 기능을 켜서 게시해줘.';
  const $ = (id) => document.getElementById(id);
  let db = null, downloads = null, timer = 0, last = 0, lastVer = null, lastBuild = 0, stale = false;

  const say = (msg) => {
    const el = $('toast'); if (!el) return;
    el.textContent = msg; el.classList.add('show');
    clearTimeout(say.t); say.t = setTimeout(() => el.classList.remove('show'), 2600);
  };

  /* ---------- 10분마다 처음 상태로 ---------- */
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
    await db.doc('notes/' + HOME).set({ name: '', body: README, createdAt: 0, updatedAt: now, by: 'demo-reset' });
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
      await db.doc('meta/demo').set({ lastReset: Date.now(), build: BUILD, readmeVersion: VERSION, by: HOLDER });
      setTimeout(() => { if (db) reset(Date.now()).catch(() => {}); }, 5000);
    } catch { schedule(30000); }
  }

  /* ---------- 앱 복제 ---------- */
  const CSS = `
.getapp { margin-left: auto; align-self: center; flex: 0 0 auto; display: flex; align-items: center; gap: 6px; height: 30px; padding: 0 13px 0 10px; border: 1px solid var(--carbon); border-radius: 7px; background: var(--carbon-soft); color: var(--carbon); font-size: 13px; font-weight: 600; white-space: nowrap; cursor: pointer; }
.getapp:hover { background: var(--carbon); color: var(--carbon-ink); }
.getapp:focus-visible { outline: 2px solid var(--carbon); outline-offset: 2px; }
.clone { width: min(460px, 100%); }
.clone .steps { margin: 0 0 16px; padding-left: 20px; font-size: 14px; line-height: 1.7; }
.clone .steps li { margin-bottom: 8px; }
.clone a { color: var(--carbon); text-underline-offset: 3px; }
.clone .prompt { display: block; margin-top: 6px; padding: 9px 11px; background: var(--hover); border-radius: 6px; font-family: var(--mono); font-size: 12.5px; line-height: 1.6; color: var(--muted); user-select: all; }
@media (max-width: 560px) { .getapp { padding: 0 10px 0 8px; } }`;
  const DIALOG = `<div class="dlg clone" role="dialog" aria-modal="true" aria-labelledby="cloneTitle">
    <h2 id="cloneTitle">내 메모장으로 복제하기</h2>
    <p>이 메모장을 그대로 복제해서, 나만의 메모장으로 쓸 수 있어요.</p>
    <ol class="steps">
      <li>아래 <b>HTML 파일 받기</b>를 눌러 파일을 받아요.</li>
      <li><a id="cloneNew" href="https://claude.ai/new" target="_blank" rel="noopener noreferrer">Claude 새 대화창</a>에 그 파일을 올리고, 아래 문구를 붙여넣어요.
        <code class="prompt" id="clonePrompt"></code>
      </li>
      <li>게시된 링크를 즐겨찾기에 넣고, 다른 기기에서도 같은 계정으로 열면 돼요.</li>
    </ol>
    <div class="dlg-actions">
      <button class="btn ghost" id="cloneClose">닫기</button>
      <button class="btn ghost" id="clonePromptCopy">문구 복사</button>
      <button class="btn primary" id="cloneGet">HTML 파일 받기</button>
    </div>
  </div>`;
  let layer = null;
  function build() {
    const style = document.createElement('style'); style.textContent = CSS; document.head.appendChild(style);
    const btn = document.createElement('button');
    btn.className = 'getapp'; btn.id = 'getApp'; btn.type = 'button';
    btn.title = '이 메모장을 내 것으로 복제하는 방법을 알려줘요';
    btn.setAttribute('aria-label', '앱 복제');
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="5.5" width="8.5" height="8.5" rx="1.6"/><path d="M10.5 5.5v-2A1.5 1.5 0 0 0 9 2H3.5A1.5 1.5 0 0 0 2 3.5V9a1.5 1.5 0 0 0 1.5 1.5h2"/></svg><span>앱 복제</span>';
    btn.addEventListener('click', open);
    document.querySelector('.top').appendChild(btn);
    layer = document.createElement('div');
    layer.className = 'dlg-layer'; layer.id = 'cloneLayer'; layer.hidden = true; layer.innerHTML = DIALOG;
    document.body.appendChild(layer);
    $('clonePrompt').textContent = PROMPT;
    /* 새 대화창을 열면서 문구까지 미리 채워 두려는 시도 (지원되지 않으면 빈 대화창만 열려요) */
    $('cloneNew').href = 'https://claude.ai/new?q=' + encodeURIComponent(PROMPT);
    $('cloneClose').addEventListener('click', close);
    $('cloneGet').addEventListener('click', download);
    $('clonePromptCopy').addEventListener('click', async () => say(await copy(PROMPT) ? '안내 문구를 복사했어요' : '복사하지 못했어요'));
    layer.addEventListener('mousedown', (e) => { if (e.target === layer) close(); });
    document.addEventListener('keydown', (e) => {
      if (layer.hidden) return;
      e.stopPropagation();
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'Tab') {
        e.preventDefault();
        const f = [$('cloneClose'), $('clonePromptCopy'), $('cloneGet')];
        f[(f.indexOf(document.activeElement) + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    }, true);
    const pop = document.querySelector('.menu .menu-pop');
    if (pop) {
      const sep = document.createElement('div'); sep.className = 'sep'; sep.setAttribute('role', 'separator');
      const mi = document.createElement('button');
      mi.className = 'mi'; mi.setAttribute('role', 'menuitem');
      mi.innerHTML = '<span></span><span>메모장 앱 복제하기…</span><kbd></kbd>';
      mi.addEventListener('click', open);
      pop.append(sep, mi);
    }
  }
  let prevFocus = null;
  function open() { if (!layer) return; prevFocus = document.activeElement; layer.hidden = false; setTimeout(() => $('cloneGet').focus(), 0); }
  function close() { if (!layer) return; layer.hidden = true; if (prevFocus && prevFocus.focus) prevFocus.focus({ preventScroll: true }); }
  async function copy(text) {
    try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(text); return true; } } catch {}
    try {
      const t = document.createElement('textarea');
      t.value = text; t.style.cssText = 'position:fixed;top:-1000px;opacity:0';
      document.body.appendChild(t); t.select();
      const okc = document.execCommand('copy'); t.remove(); return okc;
    } catch { return false; }
  }
  async function download() {
    if (downloads) {
      try { await downloads.save({ filename: '메모장-웹앱.html', data: APP_FILE }); say('메모장 앱 파일을 저장했어요'); close(); }
      catch (e) {
        const code = e && e.code;
        if (code === 'declined') return;
        say(code === 'rate_limited' ? '잠시 후 다시 시도해 주세요' : code === 'extension_not_enabled' || code === 'rejected_extension' ? '이 화면에서는 이 형식의 파일을 받을 수 없어요' : '파일로 저장하지 못했어요');
      }
      return;
    }
    try {
      const url = URL.createObjectURL(new Blob([APP_FILE], { type: 'text/html;charset=utf-8' }));
      const a = document.createElement('a');
      a.href = url; a.download = '메모장-웹앱.html'; a.style.display = 'none';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      say('메모장 앱 파일을 저장했어요'); close();
    } catch { say('이 화면에서는 파일로 저장할 수 없어요'); }
  }

  /* 안내문 안의 "바로가기" 링크가 해당 제목으로 이동하게 (체험용에서만) */
  function anchors() {
    const slug = (t) => t.trim().toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').replace(/\s+/g, '-');
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
    if (hasClaude) { try { downloads = await window.claude.use('downloads'); } catch { downloads = null; } }
    if (downloads || !hasClaude) build();
    if (!hasClaude) return;
    try { db = await window.claude.use('db'); } catch { db = null; }
    if (!db) return;
    notice();
    db.doc('meta/demo').onSnapshot((s) => {
      const d = s.exists ? (s.data() || {}) : {};
      last = Number(d.lastReset) || 0;
      lastVer = d.readmeVersion || null;
      lastBuild = Number(d.build) || 0;
      if (lastBuild > BUILD) { stepAside(); return; }
      schedule(lastBuild !== BUILD ? 300 : last ? last + PERIOD - Date.now() : 1000);
    }, () => schedule(60000));
  })();
})();
</script>
'''.replace('%README%', js_str(readme)).replace('%VER%', js_str(version)).replace('%BUILD%', str(build)).replace('%APP%', js_str(clean))
assert clean.count('</body>') == 1
open('/mnt/user-data/outputs/notepad-demo.html', 'w', encoding='utf-8').write(clean.replace('</body>', demo + '</body>'))
print('안내문 판 번호:', version)
print('체험용 파일 생성:', len(clean.replace('</body>', demo + '</body>')), '바이트')
