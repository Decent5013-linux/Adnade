import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://fconverter.vipb.top/ad.html"
    proxy = {
        "server": "http://127.0.0.1:3000"
    }
    
    async with async_playwright() as p:
        # Launch browser with proxy settings
        browser = await p.chromium.launch(
            headless=False,  # Keep browser visible
            proxy=proxy
        )
        
        # Create a new context (all tabs will share this context)
        context = await browser.new_context()
        
        # Open initial page to create the first tab
        page = await context.new_page()
        await page.goto(url)
        
        # Open 9 more tabs
        for i in range(9):
            new_page = await context.new_page()
            await new_page.goto(url)
            print(f"Tab {i+2} opened")
        
        print("All 10 tabs are open. Browser will remain open.")
        
        # Keep the script running so the browser stays open
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
