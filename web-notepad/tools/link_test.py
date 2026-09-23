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
        ctx = await b.new_context(viewport={'width': 900, 'height': 800}); await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1500)
        await A.click('[data-mode=rendered]'); await A.wait_for_timeout(500)
        link = await A.evaluate("""() => { const a = [...document.querySelectorAll('#md a')].find(x => x.href.includes('claude.ai/new')); return a ? { text: a.textContent, href: a.getAttribute('href'), target: a.getAttribute('target'), rel: a.getAttribute('rel') } : null; }""")
        ok(link and link['text'] == 'Claude 새 대화창' and link['href'] == 'https://claude.ai/new', '서식 적용 화면에 링크 생성', str(link))
        ok(link and link['target'] == '_blank' and 'noopener' in (link['rel'] or ''), '새 탭으로 열리도록 설정')
        await A.click('[data-mode=plain]'); await A.wait_for_timeout(200)
        v = await A.eval_on_selector('#ta', 'e => e.value')
        line = [l for l in v.split('\n') if '새 대화창' in l][0]
        ok('https' not in line and line.startswith('2. Claude 새 대화창'), '서식 제거 보기에는 주소 없이 글자만', line[:30])
        await A.click('[data-mode=raw]'); await A.wait_for_timeout(200)
        r = await A.eval_on_selector('#ta', 'e => e.value')
        ok('[Claude 새 대화창](https://claude.ai/new)' in r, '마크다운 원본에는 링크 문법 그대로')
        print('   페이지 오류:', errs or '없음')
        await b.close()
asyncio.run(main())
