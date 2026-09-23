import asyncio, json, re, sys
from playwright.async_api import async_playwright
RESULTS = []
def ok(cond, name, detail=''):
    RESULTS.append((bool(cond), name, detail)); print(('✅ ' if cond else '❌ ') + name + (f'  ({detail})' if detail else ''))
async def route(r):
    u = r.request.url
    if 'marked' in u: await r.fulfill(path='/tmp/package/marked.min.js', content_type='application/javascript')
    elif 'dompurify' in u: await r.fulfill(path='/tmp/dp/package/dist/purify.min.js', content_type='application/javascript')
    else: await r.abort()
DOC = "# 장보기\n\n**사과** 3개, 사과 주스\n바나나와 사과\n" + "아주 긴 줄 " * 40 + "\n마지막 줄"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        ctx = await b.new_context(viewport={'width': 1000, 'height': 700})
        await ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
        await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []
        A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad.html'); await A.wait_for_timeout(500)
        val = lambda: A.eval_on_selector('#ta', 'e => e.value')
        sel = lambda: A.eval_on_selector('#ta', 'e => [e.selectionStart, e.selectionEnd]')
        clip = lambda: A.evaluate('navigator.clipboard.readText()')
        tabs = lambda: A.eval_on_selector_all('#tabs .tab-name', 'els => els.map(e => e.textContent)')
        active = lambda: A.eval_on_selector('#tabs .tab.active .tab-name', 'e => e.textContent')
        dbnotes = lambda: A.evaluate("() => Object.entries(JSON.parse(localStorage.getItem('__mockdb') || '{}')).map(([k, v]) => ({ id: k, name: v.name, body: v.body }))")
        async def menu(m, item):
            await A.click(f'.menu-btn:text-is("{m}")'); await A.wait_for_timeout(40)
            it = A.locator('.menu-pop:not([hidden]) .mi', has_text=re.compile('^✓?' + re.escape(item)))
            dis = await it.first.get_attribute('aria-disabled')
            await it.first.click(); await A.wait_for_timeout(120); return dis
        async def item_state(m, item):
            await A.click(f'.menu-btn:text-is("{m}")'); await A.wait_for_timeout(40)
            it = A.locator('.menu-pop:not([hidden]) .mi', has_text=re.compile('^✓?' + re.escape(item))).first
            st = (await it.get_attribute('aria-disabled'), await it.get_attribute('aria-checked'))
            await A.keyboard.press('Escape'); await A.wait_for_timeout(40); return st
        async def mode(m): await A.click(f'[data-mode={m}]'); await A.wait_for_timeout(60)
        async def rawtext(): await mode('raw'); v = await val(); await mode('plain'); return v
        async def select_text(t):
            await A.eval_on_selector('#ta', '(e, t) => { const i = e.value.indexOf(t); e.focus(); e.setSelectionRange(i, i + t.length); }', t)
        async def caret_after(t):
            await A.eval_on_selector('#ta', '(e, t) => { const i = e.value.indexOf(t) + t.length; e.focus(); e.setSelectionRange(i, i); }', t)
        async def dlg_answer(text=None, button='ok'):
            await A.wait_for_selector('#dlgLayer:not([hidden])', timeout=2000)
            if text is not None: await A.fill('#dlgInput', text)
            await A.click('#dlgOk' if button == 'ok' else '#dlgCancel'); await A.wait_for_timeout(150)

        await A.click('#ta'); await A.keyboard.insert_text(DOC); await A.wait_for_timeout(900)
        print('\n━━ 파일 메뉴 ━━')
        n0 = len(await tabs())
        await menu('파일', '새 메모'); t = await tabs()
        ok(len(t) == n0 + 1 and await val() == '', '새 메모 (메뉴)', f'탭 {n0}→{len(t)}개, 빈 편집기')
        await A.keyboard.insert_text('두 번째 메모'); await A.keyboard.press('Alt+n'); await A.wait_for_timeout(150)
        ok(len(await tabs()) == n0 + 2 and await val() == '', '새 메모 (Alt+N)', f'탭 {len(await tabs())}개')
        await menu('파일', '이름 바꾸기'); await dlg_answer('테스트 이름'); await A.wait_for_timeout(800)
        names = [x['name'] for x in await dbnotes()]
        ok(await active() == '테스트 이름' and '테스트 이름' in names, '이름 바꾸기', f'탭 이름: {await active()}, 저장소 반영: {"테스트 이름" in names}')
        await menu('파일', '메모 삭제'); await A.wait_for_timeout(600)
        ok(len(await tabs()) == n0 + 1 and await A.is_hidden('#dlgLayer'), '메모 삭제 (빈 메모는 확인 없이)', f'탭 {len(await tabs())}개, 지금 탭: {await active()}')
        await A.set_input_files('#fileInput', '/home/claude/menu/회의록.md'); await A.wait_for_timeout(600)
        ok(await active() == '회의록' and '안건 정리' in await val(), '파일 열기', f'탭 이름: {await active()}, 내용: {json.dumps((await val())[:22], ensure_ascii=False)}')
        await menu('파일', '서식 제거 텍스트로 저장'); d = (await A.evaluate('window.__downloads'))[-1]
        ok(re.fullmatch(r'\d{6}_\d{4}_메모\.txt', d['filename']) and '**' not in d['data'] and '# ' not in d['data'], '마크다운 없이 저장 (.txt)', f"{d['filename']}: {json.dumps(d['data'][:26], ensure_ascii=False)}")
        await menu('파일', '마크다운 원본으로 저장'); d = (await A.evaluate('window.__downloads'))[-1]
        ok(re.fullmatch(r'\d{6}_\d{4}_메모\.md', d['filename']) and d['data'].startswith('# 회의록') and '**안건**' in d['data'], '원본 저장 (.md)', f"{d['filename']}: {json.dumps(d['data'][:26], ensure_ascii=False)}")
        await menu('파일', '메모 삭제'); await A.wait_for_selector('#dlgLayer:not([hidden])')
        msg = await A.inner_text('#dlgMsg'); await dlg_answer(button='cancel')
        ok(await active() == '회의록', '메모 삭제 → 취소', f'확인 창: "{msg[:30]}…"')
        await menu('파일', '메모 삭제'); await dlg_answer(); await A.wait_for_timeout(600)
        ok('회의록' not in await tabs() and not any(x['name'] == '회의록' for x in await dbnotes()), '메모 삭제 → 확인', f'남은 탭: {await tabs()}')
        # back to the shopping list note
        await A.click('#tabs .tab-main >> nth=0'); await A.wait_for_timeout(150)
        ok(await active() == '장보기', '첫 메모로 돌아가기', await active())

        print('\n━━ 편집 메뉴 (마크다운 제거 보기) ━━')
        await caret_after('마지막 줄'); await A.keyboard.insert_text('!')
        await menu('편집', '실행 취소'); v1 = await val()
        await menu('편집', '다시 실행'); v2 = await val()
        ok(v1.endswith('마지막 줄') and v2.endswith('마지막 줄!'), '실행 취소 / 다시 실행 (메뉴)')
        await A.click('#ta'); await A.keyboard.press('Control+z'); a = await val(); await A.keyboard.press('Control+y'); bb = await val()
        ok(a.endswith('마지막 줄') and bb.endswith('마지막 줄!'), '실행 취소 / 다시 실행 (Ctrl+Z / Ctrl+Y)')
        await A.click('#fclose') if await A.is_visible('#findbar') else None
        await select_text('바나나'); await menu('편집', '잘라내기'); c = await clip(); r = await rawtext()
        ok(c == '바나나' and '바나나' not in await val() and '와 사과' in r, '잘라내기', f'클립보드: {c}')
        await A.click('#ta'); await A.keyboard.press('Control+z')
        ok('바나나와 사과' in await val(), '잘라내기 실행 취소')
        await select_text('주스'); await menu('편집', '복사'); c = await clip()
        ok(c == '주스' and '주스' in await val(), '복사', f'클립보드: {c}')
        await A.evaluate("navigator.clipboard.writeText('포도')"); await caret_after('사과 주스'); await menu('편집', '붙여넣기')
        ok('사과 주스포도' in await val(), '붙여넣기', json.dumps((await val()).split('\n')[2], ensure_ascii=False))
        await select_text('포도'); await menu('편집', '삭제')
        ok('포도' not in await val(), '삭제')
        await menu('편집', '찾기'); vis = await A.is_visible('#findbar')
        await A.fill('#fq', '사과'); await A.wait_for_timeout(100); c1 = await A.inner_text('#fcount')
        ok(vis and c1.endswith('/3'), '찾기 (메뉴)', f'결과 {c1}')
        await A.keyboard.press('Escape'); await A.wait_for_timeout(50); await A.keyboard.press('Control+f'); ok(await A.is_visible('#findbar') and await A.evaluate("document.activeElement.id") == 'fq', '찾기 (Ctrl+F) → 찾기 칸에 커서')
        await A.keyboard.press('Enter'); s1 = await A.inner_text('#fcount'); await A.keyboard.press('F3'); s2 = await A.inner_text('#fcount'); await A.keyboard.press('Shift+F3'); s3 = await A.inner_text('#fcount')
        ok(s1 != s2 and s3 == s1, '다음 찾기(F3) / 이전 찾기(Shift+F3)', f'{s1} → {s2} → {s3}')
        await menu('편집', '다음 찾기'); s4 = await A.inner_text('#fcount'); await menu('편집', '이전 찾기'); s5 = await A.inner_text('#fcount')
        ok(s4 != s1 and s5 == s1, '다음 찾기 / 이전 찾기 (메뉴)', f'{s1} → {s4} → {s5}')
        s = await sel(); v = await val(); ok(v[s[0]:s[1]] == '사과', '찾은 단어가 편집기에서 선택됨')
        await A.click('#fclose')
        await menu('편집', '바꾸기'); ok(await A.is_visible('#replrow'), '바꾸기 창 열림 (메뉴)')
        await A.fill('#fq', '바나나와'); await A.fill('#fr', '키위와'); await A.wait_for_timeout(80)
        await A.click('#frep'); await A.wait_for_timeout(120)
        ok('키위와' in await val(), '찾을 내용 입력 직후 바꾸기 한 번 클릭', json.dumps((await val()).split(chr(10))[3], ensure_ascii=False))
        if '키위와' in await val(): await A.click('#ta'); await A.keyboard.press('Control+z')
        await A.fill('#fq', '사과'); await A.fill('#fr', '배'); await A.wait_for_timeout(80)
        before = (await val()).count('사과')
        await A.click('#frep'); await A.wait_for_timeout(120); after1 = (await val()).count('사과')
        ok(after1 == before - 1, '바꾸기 버튼 한 번 → 하나 바뀜', f'사과 {before}개 → {after1}개')
        await A.click('#frepall'); await A.wait_for_timeout(150); r = await rawtext()
        ok((await val()).count('사과') == 0 and '**배**' in r, '모두 바꾸기 (굵은 글씨 서식 유지)', f'원본: {json.dumps(r.split(chr(10))[2][:14], ensure_ascii=False)}')
        await A.keyboard.press('Escape'); await A.click('#fclose') if await A.is_visible('#findbar') else None
        await menu('편집', '줄 이동'); await dlg_answer('4'); await A.wait_for_timeout(100)
        ok((await A.inner_text('#stPos')).startswith('줄 4,'), '줄 이동 (메뉴)', await A.inner_text('#stPos'))
        await A.keyboard.press('Control+g'); await dlg_answer('1'); ok((await A.inner_text('#stPos')) == '줄 1, 열 1', '줄 이동 (Ctrl+G)', await A.inner_text('#stPos'))
        await menu('편집', '모두 선택'); s = await sel(); ok(s == [0, len(await val())], '모두 선택', f'{s}')
        items = await A.eval_on_selector_all('.menu-pop .mi', 'els => els.map(e => e.textContent)')
        ok(not any('시간/날짜' in t for t in items), '시간/날짜 메뉴 없음')
        await caret_after('마지막 줄!')
        before_v = await val()
        r5 = await A.evaluate("() => { const t = document.getElementById('ta'); const e = new KeyboardEvent('keydown', { key: 'F5', code: 'F5', bubbles: true, cancelable: true }); t.dispatchEvent(e); return e.defaultPrevented; }")
        await A.keyboard.press('F5'); await A.wait_for_timeout(150)
        ok(r5 is False and await val() == before_v, 'F5를 앱이 가로채지 않음 (브라우저 새로고침으로 동작)', f'가로챔: {r5}, 내용 변화 없음')
        await A.click('#ta')
        print('\n━━ 편집 메뉴 (원본 보기) ━━')
        await mode('raw'); await select_text('배'); await menu('편집', '잘라내기'); c = await clip()
        ok(c == '배' and '****' in await val(), '원본 보기에서 잘라내기', 'raw: ' + json.dumps((await val()).split('\n')[2][:12], ensure_ascii=False))
        await menu('편집', '실행 취소'); ok('**배**' in await val(), '원본 보기에서 실행 취소')
        await A.keyboard.press('Control+h'); await A.fill('#fq', '**'); await A.fill('#fr', '__'); await A.click('#frepall'); await A.wait_for_timeout(120)
        ok('__배__' in await val(), '원본 보기에서 모두 바꾸기 (기호까지 바꿈)')
        await A.keyboard.press('Control+z') if False else None
        await A.click('#ta'); await A.keyboard.press('Control+z'); ok('**배**' in await val(), '모두 바꾸기도 실행 취소 한 번에 되돌림')
        await A.click('#fclose')

        print('\n━━ 편집 메뉴 (마크다운 적용 보기) ━━')
        await mode('rendered')
        st = {k: (await item_state('편집', k))[0] for k in ['잘라내기', '붙여넣기', '삭제', '복사', '찾기', '모두 선택']}
        ok(st['잘라내기'] == st['붙여넣기'] == st['삭제'] == 'true' and st['복사'] == st['찾기'] == st['모두 선택'] == 'false', '읽기 전용이라 편집 항목은 비활성', ', '.join(f'{k}:{"꺼짐" if v == "true" else "켜짐"}' for k, v in st.items()))
        await menu('편집', '모두 선택'); await menu('편집', '복사'); c = await clip()
        ok('장보기' in c and '마지막 줄' in c, '적용 보기에서 모두 선택 → 복사', json.dumps(c[:18], ensure_ascii=False))
        await menu('편집', '찾기'); ok(await A.get_attribute('[data-mode=plain]', 'aria-checked') == 'true' and await A.is_visible('#findbar'), '적용 보기에서 찾기 → 제거 보기로 전환해서 찾기')
        await A.click('#fclose')

        print('\n━━ 서식 메뉴 ━━')
        w0 = await A.eval_on_selector('#ta', 'e => [e.wrap, e.scrollWidth > e.clientWidth + 5]')
        await menu('서식', '자동 줄 바꿈'); w1 = await A.eval_on_selector('#ta', 'e => [e.wrap, e.scrollWidth > e.clientWidth + 5]'); c1 = (await item_state('서식', '자동 줄 바꿈'))[1]
        await menu('서식', '자동 줄 바꿈'); w2 = await A.eval_on_selector('#ta', 'e => [e.wrap, e.scrollWidth > e.clientWidth + 5]'); c2 = (await item_state('서식', '자동 줄 바꿈'))[1]
        ok(w0 == ['soft', False] and w1 == ['off', True] and w2 == ['soft', False] and c1 == 'false' and c2 == 'true', '자동 줄 바꿈 켜기/끄기', f'켬:{w0} → 끔:{w1}(가로 스크롤 생김) → 켬:{w2}')
        await menu('서식', '고정폭 글꼴'); f1 = await A.eval_on_selector('#ta', 'e => getComputedStyle(e).fontFamily'); k1 = await item_state('서식', '고정폭 글꼴')
        await menu('서식', '기본 글꼴'); f2 = await A.eval_on_selector('#ta', 'e => getComputedStyle(e).fontFamily'); k2 = await item_state('서식', '기본 글꼴')
        ok('Nanum Gothic Coding' in f1 and 'IBM Plex Sans KR' in f2 and k1[1] == 'true' and k2[1] == 'true', '글꼴 바꾸기 (고정폭 ↔ 기본)', f'{f1.split(",")[0]} ↔ {f2.split(",")[0]}')

        print('\n━━ 보기 메뉴 ━━')
        got = []
        for item, m in [('마크다운 원본', 'raw'), ('서식 적용 화면', 'rendered'), ('서식 제거 텍스트', 'plain')]:
            await menu('보기', item); got.append((await A.get_attribute(f'[data-mode={m}]', 'aria-checked')) == 'true' and (await item_state('보기', item))[1] == 'true')
        ok(all(got), '보기 방식 3가지 (메뉴, 체크 표시 포함)')
        got = []
        for key, m in [('Alt+2', 'raw'), ('Alt+3', 'rendered'), ('Alt+1', 'plain')]:
            await A.keyboard.press(key); await A.wait_for_timeout(60); got.append((await A.get_attribute(f'[data-mode={m}]', 'aria-checked')) == 'true')
        ok(all(got), '보기 방식 3가지 (Alt+1 텍스트 / Alt+2 마크다운 / Alt+3 미리보기)')
        order = await A.eval_on_selector_all('#seg [role=radio]', 'els => els.map(e => e.dataset.mode + ":" + e.querySelector(".l").textContent + "/" + e.querySelector(".s").textContent)')
        ok(order == ['plain:서식 제거 텍스트/텍스트', 'raw:마크다운 원본/마크다운', 'rendered:서식 적용 화면/미리보기'], '버튼 순서와 이름 (PC/모바일)', ' | '.join(order))
        await A.focus('[data-mode=plain]'); seq = []
        for _ in range(3): await A.keyboard.press('ArrowRight'); seq.append(await A.evaluate("document.activeElement.dataset.mode"))
        ok(seq == ['raw', 'rendered', 'plain'], '방향키로 보기 전환도 새 순서대로', ' → '.join(seq))
        await A.keyboard.press('Alt+1')
        fs = lambda: A.eval_on_selector('#ta', 'e => parseFloat(getComputedStyle(e).fontSize)')
        base = await fs(); await menu('보기', '확대'); z1 = (await A.inner_text('#stZoom'), await fs())
        await menu('보기', '축소'); await menu('보기', '축소'); z2 = (await A.inner_text('#stZoom'), await fs())
        await menu('보기', '기본 크기로'); z3 = (await A.inner_text('#stZoom'), await fs())
        ok(z1 == ('110%', base * 1.1) and z2[0] == '90%' and z3 == ('100%', base), '확대 / 축소 / 기본 크기로 (메뉴)', f'{z1[0]} → {z2[0]} → {z3[0]}')
        await A.click('#ta'); await A.keyboard.press('Control+='); a = await A.inner_text('#stZoom'); await A.keyboard.press('Control+-'); await A.keyboard.press('Control+-'); bq = await A.inner_text('#stZoom'); await A.keyboard.press('Control+0'); cq = await A.inner_text('#stZoom')
        ok((a, bq, cq) == ('110%', '90%', '100%'), '확대 / 축소 / 기본 크기로 (Ctrl + = / - / 0)', f'{a} → {bq} → {cq}')
        await menu('보기', '상태 표시줄'); h1 = await A.is_hidden('#status'); await menu('보기', '상태 표시줄'); h2 = await A.is_hidden('#status')
        ok(h1 and not h2, '상태 표시줄 숨기기/보이기')

        print('\n━━ 도움말 · 기타 ━━')
        await menu('도움말', '메모장 정보'); ok('JOON' in await A.inner_text('#aboutWho'), '메모장 정보'); await A.click('#aboutOk')
        await A.focus('.menu-btn >> nth=0'); await A.keyboard.press('Enter'); f1 = await A.evaluate('document.activeElement.textContent.trim()')
        await A.keyboard.press('ArrowDown'); f2 = await A.evaluate('document.activeElement.textContent.trim()')
        await A.keyboard.press('ArrowRight'); f3 = await A.evaluate('document.activeElement.textContent.trim()'); await A.keyboard.press('Escape')
        ok(f1.startswith('새 메모') and f2.startswith('파일 열기') and f3.startswith('실행 취소'), '키보드로 메뉴 이동 (Enter, ↓, →, Esc)', f'{f1[:5]} → {f2[:5]} → {f3[:5]}')
        # settings survive a reload; view resets to 마크다운 제거
        await menu('서식', '자동 줄 바꿈'); await menu('서식', '고정폭 글꼴'); await menu('보기', '확대'); await menu('보기', '상태 표시줄'); await mode('raw')
        await A.reload(); await A.wait_for_timeout(600)
        st = await A.evaluate("() => [document.getElementById('ta').wrap, getComputedStyle(document.getElementById('ta')).fontFamily.includes('Nanum'), document.getElementById('stZoom').textContent, document.getElementById('status').hidden, document.querySelector('[data-mode=plain]').getAttribute('aria-checked')]")
        ok(st == ['off', True, '110%', True, 'true'], '새로고침 후 설정 유지 (보기는 마크다운 제거로 시작)', str(st))
        await menu('서식', '자동 줄 바꿈'); await menu('서식', '기본 글꼴'); await menu('보기', '기본 크기로'); await menu('보기', '상태 표시줄')
        print('\n페이지 오류:', errs or '없음')
        print(f'\n결과: {sum(1 for r in RESULTS if r[0])}/{len(RESULTS)} 통과')
        await b.close()
asyncio.run(main())
