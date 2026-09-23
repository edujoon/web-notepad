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
        ctx = await b.new_context(); await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1500)
        v = await A.eval_on_selector('#ta', 'e => e.value')
        ok('개발 목적' in v, '새 안내문으로 시작', f'{len(v)}자')
        meta = await A.evaluate("() => JSON.parse(localStorage.getItem('__mockdb'))['meta/demo']")
        ok(bool(meta.get('readmeVersion')), '안내문 판 번호 저장', meta.get('readmeVersion'))
        # 예전 안내문이 남아 있고 초기화 시각이 방금인 상태를 그대로 흉내내기
        await A.evaluate("""() => { const all = JSON.parse(localStorage.getItem('__mockdb'));
          all['notes/demo-home'].body = '# 예전 안내문'; all['meta/demo'] = { lastReset: Date.now(), readmeVersion: 'old12345', by: 'x' };
          localStorage.setItem('__mockdb', JSON.stringify(all)); localStorage.removeItem('__leases'); }""")
        B = await ctx.new_page(); await B.goto('http://localhost:8765/notepad-demo.html'); await B.wait_for_timeout(3500)
        v = await B.eval_on_selector('#ta', 'e => e.value')
        ok('개발 목적' in v, '안내문이 바뀌면 10분을 기다리지 않고 바로 새 글로', f'{len(v)}자')
        await b.close()
asyncio.run(main())
