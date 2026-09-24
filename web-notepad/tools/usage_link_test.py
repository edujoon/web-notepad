import asyncio

from playwright.async_api import async_playwright


def ok(condition, name, detail=""):
    print(("✅ " if condition else "❌ ") + name + (f"  ({detail})" if detail else ""))
    if not condition:
        raise AssertionError(name)


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
        context = await browser.new_context(viewport={"width": 900, "height": 760})
        await context.add_init_script(path="/home/claude/menu/mock.js")
        await context.route("**/*", lambda r: route(r) if r.request.url.startswith("https") else r.continue_())
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto("http://localhost:8765/notepad-demo.html")
        await page.wait_for_timeout(1300)

        await page.click('[data-mode="rendered"]')
        await page.wait_for_timeout(500)
        link = await page.evaluate("""() => {
          const el = [...document.querySelectorAll('#md a')].find(a => a.href.includes('github.com/edujoon/web-notepad'));
          return el ? { text: el.textContent, href: el.href, target: el.target } : null;
        }""")
        ok(link and link["text"] == "edujoon/web-notepad" and link["target"] == "_blank", "USAGE 안내문의 프로젝트 링크", link["href"] if link else "없음")

        await page.click("#webClone")
        await page.wait_for_function("!document.querySelector('#cloneCopy').disabled")
        dialog = await page.inner_text("#cloneLayer")
        href = await page.get_attribute("#cloneGemini", "href")
        ok("이 메모장을 Gemini Canvas에서 만들어 보세요" in dialog and "Canvas 미리보기에서 메모장 사용" in dialog, "앱 복제 안내 창에 Gemini Canvas 목적과 순서 포함")
        ok("복제본에는 앱 복제 기능이 포함되지 않아요" in dialog, "안내 창에 원본·복제본 기능 구분 포함")
        ok(href == "https://gemini.google.com/app", "Gemini 열기 주소", href)
        await page.click("#cloneClose")

        await page.click('[data-mode="raw"]')
        await page.wait_for_timeout(200)
        raw = await page.eval_on_selector("#ta", "e => e.value")
        line = next(text for text in raw.split("\n") if "프로젝트 저장소:" in text)
        ok("https://github.com/edujoon/web-notepad" in line, "마크다운 원본의 프로젝트 링크", line[:72] + "…")
        await page.click('[data-mode="plain"]')
        await page.wait_for_timeout(200)
        plain = await page.eval_on_selector("#ta", "e => e.value")
        ok("claude.ai" not in plain, "서식 제거 보기에서 불필요한 주소 없음")
        print("   페이지 오류:", errors or "없음")
        await browser.close()


asyncio.run(main())
