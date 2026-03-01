import asyncio
import random
import time
import requests
from playwright.async_api import async_playwright
from pynput.mouse import Controller, Button
import pyautogui

# Initialize mouse controller
mouse = Controller()

async def get_proxy_credentials():
    """Fetch proxy username and password from the URL"""
    try:
        response = requests.get("https://ff.vpsmail.name.ng/secret.txt")
        credentials = response.text.strip().split('\n')
        if len(credentials) >= 2:
            return credentials[0].strip(), credentials[1].strip()
    except Exception as e:
        print(f"Error fetching proxy credentials: {e}")
        return None, None

async def hover_and_scroll(duration):
    """Random mouse movements and scrolling for specified duration"""
    screen_width, screen_height = pyautogui.size()
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # Random mouse movement
        x = random.randint(100, screen_width - 100)
        y = random.randint(100, screen_height - 100)
        mouse.position = (x, y)
        
        # Random scrolling
        scroll_amount = random.randint(-300, 300)
        mouse.scroll(0, scroll_amount)
        
        # Random wait between actions
        await asyncio.sleep(random.uniform(0.5, 2))

async def run_browser_cycle():
    """Run one browser cycle"""
    # Get proxy credentials
    username, password = await get_proxy_credentials()
    if not username or not password:
        print("Failed to get proxy credentials")
        return False
    
    # Proxy configuration
    proxy = {
        "server": "gateway.aluvia.io",
        "username": username,
        "password": password
    }
    
    async with async_playwright() as p:
        # Launch browser with proxy
        browser = await p.chromium.launch(
            headless=False,
            proxy=proxy
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to URL
            await page.goto("https://lltrco.com/?r=zedred", wait_until="domcontentloaded")
            print("Page loaded, looking for iframe...")
            
            # Keep looking for iframe (no timeout)
            iframe_found = False
            while not iframe_found:
                iframes = await page.locator("iframe").all()
                if iframes:
                    print(f"Found {len(iframes)} iframe(s)")
                    iframe_found = True
                else:
                    await asyncio.sleep(0.5)
            
            # Random hover and scroll for 11-15 seconds
            duration = random.randint(11, 15)
            print(f"Hovering and scrolling for {duration} seconds...")
            await hover_and_scroll(duration)
            
        except Exception as e:
            print(f"Error during browser cycle: {e}")
        
        finally:
            # Close browser
            await browser.close()
            print("Browser closed")
    
    return True

async def main():
    """Main loop - repeats indefinitely"""
    cycle_count = 0
    
    while True:
        cycle_count += 1
        print(f"\n=== Starting cycle #{cycle_count} ===")
        
        success = await run_browser_cycle()
        
        if success:
            print(f"Cycle #{cycle_count} completed successfully")
        else:
            print(f"Cycle #{cycle_count} failed")
        
        # Small delay before next cycle
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
