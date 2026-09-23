import asyncio, json
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
        print('── 더 새로운 판이 돌고 있을 때 (내 창이 오래된 창인 상황)')
        ctx = await b.new_context(viewport={'width': 900, 'height': 600})
        await ctx.add_init_script(script="window.__DEMO_PERIOD_MS = 4000;")
        await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.add_init_script(script="""
          localStorage.setItem('__mockdb', JSON.stringify({
            'notes/demo-home': { name: '', body: '# 새 판이 쓴 안내문\\n\\n링크 포함', createdAt: 0, updatedAt: Date.now(), by: 'newer' },
            'meta/demo': { lastReset: Date.now(), build: 9999999999999, readmeVersion: 'newer', by: 'newer' } }));""")
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(9000)
        body = await A.evaluate("() => JSON.parse(localStorage.getItem('__mockdb'))['notes/demo-home'].body")
        ok('새 판이 쓴 안내문' in body, '오래된 창이 새 안내문을 덮어쓰지 않음', body.split(chr(10))[0])
        ok('새로고침' in await A.inner_text('#demoNote'), '새로고침 안내로 바뀜', await A.inner_text('#demoNote'))
        print('   페이지 오류:', errs or '없음')
        await ctx.close()
        print('── 예전 판이 남긴 글이 있을 때 (내 창이 최신인 상황)')
        c2 = await b.new_context(viewport={'width': 900, 'height': 600})
        await c2.add_init_script(script="window.__DEMO_PERIOD_MS = 4000;")
        await c2.add_init_script(path='/home/claude/menu/mock.js')
        await c2.add_init_script(script="""
          localStorage.setItem('__mockdb', JSON.stringify({
            'notes/demo-home': { name: '', body: '# 예전 판 안내문', createdAt: 0, updatedAt: Date.now(), by: 'older' },
            'meta/demo': { lastReset: Date.now(), build: 1, readmeVersion: 'older', by: 'older' } }));""")
        await c2.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        B = await c2.new_page(); errs2 = []; B.on('pageerror', lambda e: errs2.append(str(e)))
        await B.goto('http://localhost:8765/notepad-demo.html'); await B.wait_for_timeout(3000)
        v = await B.eval_on_selector('#ta', 'e => e.value')
        ok('개발 목적' in v, '최신 창은 곧바로 새 안내문으로 되돌림', f'{len(v)}자')
        meta = await B.evaluate("() => JSON.parse(localStorage.getItem('__mockdb'))['meta/demo']")
        ok(meta['build'] > 1700000000000, '판 번호 기록', str(meta['build']))
        await B.wait_for_timeout(6000)
        v2 = await B.eval_on_selector('#ta', 'e => e.value')
        ok(v2 == v, '주기 초기화도 계속 정상')
        print('   페이지 오류:', errs2 or '없음')
        await b.close()
asyncio.run(main())
