import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        for w in [1000, 780, 600, 561, 540, 360]:
            ctx = await b.new_context(viewport={'width': w, 'height': 150}); await ctx.add_init_script(path='/home/claude/menu/mock.js')
            await ctx.route('**/*', lambda r: r.abort() if r.request.url.startswith('https') else r.continue_())
            A = await ctx.new_page(); await A.goto('http://localhost:8765/notepad.html'); await A.wait_for_timeout(400)
            info = await A.evaluate("""() => { const seg = document.getElementById('seg'), bar = document.querySelector('.bar');
              const labels = [...seg.querySelectorAll('[role=radio]')].map(b => [...b.children].find(c => getComputedStyle(c).display !== 'none').textContent);
              const over = [...document.querySelectorAll('.bar *')].some(el => el.getBoundingClientRect().right > innerWidth + 0.5);
              return { labels, overflow: over || bar.scrollWidth > bar.clientWidth, rows: Math.round(bar.getBoundingClientRect().height) }; }""")
            print(f'{w:>5}px', ' | '.join(info['labels']), '| 넘침' if info['overflow'] else '| 넘침 없음', f'| 막대 높이 {info["rows"]}px')
            await A.screenshot(path=f'/home/claude/menu/w{w}.png'); await ctx.close()
        await b.close()
asyncio.run(main())
