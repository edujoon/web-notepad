import asyncio, urllib.parse
from playwright.async_api import async_playwright
def ok(c, n, d=''): print(('✅ ' if c else '❌ ') + n + (f'  ({d})' if d else ''))
async def route(r):
    u = r.request.url
    if 'marked' in u: await r.fulfill(path='/tmp/package/marked.min.js', content_type='application/javascript')
    elif 'dompurify' in u: await r.fulfill(path='/tmp/dp/package/dist/purify.min.js', content_type='application/javascript')
    else: await r.abort()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(viewport={'width': 900, 'height': 760}); await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1300)
        await A.click('[data-mode=rendered]'); await A.wait_for_timeout(500)
        a = await A.evaluate("""() => { const x = [...document.querySelectorAll('#md a')].find(e => e.href.includes('claude.ai/new')); return x ? { text: x.textContent, href: x.href, target: x.target } : null; }""")
        q = urllib.parse.unquote(a['href'].split('?q=')[1]) if a else ''
        ok(a and a['text'] == 'Claude 새 대화창' and a['target'] == '_blank' and q.startswith('첨부한 HTML'), '안내문 링크에 문구 담김', q[:30] + '…')
        dlg = await A.evaluate("""() => { const b = document.getElementById('getApp'); b.click(); const x = document.getElementById('cloneNew'); const h = x.href; document.getElementById('cloneClose').click(); return h; }""")
        ok(dlg == a['href'], '복제 안내 창 링크와 동일', '같음' if dlg == a['href'] else '다름')
        await A.click('[data-mode=raw]'); await A.wait_for_timeout(200)
        raw = await A.eval_on_selector('#ta', 'e => e.value')
        line = [l for l in raw.split('\n') if '새 대화창' in l][0]
        ok('%' not in line and 'claude.ai/new?q=첨부한' in line, '마크다운 원본에서도 읽히는 형태', line[:52] + '…')
        await A.click('[data-mode=plain]'); await A.wait_for_timeout(200)
        v = await A.eval_on_selector('#ta', 'e => e.value')
        ok('claude.ai' not in v, '서식 제거 보기에는 주소가 드러나지 않음')
        print('   페이지 오류:', errs or '없음')
        await b.close()
asyncio.run(main())
