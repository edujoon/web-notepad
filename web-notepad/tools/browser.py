import asyncio, json
from playwright.async_api import async_playwright
C = json.load(open('/home/claude/qa/all.json', encoding='utf-8'))
async def route(r):
    u = r.request.url
    if 'marked' in u: await r.fulfill(path='/tmp/package/marked.min.js', content_type='application/javascript')
    elif 'dompurify' in u: await r.fulfill(path='/tmp/dp/package/dist/purify.min.js', content_type='application/javascript')
    else: await r.abort()
def ok(c, msg): print(('✅ ' if c else '❌ ') + msg)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(viewport={'width': 1000, 'height': 760})
        await ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []
        A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad.html'); await A.wait_for_timeout(400)
        val = lambda: A.eval_on_selector('#ta', 'e => e.value')
        async def mode(m): await A.click(f'[data-mode={m}]'); await A.wait_for_timeout(60)
        async def raw(): await mode('raw'); v = await val(); await mode('plain'); return v
        async def caret_after(text, extra=0):
            await A.eval_on_selector('#ta', '(e, t) => { const i = e.value.indexOf(t) + t.length; e.focus(); e.setSelectionRange(i, i); }', text)
        async def select(text):
            await A.eval_on_selector('#ta', '(e, t) => { const i = e.value.indexOf(t); e.focus(); e.setSelectionRange(i, i + t.length); }', text)

        # 1) paste everything into the default view (마크다운 제거) with a real paste
        print('\n[1] 기본 보기(마크다운 제거)에 마크다운 글 붙여넣기')
        await A.evaluate('t => navigator.clipboard.writeText(t)', C['all'])
        await A.click('#ta'); await A.keyboard.press('Control+v'); await A.wait_for_timeout(300)
        ok((await A.get_attribute('[data-mode=plain]', 'aria-checked')) == 'true', '처음 열면 마크다운 제거 보기')
        ok(await val() == C['plain'], '제거 보기 = 기호 제거 결과와 정확히 일치')
        r = await raw(); ok(r == C['all'], f'원본 보기 = 붙여넣은 원문 그대로 ({len(r)}자)')

        # 2) rendered view
        print('\n[2] 마크다운 적용 보기')
        await mode('rendered')
        info = await A.evaluate('''() => { const m = document.getElementById('md');
          const txt = [...m.querySelectorAll(':not(pre):not(code)')].map(e => [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('')).join('');
          return { h: m.querySelectorAll('h1,h2,h3,h4,h5,h6').length, strong: m.querySelectorAll('strong').length, em: m.querySelectorAll('em').length, del: m.querySelectorAll('del').length,
            li: m.querySelectorAll('li').length, table: m.querySelectorAll('table').length, pre: m.querySelectorAll('pre').length, a: m.querySelectorAll('a').length, bq: m.querySelectorAll('blockquote').length,
            cb: m.querySelectorAll('input[type=checkbox]').length, stars: (txt.match(/\\*\\*/g) || []).length, korean: [...m.querySelectorAll('strong')].map(e => e.textContent).filter(t => /따옴표|괄호/.test(t)) } }''')
        print('   ', info)
        ok(info['stars'] == 0, '코드 밖에 ** 기호가 남지 않음')
        ok(len(info['korean']) == 2, "**'따옴표'**를, **(괄호)**가 도 굵게 표시")
        ok(info['table'] == 3 and info['pre'] == 2 and info['cb'] == 3, '표 3개, 코드 블록 2개, 체크박스 3개')
        await A.screenshot(path='/home/claude/qa/v_rendered.png', full_page=False)

        # 3) editing in rendered view is blocked
        print('\n[3] 마크다운 적용 보기에서 편집 시도')
        before = C['all']
        await A.click('#md h2'); await A.keyboard.type('xyz'); await A.keyboard.press('Backspace'); await A.keyboard.press('Enter')
        await A.wait_for_timeout(100)
        ce = await A.evaluate("document.getElementById('md').isContentEditable")
        r = await raw(); ok(r == before and not ce, '타이핑해도 내용이 바뀌지 않음 (읽기 전용)')

        # 4) realistic edits in the default view
        print('\n[4] 마크다운 제거 보기에서 편집')
        await caret_after('중요'); await A.keyboard.insert_text('사항')
        r = await raw(); ok('**중요사항**한' in r, '굵은 글자 끝에 이어 쓰면 굵게 유지 → ' + r[r.index('**중요'):r.index('**중요')+12])
        await select('기울임'); await A.keyboard.insert_text('이탤릭')
        r = await raw(); ok('*이탤릭*' in r, '기울임 글자를 선택해 덮어쓰면 서식 유지')
        await caret_after('실시간 '); await A.keyboard.press('Enter')
        r = await raw(); seg = r[r.index('실시간'):r.index('실시간')+16]; ok('**실시간** \n**동기화**' in r, 'Enter로 굵은 글자를 나눠도 양쪽 모두 굵게 → ' + json.dumps(seg, ensure_ascii=False))
        await A.keyboard.press('Control+z'); r = await raw(); ok('**실시간 동기화**' in r, '실행 취소(Ctrl+Z)로 원래대로')
        await caret_after('문서'); await A.keyboard.insert_text('들')
        r = await raw(); ok('[문서](https://docs.example.com)들를' in r, '링크 끝에 이어 쓰면 링크 밖에 입력')
        await A.eval_on_selector('#ta', "e => { const i = e.value.indexOf('제목 2'); e.focus(); e.setSelectionRange(i, i); }"); await A.keyboard.press('Backspace')
        r = await raw(); ok('제목 1제목 2' in (await val()) and '# 제목 1제목 2' in r, '제목 줄 합치기(Backspace)도 보이는 그대로')
        await caret_after('• 첫째'); await A.keyboard.press('End'); await A.keyboard.insert_text(' 항목')
        r = await raw(); ok('- 첫째 항목' in r, '목록 항목 끝에 입력')
        await select('파이프 없는'); await A.keyboard.insert_text('새 값')
        r = await raw(); ok('새 값 | 표' in r, '표 칸 내용 바꾸기')
        await A.click('#ta'); await A.keyboard.press('Control+End'); await A.keyboard.press('Enter'); await A.keyboard.insert_text('끝에 쓴 한 줄')
        r = await raw(); ok(r.endswith('\n끝에 쓴 한 줄'), '문서 끝에 새 줄 입력')
        import re as _re
        await mode('plain'); v = await val()
        ok('**' not in v.split('def f(x)')[0].replace('**안 굵게**','') , '편집 후에도 제거 보기에 ** 없음(코드 제외)')

        # 5) copy-all in each view
        print('\n[5] 전체 복사')
        for m, label in [('plain', '제거'), ('rendered', '적용'), ('raw', '원본')]:
            await mode(m); await A.click('#copyAll'); await A.wait_for_timeout(120)
            clip = await A.evaluate('navigator.clipboard.readText()')
            if m == 'raw': ok(clip == await val(), f'{label} 보기: 원문 그대로 복사')
            elif m == 'plain': ok(clip == await val() and '**' not in clip.split('def f')[0].replace('**안 굵게**',''), f'{label} 보기: 기호 없이 복사')
            else:
                html = await A.evaluate('''async () => { const it = await navigator.clipboard.read(); const t = it[0].types; return t.includes('text/html') ? await (await it[0].getType('text/html')).text() : '' }''')
                ok('<strong>' in html and '<table>' in html, f'{label} 보기: 서식(HTML) 포함 복사, 일반 텍스트는 기호 없이')
            print('     안내:', await A.inner_text('#toast'))
        await mode('plain'); await A.eval_on_selector('#ta', 'e => e.scrollTop = 0'); await A.screenshot(path='/home/claude/qa/v_plain.png')
        await mode('raw'); await A.eval_on_selector('#ta', 'e => e.scrollTop = 0'); await A.screenshot(path='/home/claude/qa/v_raw.png')
        print('\n페이지 오류:', errs or '없음')
        await b.close()
asyncio.run(main())
