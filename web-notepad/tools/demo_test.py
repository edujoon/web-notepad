import asyncio

from playwright.async_api import async_playwright


def ok(condition, name, detail=""):
    print(("✅ " if condition else "❌ ") + name + (f"  ({detail})" if detail else ""))
    if not condition:
        raise AssertionError(name)


CODE_START = "===== 실행 가능한 전체 HTML 시작 ====="
CODE_END = "===== 실행 가능한 전체 HTML 끝 ====="


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
        context = await browser.new_context(viewport={"width": 1000, "height": 700})
        await context.add_init_script(script="window.__DEMO_PERIOD_MS = 6000;")
        await context.add_init_script(path="/home/claude/menu/mock.js")
        await context.route("**/*", lambda r: route(r) if r.request.url.startswith("https") else r.continue_())
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto("http://localhost:8765/notepad-demo.html")
        await page.wait_for_timeout(1800)

        value = lambda p: p.eval_on_selector("#ta", "e => e.value")
        tabs = lambda p: p.eval_on_selector_all("#tabs .tab-name", "els => els.map(e => e.textContent)")
        first = await value(page)
        ok(len(await tabs(page)) == 1 and first.startswith("웹 메모장 사용 가이드"), "체험판 초기 USAGE 안내 메모")
        ok(await page.is_visible("#demoNote"), "체험판 초기화 안내 표시")

        second = await context.new_page()
        await second.goto("http://localhost:8765/notepad-demo.html")
        await second.wait_for_timeout(600)
        await page.click("#ta")
        await page.keyboard.press("Control+End")
        await page.keyboard.insert_text("\n\n체험자가 쓴 글")
        await page.keyboard.press("Alt+n")
        await page.wait_for_timeout(200)
        await page.keyboard.insert_text("첫 번째 창")
        await second.keyboard.press("Alt+n")
        await second.wait_for_timeout(200)
        await second.click("#ta")
        await second.keyboard.insert_text("다른 창에서 만든 메모")
        await page.wait_for_timeout(8000)
        ok(len(await tabs(page)) == len(await tabs(second)) == 1, "설정 주기 뒤 두 창 모두 안내 메모 하나만 유지")
        ok((await value(page)).startswith("웹 메모장 사용 가이드") and "체험자가 쓴 글" not in await value(page), "체험판 내용 초기화")

        await page.click("#webClone")
        await page.wait_for_function("!document.querySelector('#cloneDownload').disabled")
        await page.click("#cloneDownload")
        await page.wait_for_timeout(300)
        bundle = (await page.evaluate("window.__downloads"))[-1]["data"]
        html = bundle.split(CODE_START, 1)[1].split(CODE_END, 1)[0].strip("\n")
        ok("demo-home" not in html and "__DEMO_PERIOD_MS" not in html and "demoNote" not in html, "복제 HTML에서 체험판 코드 제외")
        ok('const EMBEDDED_USAGE = "# 웹 메모장 사용 가이드' in html, "복제 HTML에 기본 가이드 포함")
        ok('id="webClone"' not in html and "buildCloneKit" not in html and "앱 복제" not in html, "복제 HTML에서 앱 복제와 재복제 코드 제외")
        ok(html.index('id="tabs"') < html.index('id="newTab"') and "%F0%9F%93%8B" in html, "복제 HTML에 마지막 탭 뒤 +와 📋 파비콘 유지")
        ok("fonts.googleapis.com" not in html and "cdn.jsdelivr.net" not in html and "marked v12.0.2" in html and "@license DOMPurify 3.2.6" in html, "복제 HTML 자체 포함 라이브러리 유지")
        print("   페이지 오류:", errors or "없음")
        await browser.close()


asyncio.run(main())
