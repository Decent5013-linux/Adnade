import asyncio
import random
import time
import requests
from playwright.async_api import async_playwright
from pynput.mouse import Controller
from pynput.keyboard import Controller as KeyboardController, Key

# Only need mouse for scrolling now
mouse = Controller()
keyboard = KeyboardController()

class SimpleBotSimulator:
    def __init__(self, page):
        self.page = page
        self.has_clicked = False
        
    async def get_proxy_credentials(self):
        """Fetch proxy credentials from secret.txt"""
        try:
            response = requests.get('https://bot.vpsmail.name.ng/secret.txt', timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) >= 2:
                    return lines[0].strip(), lines[1].strip()
        except Exception as e:
            print(f"Error fetching proxy credentials: {e}")
        return None, None

    async def setup_browser(self, playwright):
        """Setup browser with proxy"""
        username, password = await self.get_proxy_credentials()
        
        proxy_config = {"server": "gateway.aluvia.io:8080"}
        if username and password:
            proxy_config["username"] = username
            proxy_config["password"] = password
            print(f"Using proxy with username: {username}")
        else:
            print("Using proxy without authentication")
            
        browser = await playwright.chromium.launch(
            headless=False,
            proxy=proxy_config,
            args=['--disable-blink-features=AutomationControlled']
        )
        return browser

    async def create_scroll_space(self):
        """Make page scrollable if it isn't already"""
        await self.page.evaluate("""
            if (document.body.scrollHeight < window.innerHeight * 1.5) {
                var spacer = document.createElement('div');
                spacer.style.height = '2000px';
                spacer.style.width = '1px';
                spacer.style.opacity = '0';
                document.body.appendChild(spacer);
            }
        """)

    async def human_scroll(self):
        """OS-level scrolling using pynput - REAL scroll events (isTrusted=true)"""
        method = random.choice(['wheel', 'pagedown'])
        
        if method == 'wheel':
            chunks = random.randint(3, 6)
            for _ in range(chunks):
                clicks = random.randint(2, 4)
                for _ in range(clicks):
                    mouse.scroll(0, -1)  # REAL scroll event with isTrusted=true
                    await asyncio.sleep(random.uniform(0.05, 0.1))
                await asyncio.sleep(random.uniform(0.2, 0.4))
                
            if random.random() < 0.3:
                await asyncio.sleep(0.3)
                for _ in range(random.randint(1, 3)):
                    mouse.scroll(0, 1)
                    await asyncio.sleep(0.05)
        else:
            keyboard.press(Key.page_down)
            keyboard.release(Key.page_down)
            await asyncio.sleep(random.uniform(0.2, 0.4))
            keyboard.press(Key.page_down)
            keyboard.release(Key.page_down)

    async def find_clickable_elements(self):
        """Find anything clickable on the page"""
        elements = await self.page.evaluate("""
            () => {
                const clickables = [];
                
                // Surfe ad container
                const surfeAd = document.querySelector('.surfe-be');
                if (surfeAd) {
                    const rect = surfeAd.getBoundingClientRect();
                    if (rect.width > 10 && rect.height > 10) {
                        clickables.push({
                            type: 'surfe-ad',
                            selector: '.surfe-be'
                        });
                    }
                }
                
                // Iframes
                document.querySelectorAll('iframe').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 50) {
                        clickables.push({
                            type: 'iframe',
                            selector: 'iframe'
                        });
                    }
                });
                
                // Links and buttons
                document.querySelectorAll('a, button, [onclick]').forEach(el => {
                    if (el.offsetParent !== null) {
                        clickables.push({
                            type: el.tagName.toLowerCase(),
                            selector: el.tagName.toLowerCase()
                        });
                    }
                });
                
                return clickables;
            }
        """)
        return elements

    async def run_session(self):
        """Main session loop"""
        print("🌐 Loading page...")
        await self.page.goto('https://bot.vpsmail.name.ng/ad2.html', wait_until='domcontentloaded')
        
        # Make sure page is scrollable
        await self.create_scroll_space()
        
        # Wait for ad to load
        await asyncio.sleep(2)
        
        # Session duration between 20-30 seconds
        session_duration = random.uniform(20, 30)
        session_end = time.time() + session_duration
        
        # Can click after 15-20 seconds
        min_click_time = time.time() + random.uniform(15, 20)
        
        last_scroll = time.time()
        
        print(f"⏱️  Session: {session_duration:.1f}s | Click after: {(min_click_time - time.time()):.1f}s | 39% chance\n")
        
        while time.time() < session_end:
            now = time.time()
            
            # Try to click if eligible (after min time, 39% chance)
            if now >= min_click_time and not self.has_clicked:
                clickables = await self.find_clickable_elements()
                
                if clickables and random.random() < 0.39:
                    target = random.choice(clickables)
                    
                    # Use Playwright click - simpler and works great!
                    # It automatically scrolls to element and clicks
                    await self.page.click(target['selector'])
                    print(f"✅ CLICKED: {target['type']}")
                    self.has_clicked = True
                    await asyncio.sleep(random.uniform(1, 2))
            
            # Scroll every 3-7 seconds using REAL OS scroll (isTrusted=true)
            if now - last_scroll > random.uniform(3, 7):
                await self.human_scroll()
                last_scroll = now
            
            await asyncio.sleep(0.5)
        
        print(f"✅ Session ended - {'clicked' if self.has_clicked else 'no click'}")

async def main():
    async with async_playwright() as p:
        session_count = 0
        
        while True:
            session_count += 1
            print(f"\n{'='*50}")
            print(f"🔄 SESSION #{session_count}")
            print(f"{'='*50}")
            
            try:
                simulator = SimpleBotSimulator(None)
                
                # Setup browser with proxy
                browser = await simulator.setup_browser(p)
                
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720}
                )
                
                page = await context.new_page()
                simulator.page = page
                
                # Run the session
                await simulator.run_session()
                
                # Browser closes - complete fresh session next time
                await browser.close()
                print("✅ Browser closed")
                
                # Wait 1-3 seconds for fresh start
                delay = random.uniform(1, 3)
                print(f"⏱️  Next session in {delay:.1f}s")
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    print("🚀 Bot Simulator Starting...")
    print("🖱️  Scrolls: REAL OS events (isTrusted=true)")
    print("👆 Clicks: Playwright (isTrusted NOT checked by tracker)")
    print("🎯 39% click chance AFTER 15-20 seconds")
    print("🔄 Fresh browser each session\n")
    asyncio.run(main())
