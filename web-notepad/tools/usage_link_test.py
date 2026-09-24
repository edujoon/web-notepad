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
        ctx = await b.new_context(viewport={'width': 900, 'height': 760}); await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1300)
        await A.click('[data-mode=rendered]'); await A.wait_for_timeout(500)
        a = await A.evaluate("""() => { const x = [...document.querySelectorAll('#md a')].find(e => e.href.includes('github.com/edujoon/web-notepad')); return x ? { text: x.textContent, href: x.href, target: x.target } : null; }""")
        ok(a and a['text'] == 'edujoon/web-notepad' and a['target'] == '_blank', 'USAGE 안내문의 프로젝트 링크', a['href'] if a else '없음')
        await A.click('#webClone'); await A.wait_for_function("!document.querySelector('#cloneCopy').disabled")
        dlg = await A.inner_text('#cloneLayer')
        href = await A.get_attribute('#cloneChatGPT', 'href')
        ok('코드와 제작 요청문을 복사해 ChatGPT에 붙여 넣으면' in dlg, '복제 안내 창에 사용 설명 포함')
        ok(href == 'https://chatgpt.com', 'ChatGPT 열기 주소', href)
        await A.click('#cloneClose')
        await A.click('[data-mode=raw]'); await A.wait_for_timeout(200)
        raw = await A.eval_on_selector('#ta', 'e => e.value')
        line = [l for l in raw.split('\n') if '프로젝트 저장소:' in l][0]
        ok('https://github.com/edujoon/web-notepad' in line, '마크다운 원본에서도 읽히는 프로젝트 링크', line[:72] + '…')
        await A.click('[data-mode=plain]'); await A.wait_for_timeout(200)
        v = await A.eval_on_selector('#ta', 'e => e.value')
        ok('claude.ai' not in v, '서식 제거 보기에는 주소가 드러나지 않음')
        print('   페이지 오류:', errs or '없음')
        await b.close()
asyncio.run(main())
