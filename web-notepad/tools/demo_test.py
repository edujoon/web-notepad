import asyncio
from playwright.async_api import async_playwright

def ok(c, n, d=''):
    print(('✅ ' if c else '❌ ') + n + (f'  ({d})' if d else ''))

CODE_START = '===== 실행 가능한 전체 HTML 시작 ====='
CODE_END = '===== 실행 가능한 전체 HTML 끝 ====='

async def route(r):
    u = r.request.url
    if 'marked' in u:
        await r.fulfill(path='/tmp/package/marked.min.js', content_type='application/javascript')
    elif 'dompurify' in u:
        await r.fulfill(path='/tmp/dp/package/dist/purify.min.js', content_type='application/javascript')
    else:
        await r.abort()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(viewport={'width': 1000, 'height': 700})
        await ctx.add_init_script(script='window.__DEMO_PERIOD_MS = 6000;')
        await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1800)
        val = lambda pg: pg.eval_on_selector('#ta', 'e => e.value')
        tabs = lambda pg: pg.eval_on_selector_all('#tabs .tab-name', 'els => els.map(e => e.textContent)')
        v = await val(A)
        ok(len(await tabs(A)) == 1 and v.startswith('웹 메모장 사용 가이드') and '세 가지 보기' in v, '처음 상태: USAGE 안내 메모 한 장', f'탭 {await tabs(A)}, {len(v)}자')
        ok(await A.is_visible('#demoNote'), '체험용 안내 표시', await A.inner_text('#demoNote') if await A.is_visible('#demoNote') else '')

        B = await ctx.new_page(); await B.goto('http://localhost:8765/notepad-demo.html'); await B.wait_for_timeout(600)
        await A.click('#ta'); await A.keyboard.press('Control+End'); await A.keyboard.insert_text('\n\n체험자가 쓴 글')
        await A.keyboard.press('Alt+n'); await A.wait_for_timeout(200); await A.keyboard.insert_text('두 번째 창')
        await B.keyboard.press('Alt+n'); await B.wait_for_timeout(200); await B.click('#ta'); await B.keyboard.insert_text('다른 창에서 만든 메모')
        await A.wait_for_timeout(1200)
        ok(len(await tabs(A)) == 3, '체험 중 상태 만들기', f'탭 {len(await tabs(A))}개')
        await A.wait_for_timeout(8000)
        ta, tb = await tabs(A), await tabs(B); va, vb = await val(A), await val(B)
        ok(len(ta) == 1 and len(tb) == 1, '설정 주기 초기화: 창이 여러 개여도 메모 한 장만 남음', f'A {ta} / B {tb}')
        ok(va == vb and va.startswith('웹 메모장 사용 가이드') and '체험자가 쓴 글' not in va and '두 번째' not in va, '내용도 USAGE 처음 상태로', f'{len(va)}자')

        await A.click('#webClone'); await A.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        await A.click('#cloneDownload'); await A.wait_for_timeout(300)
        bundle = (await A.evaluate('window.__downloads'))[-1]['data']
        html = bundle.split(CODE_START, 1)[1].split(CODE_END, 1)[0].strip('\n')
        ok('demo-home' not in html and '__DEMO_PERIOD_MS' not in html and 'demoNote' not in html, '복제 HTML에 체험용 코드가 없음')
        ok('const EMBEDDED_USAGE = "# 웹 메모장 사용 가이드' in html, '복제 HTML에 기본 USAGE 안내 포함')
        ok('id="webClone"' in html, '복제 HTML에도 웹 복제 기능 포함')
        print('   페이지 오류:', errs or '없음')

        open('/tmp/host/copy_demo.html', 'w', encoding='utf-8').write(html)
        c2 = await b.new_context()
        await c2.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        C = await c2.new_page(); await C.goto('http://localhost:8765/copy_demo.html'); await C.wait_for_timeout(700)
        ok((await val(C)).startswith('웹 메모장 사용 가이드'), '복제본의 내장 안내 메모 표시')
        await C.keyboard.press('Alt+n'); await C.wait_for_timeout(200); await C.click('#ta'); await C.keyboard.insert_text('복사본에 쓴 글'); await C.wait_for_timeout(6000)
        ok(await val(C) == '복사본에 쓴 글', '복제본은 초기화되지 않고 메모가 그대로 남음', await val(C))
        await b.close()

asyncio.run(main())
