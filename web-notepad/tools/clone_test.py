import asyncio
import re

from playwright.async_api import async_playwright


def ok(condition, name, detail=""):
    print(("✅ " if condition else "❌ ") + name + (f"  ({detail})" if detail else ""))
    if not condition:
        raise AssertionError(name)


CLEAN = open("/mnt/user-data/outputs/notepad.html", encoding="utf-8").read()
CODE_START = "===== 실행 가능한 전체 HTML 시작 ====="
CODE_END = "===== 실행 가능한 전체 HTML 끝 ====="
PROMPT_START = "===== 제작 요청 프롬프트 시작 ====="
PROMPT_END = "===== 제작 요청 프롬프트 끝 ====="


def app_html(bundle):
    return bundle.split(CODE_START, 1)[1].split(CODE_END, 1)[0].strip("\n")


def prompt_text(bundle):
    return bundle.split(PROMPT_START, 1)[1].split(PROMPT_END, 1)[0].strip("\n")


async def route(request_route):
    url = request_route.request.url
    if "marked" in url:
        await request_route.fulfill(path="/tmp/package/marked.min.js", content_type="application/javascript")
    elif "dompurify" in url:
        await request_route.fulfill(path="/tmp/dp/package/dist/purify.min.js", content_type="application/javascript")
    else:
        await request_route.abort()


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

        print("── 원본 배포 파일 자체 점검")
        for token in ('id="webClone"', 'id="cloneLayer"', "buildCloneKit", "https://gemini.google.com/app"):
            ok(token in CLEAN, f"원본에 {token} 포함")
        ok(CLEAN.index('id="tabs"') < CLEAN.index('id="newTab"') < CLEAN.index('id="webClone"'), "탭 목록 → 새 메모 → 앱 복제 DOM 순서")
        ok('rel="icon"' in CLEAN and "%F0%9F%93%8B" in CLEAN, "📋 SVG data URL 파비콘 포함")
        clone_runtime = CLEAN[CLEAN.index("async function buildCloneKit"):CLEAN.index("function getCloneKit")]
        ok("localStorage" not in clone_runtime and "fetch(" not in clone_runtime, "복제 생성기가 개인 저장소나 원본 주소를 읽지 않음")
        ok("window.__WEB_NOTEPAD_CLONE_SOURCE__" in clone_runtime, "빌드된 정적 복제 소스만 사용")

        print("── 원본 앱의 복제 흐름")
        context = await browser.new_context(viewport={"width": 1000, "height": 700})
        await context.add_init_script(path="/home/claude/menu/mock.js")
        await context.route("**/*", lambda r: route(r) if r.request.url.startswith("https") else r.continue_())
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto("http://localhost:8765/notepad-demo.html")
        await page.wait_for_timeout(1200)
        ok(await page.is_visible("#webClone"), "원본의 앱 복제 버튼 표시")
        await page.click("#newTab")
        await page.click("#ta")
        await page.keyboard.insert_text("현재 편집 중인 개인 메모")
        await page.wait_for_timeout(700)
        await page.click("#webClone")
        await page.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        dialog = await page.inner_text("#cloneLayer")
        steps = [
            "복제 파일 다운로드",
            "Gemini에서 새 대화를 열고 Canvas 선택",
            "다운로드한 파일 첨부",
            "아래 제작 요청을 입력하고 전송",
            "Canvas 미리보기에서 메모장 사용",
        ]
        ok("내가 작성한 메모는 포함되지 않아요" in dialog and all(step in dialog for step in steps), "개인정보 안내와 5단계 순서")
        ok("복제본에는 앱 복제 기능이 포함되지 않아요" in dialog, "원본 안내 창에서 복제본 범위 명시")
        ok(await page.get_attribute("#cloneGemini", "href") == "https://gemini.google.com/app", "Gemini 열기 주소")

        await page.click("#cloneDownload")
        await page.wait_for_timeout(300)
        download = (await page.evaluate("window.__downloads"))[-1]
        ok(download["filename"] == "web-notepad-gemini-canvas-kit.txt", "UTF-8 복제 파일 다운로드", download["filename"])
        bundle = download["data"]
        ok(bundle.count(CODE_START) == bundle.count(CODE_END) == 1, "HTML 경계가 각각 한 번만 포함")
        ok(bundle.count(PROMPT_START) == bundle.count(PROMPT_END) == 1, "프롬프트 경계가 각각 한 번만 포함")

        prompt = prompt_text(bundle)
        required_prompt = [
            "Gemini Canvas에서 바로 사용할 수 있는 메모장 앱",
            "메모 작성·수정·삭제·탭 전환·마크다운 미리보기·전체 복사·메모 파일 저장·사용 가이드",
            "이 복제본에는 앱 복제 버튼이나 재복제 기능을 추가하지 말아 줘",
            "외부 접속 의존성은 추가하지 말아 줘",
        ]
        ok(all(text in prompt for text in required_prompt), "간소화한 Gemini Canvas 프롬프트 포함")
        ok("ChatGPT" not in prompt and "Vercel" not in prompt and "앱 이름" not in prompt, "과거 서비스·배포·사전 질문 지시 없음")

        html = app_html(bundle)
        forbidden_clone = [
            'id="webClone"', 'id="cloneLayer"', "cloneGemini", "cloneCopy", "cloneDownload",
            "buildCloneKit", "getCloneKit", "openClone", "copyCloneKit", "downloadCloneKit",
            "CLONE_PROMPT", "__WEB_NOTEPAD_CLONE_SOURCE__",
            "https://gemini.google.com/app", "앱 복제",
        ]
        ok(not any(token in html for token in forbidden_clone), "복제 HTML에서 복제 UI·이벤트·생성기·내장 템플릿 제거")
        ok('id="newTab"' in html and 'id="copyAll"' in html and "%F0%9F%93%8B" in html, "새 메모·전체 복사·📋 파비콘 유지")
        ok("나만의 앱 만들기" not in html and "Gemini 열기" not in html, "복제본 사용 가이드에서 복제 안내 제거")
        ok("fonts.googleapis.com" not in html and "cdn.jsdelivr.net" not in html, "복제 HTML에 외부 실행 의존성 없음")
        ok("marked v12.0.2" in html and "@license DOMPurify 3.2.6" in html, "마크다운·HTML 정화 라이브러리와 고지 유지")
        ok(html.count("<script>\n/*! marked v12.0.2") == 1 and html.count("<script>\n/*! @license DOMPurify 3.2.6") == 1, "내장 라이브러리는 각각 한 번만 포함")
        ok("Copyright (c) 2026 JOON" in html and "Permission is hereby granted" in html, "프로젝트 저작권과 MIT 본문 유지")
        private_tokens = ["eduedujoon@gmail.com", "2026-09-22", "2026. 9. 22", "SIG_MAIL", "aboutLayer", "showAbout"]
        ok(not any(token in html for token in private_tokens), "이메일·작성일·별도 작성자 소개 제거")
        ok("현재 편집 중인 개인 메모" not in bundle, "현재 사용자 메모가 복제 자료에 없음")
        ok(html.startswith("<!doctype html>") and html.endswith("</html>"), "추출 HTML에 불필요한 바깥 이스케이프 없음")
        ok("\\u003c!doctype html>" not in html and "\\u003c/html>" not in html and "https:\\/\\/github.com" not in html, "실제 전달 HTML에 불필요한 바깥 태그·URL 이스케이프 없음")
        print("   원본 페이지 오류:", errors or "없음")

        open("/tmp/host/copy_clean.html", "w", encoding="utf-8").write(html)
        print("── 복제본 핵심 기능")
        clone_context = await browser.new_context(viewport={"width": 1000, "height": 700})
        await clone_context.add_init_script(path="/home/claude/menu/mock.js")
        await clone_context.route("**/*", lambda r: route(r) if r.request.url.startswith("https") else r.continue_())
        clone = await clone_context.new_page()
        clone_errors = []
        external = []
        clone.on("pageerror", lambda error: clone_errors.append(str(error)))
        clone.on("request", lambda request: external.append(request.url) if request.url.startswith("http") and "localhost:8765" not in request.url else None)
        await clone.goto("http://localhost:8765/copy_clean.html")
        await clone.wait_for_timeout(700)
        ok(await clone.locator("#webClone").count() == 0 and await clone.locator("#cloneLayer").count() == 0, "복제본에 앱 복제 UI 없음")
        ok((await clone.eval_on_selector("#ta", "e => e.value")).startswith("웹 메모장 사용 가이드"), "복제본의 전용 사용 가이드 표시")
        await clone.click("#newTab")
        await clone.click("#ta")
        await clone.keyboard.insert_text("# 복제본 메모\n\n**개인 글**")
        await clone.wait_for_timeout(700)
        ok(await clone.locator("#tabs .tab").count() == 2, "복제본 새 메모와 탭 전환 유지")
        await clone.click('[data-mode="rendered"]')
        await clone.wait_for_timeout(200)
        ok("복제본 메모" in await clone.inner_text("#md"), "복제본 마크다운 미리보기 유지")
        await clone.click('[data-mode="raw"]')
        await clone.evaluate("""() => Object.defineProperty(navigator, 'clipboard', {
          configurable: true,
          value: { writeText: async text => { window.__copiedNote = text; } }
        })""")
        await clone.click("#copyAll")
        await clone.wait_for_timeout(100)
        ok(await clone.evaluate("window.__copiedNote") == "# 복제본 메모\n\n**개인 글**", "복제본 메모 전체 복사 유지")
        await clone.click('.menu-btn:text-is("파일")')
        await clone.click('.menu-pop:not([hidden]) .mi:has-text("마크다운 원본으로 저장")')
        await clone.wait_for_timeout(300)
        memo = (await clone.evaluate("window.__downloads"))[-1]
        ok(memo["data"] == "# 복제본 메모\n\n**개인 글**" and re.fullmatch(r"\d{6}_\d{4}_메모\.md", memo["filename"]), "복제본 메모 파일 저장 유지", memo["filename"])
        ok(not external, "복제본 실행 중 외부 네트워크 요청 없음", str(external))
        print("   복제본 페이지 오류:", clone_errors or "없음")
        await browser.close()


asyncio.run(main())
