import asyncio
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
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1500)
        ok('1분마다' in await A.inner_text('#demoNote'), '안내 문구', await A.inner_text('#demoNote'))
        v0 = await A.eval_on_selector('#ta', 'e => e.value')
        await A.click('#ta'); await A.keyboard.press('Control+End'); await A.keyboard.insert_text('\n\n체험자가 쓴 글')
        await A.keyboard.press('Alt+n'); await A.wait_for_timeout(300); await A.keyboard.insert_text('두 번째 메모')
        await A.wait_for_timeout(1500)
        mid = await A.eval_on_selector_all('#tabs .tab-name', 'els => els.length')
        await A.wait_for_timeout(62000)
        tabs = await A.eval_on_selector_all('#tabs .tab-name', 'els => els.length')
        v1 = await A.eval_on_selector('#ta', 'e => e.value')
        ok(mid == 2 and tabs == 1 and v1 == v0, '1분 뒤 처음 상태로 (탭 %d개 → %d개)' % (mid, tabs), f'{len(v1)}자')
        print('   페이지 오류:', errs or '없음')
        await b.close()
asyncio.run(main())
