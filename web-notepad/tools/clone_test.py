import asyncio, re
from playwright.async_api import async_playwright

def ok(c, n, d=''):
    print(('✅ ' if c else '❌ ') + n + (f'  ({d})' if d else ''))

CLEAN = open('/mnt/user-data/outputs/notepad.html', encoding='utf-8').read()
CODE_START = '===== 실행 가능한 전체 HTML 시작 ====='
CODE_END = '===== 실행 가능한 전체 HTML 끝 ====='

def app_html(bundle):
    return bundle.split(CODE_START, 1)[1].split(CODE_END, 1)[0].strip('\n')

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
        print('── 배포용 파일 자체 점검')
        for word in ['id="webClone"', 'id="cloneLayer"', 'buildCloneKit', 'https://chatgpt.com']:
            ok(word in CLEAN, f'배포용 파일에 {word} 포함')
        ok(CLEAN.index('id="tabs"') < CLEAN.index('id="newTab"') < CLEAN.index('id="webClone"'), '탭 목록 → 새 메모 → 앱 복제 DOM 순서')
        ok('rel="icon"' in CLEAN and '%F0%9F%93%8B' in CLEAN, '📋 SVG data URL 파비콘 포함')
        ok('localStorage.getItem(LOCAL_NOTES_KEY)' not in CLEAN[CLEAN.index('async function buildCloneKit'):CLEAN.index('function getCloneKit')], '복제 생성기가 개인 메모를 읽지 않음')

        print('── 체험용 앱')
        ctx = await b.new_context(viewport={'width': 1000, 'height': 700})
        await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1200)
        ok(await A.is_visible('#webClone'), '앱 복제 버튼 보임')
        await A.click('#webClone'); await A.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        text = await A.inner_text('#cloneLayer')
        ok('내가 작성한 메모는 포함되지 않아요' in text and all(step in text for step in ['코드와 프롬프트 복사 또는 파일 다운로드', 'ChatGPT에 붙여넣기 또는 첨부', '생성 요청']), '앱 복제 안내 창의 개인정보 안내와 순서')
        ok(await A.get_attribute('#cloneChatGPT', 'href') == 'https://chatgpt.com', 'ChatGPT 열기 주소')
        await A.click('#cloneDownload'); await A.wait_for_timeout(300)
        d = (await A.evaluate('window.__downloads'))[-1]
        ok(d['filename'] == 'web-notepad-clone-kit.txt', 'UTF-8 복제 파일 받기', d['filename'])
        bundle = d['data']
        ok(bundle.count(CODE_START) == 1 and bundle.count(CODE_END) == 1, '코드 경계가 각각 한 번만 포함')
        ok('추가 질문 없이 즉시 실행 가능한 웹 메모장 전체 파일을 만들어 줘' in bundle and '앱 이름, 사용자 표시 이름, 대표 색상은 묻지 말고' in bundle, '사전 질문 없는 제작용 프롬프트 포함')
        ok('먼저 앱 이름·사용자 표시 이름·대표 색상을 한 번에 질문해 줘' not in bundle and '기본값으로 진행해 달라고' not in bundle, '이전 사전 질문 지시 제거')
        html = app_html(bundle)
        ok('demo-home' not in html and '__DEMO_PERIOD_MS' not in html and 'demoNote' not in html, '복제 HTML에 체험판 초기화 코드 없음')
        ok('const EMBEDDED_USAGE = "# 웹 메모장 사용 가이드' in html and 'id="webClone"' in html, '복제 HTML에 기본 가이드와 재복제 기능 포함')
        ok(html.index('id="tabs"') < html.index('id="newTab"') < html.index('id="webClone"') and '%F0%9F%93%8B' in html, '복제 HTML에 탭 뒤 + 버튼과 📋 파비콘 포함')
        print('   페이지 오류:', errs or '없음')

        open('/tmp/host/copy_clean.html', 'w', encoding='utf-8').write(html)
        print('── 복제한 앱')
        c2 = await b.new_context(viewport={'width': 1000, 'height': 700})
        await c2.add_init_script(path='/home/claude/menu/mock.js')
        await c2.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        C = await c2.new_page(); errs2 = []; C.on('pageerror', lambda e: errs2.append(str(e)))
        await C.goto('http://localhost:8765/copy_clean.html'); await C.wait_for_timeout(700)
        ok(await C.is_visible('#webClone'), '복제한 앱에도 앱 복제 버튼 유지')
        await C.click('#ta'); await C.keyboard.insert_text('**복제한 앱**에서 쓴 개인 글'); await C.wait_for_timeout(700)
        await C.click('.menu-btn:text-is("파일")'); await C.click('.menu-pop:not([hidden]) .mi:has-text("마크다운 원본으로 저장")'); await C.wait_for_timeout(300)
        memo = (await C.evaluate('window.__downloads'))[-1]
        ok(memo['data'] == '**복제한 앱**에서 쓴 개인 글' and re.fullmatch(r'\d{6}_\d{4}_메모\.md', memo['filename']), '복제 앱의 메모 저장 정상', memo['filename'])
        await C.click('#webClone'); await C.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        await C.click('#cloneDownload'); await C.wait_for_timeout(300)
        again = (await C.evaluate('window.__downloads'))[-1]
        ok(again['filename'] == 'web-notepad-clone-kit.txt' and '>앱 복제</span>' in again['data'] and '%F0%9F%93%8B' in again['data'], '복제 앱에서 변경 사항을 유지해 재복제 가능')
        ok('복제한 앱</strong>에서 쓴 개인 글' not in again['data'] and '**복제한 앱**에서 쓴 개인 글' not in again['data'], '개인 메모가 재복제 자료에 없음')
        print('   페이지 오류:', errs2 or '없음')
        await b.close()

asyncio.run(main())
