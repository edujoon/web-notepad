import asyncio, re
from playwright.async_api import async_playwright

def ok(c, n, d=''):
    print(('✅ ' if c else '❌ ') + n + (f'  ({d})' if d else ''))

CLEAN = open('/mnt/user-data/outputs/notepad.html', encoding='utf-8').read()
CODE_START = '===== 실행 가능한 전체 HTML 시작 ====='
CODE_END = '===== 실행 가능한 전체 HTML 끝 ====='
PROMPT_START = '===== 제작 요청 프롬프트 시작 ====='
PROMPT_END = '===== 제작 요청 프롬프트 끝 ====='

def app_html(bundle):
    return bundle.split(CODE_START, 1)[1].split(CODE_END, 1)[0].strip('\n')

def prompt_text(bundle):
    return bundle.split(PROMPT_START, 1)[1].split(PROMPT_END, 1)[0].strip('\n')

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
        for word in ['id="webClone"', 'id="cloneLayer"', 'buildCloneKit', 'https://gemini.google.com/app']:
            ok(word in CLEAN, f'배포용 파일에 {word} 포함')
        ok(CLEAN.index('id="tabs"') < CLEAN.index('id="newTab"') < CLEAN.index('id="webClone"'), '탭 목록 → 새 메모 → 앱 복제 DOM 순서')
        ok('rel="icon"' in CLEAN and '%F0%9F%93%8B' in CLEAN, '📋 SVG data URL 파비콘 포함')
        ok('localStorage.getItem(LOCAL_NOTES_KEY)' not in CLEAN[CLEAN.index('async function buildCloneKit'):CLEAN.index('function getCloneKit')], '복제 생성기가 개인 메모를 읽지 않음')
        clone_fn = CLEAN[CLEAN.index('async function buildCloneKit'):CLEAN.index('function getCloneKit')]
        ok('fetch(' not in clone_fn and '__WEB_NOTEPAD_CLONE_SOURCE__' in clone_fn, '복제 생성기가 현재 주소나 원본 주소를 다시 가져오지 않음')

        print('── 체험용 앱')
        ctx = await b.new_context(viewport={'width': 1000, 'height': 700})
        await ctx.add_init_script(path='/home/claude/menu/mock.js')
        await ctx.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        A = await ctx.new_page(); errs = []; A.on('pageerror', lambda e: errs.append(str(e)))
        await A.goto('http://localhost:8765/notepad-demo.html'); await A.wait_for_timeout(1200)
        ok(await A.is_visible('#webClone'), '앱 복제 버튼 보임')
        await A.click('#webClone'); await A.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        text = await A.inner_text('#cloneLayer')
        steps = ['복제 파일 다운로드', 'Gemini에서 새 대화를 열고 Canvas 선택', '다운로드한 파일 첨부', '아래 제작 요청을 입력하고 전송', 'Canvas 미리보기에서 메모장 사용']
        short_request = '첨부 파일의 제작 요청과 전체 소스를 읽고, 추가 질문 없이 Gemini Canvas에서 바로 사용할 수 있는 메모장 앱을 만들어 줘.'
        ok('내가 작성한 메모는 포함되지 않아요' in text and all(step in text for step in steps) and short_request in text, '앱 복제 안내 창의 개인정보 안내·5단계 순서·짧은 요청')
        ok(await A.get_attribute('#cloneGemini', 'href') == 'https://gemini.google.com/app', 'Gemini 열기 주소')
        await A.click('#cloneDownload'); await A.wait_for_timeout(300)
        d = (await A.evaluate('window.__downloads'))[-1]
        ok(d['filename'] == 'web-notepad-gemini-canvas-kit.txt', 'UTF-8 복제 파일 받기', d['filename'])
        bundle = d['data']
        ok(bundle.count(CODE_START) == 1 and bundle.count(CODE_END) == 1, '코드 경계가 각각 한 번만 포함')
        prompt = prompt_text(bundle)
        ok('Gemini Canvas에서 즉시 조작할 수 있는 웹 메모장 앱' in prompt and '결과물은 Canvas의 앱 미리보기여야 해' in prompt and '앱 이름·사용자 표시 이름·대표 색상을 묻지 말고' in prompt, 'Gemini Canvas 우선·사전 질문 없는 프롬프트 포함')
        ok('ChatGPT' not in prompt and 'Vercel' not in prompt and '로컬 실행 방법' not in prompt, '이전 ChatGPT·Vercel 배포 지시 없음')
        ok('현재 환경에서 Canvas 앱을 만들 수 없다면' in prompt and '실제로 확인하지 못한 동작은 검증했다고 말하지 말아 줘' in prompt, '제한과 미검증 동작을 정확히 알리는 지시 포함')
        html = app_html(bundle)
        ok('demo-home' not in html and '__DEMO_PERIOD_MS' not in html and 'demoNote' not in html, '복제 HTML에 체험판 초기화 코드 없음')
        ok('const EMBEDDED_USAGE = "# 웹 메모장 사용 가이드' in html and 'id="webClone"' in html, '복제 HTML에 기본 가이드와 재복제 기능 포함')
        ok(html.index('id="tabs"') < html.index('id="newTab"') < html.index('id="webClone"') and '%F0%9F%93%8B' in html, '복제 HTML에 탭 뒤 + 버튼과 📋 파비콘 포함')
        ok('fonts.googleapis.com' not in html and 'cdn.jsdelivr.net' not in html, '복제 HTML에 Google Fonts·CDN 런타임 의존성 없음')
        ok('marked v12.0.2' in html and '@license DOMPurify 3.2.6' in html, '마크다운 처리·HTML 정화 라이브러리와 고지 포함')
        ok(html.count('<script>\n/*! marked v12.0.2') == 1 and html.count('<script>\n/*! @license DOMPurify 3.2.6') == 1, '실행용 라이브러리는 각각 한 번만 인라인됨')
        ok('fetch(sourceUrl.href' not in html and 'makeMemoryStore' in html, '재복제 원본 독립성과 저장 제한용 메모리 대체 포함')
        print('   페이지 오류:', errs or '없음')

        open('/tmp/host/copy_clean.html', 'w', encoding='utf-8').write(html)
        print('── 복제한 앱')
        c2 = await b.new_context(viewport={'width': 1000, 'height': 700})
        await c2.add_init_script(path='/home/claude/menu/mock.js')
        await c2.route('**/*', lambda r: route(r) if r.request.url.startswith('https') else r.continue_())
        C = await c2.new_page(); errs2 = []; external = []
        C.on('pageerror', lambda e: errs2.append(str(e)))
        C.on('request', lambda r: external.append(r.url) if r.url.startswith('http') and 'localhost:8765' not in r.url else None)
        await C.goto('http://localhost:8765/copy_clean.html'); await C.wait_for_timeout(700)
        ok(await C.is_visible('#webClone'), '복제한 앱에도 앱 복제 버튼 유지')
        await C.click('#ta'); await C.keyboard.insert_text('**복제한 앱**에서 쓴 개인 글'); await C.wait_for_timeout(700)
        await C.click('.menu-btn:text-is("파일")'); await C.click('.menu-pop:not([hidden]) .mi:has-text("마크다운 원본으로 저장")'); await C.wait_for_timeout(300)
        memo = (await C.evaluate('window.__downloads'))[-1]
        ok(memo['data'] == '**복제한 앱**에서 쓴 개인 글' and re.fullmatch(r'\d{6}_\d{4}_메모\.md', memo['filename']), '복제 앱의 메모 저장 정상', memo['filename'])
        await C.click('#webClone'); await C.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        await C.click('#cloneDownload'); await C.wait_for_timeout(300)
        again = (await C.evaluate('window.__downloads'))[-1]
        ok(again['filename'] == 'web-notepad-gemini-canvas-kit.txt' and '>앱 복제</span>' in again['data'] and '%F0%9F%93%8B' in again['data'], '복제 앱에서 변경 사항을 유지해 재복제 가능')
        ok('Gemini Canvas에서 즉시 조작할 수 있는 웹 메모장 앱' in prompt_text(again['data']) and 'ChatGPT' not in prompt_text(again['data']) and 'cdn.jsdelivr.net' not in app_html(again['data']), '재복제 자료에도 Gemini 프롬프트와 자체 포함 소스 유지')
        ok('복제한 앱</strong>에서 쓴 개인 글' not in again['data'] and '**복제한 앱**에서 쓴 개인 글' not in again['data'], '개인 메모가 재복제 자료에 없음')
        ok(not external, '복제 앱 실행 중 외부 네트워크 요청 없음', str(external))
        print('   페이지 오류:', errs2 or '없음')
        await b.close()

asyncio.run(main())
