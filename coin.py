import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

URL = "https://fconverter.vipb.top/coin.html"
PROXY = "http://127.0.0.1:3000"

TAB_COUNT = 12
REOPEN_DELAY = 10
ALLOWED_DOMAIN = "fconverter.vipb.top"


def is_allowed(url: str) -> bool:
    try:
        return ALLOWED_DOMAIN in urlparse(url).netloc
    except:
        return False


async def monitor_page(page):
    """Closes any page that navigates outside allowed domain."""
    try:
        while True:
            await asyncio.sleep(0.5)
            current_url = page.url

            if current_url and not is_allowed(current_url):
                print(f"[BLOCK] Closing invalid tab: {current_url}")
                await page.close()
                break
    except:
        pass


async def tab_worker(browser, tab_id):
    context = await browser.new_context()

    async def handle_new_page(page):
        print(f"[Tab {tab_id}] New page detected -> {page.url}")
        asyncio.create_task(monitor_page(page))

    context.on("page", handle_new_page)

    while True:
        page = await context.new_page()

        try:
            print(f"[Tab {tab_id}] Opening main page...")
            await page.goto(URL, wait_until="load", timeout=60000)

            asyncio.create_task(monitor_page(page))

            await asyncio.sleep(REOPEN_DELAY)

        except Exception as e:
            print(f"[Tab {tab_id}] Error: {e}")

        finally:
            try:
                await page.close()
            except:
                pass


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            proxy={"server": PROXY},
        )

        tasks = [
            asyncio.create_task(tab_worker(browser, i + 1))
            for i in range(TAB_COUNT)
        ]

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
