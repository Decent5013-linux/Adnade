import asyncio
import random
import time
import subprocess
from playwright.async_api import async_playwright
from pynput.mouse import Controller
import re

# Initialize mouse controller
mouse = Controller()

async def get_proxy_credentials():
    """Fetch username and password from secret URL using curl"""
    try:
        # Run curl command to fetch credentials
        print("Fetching proxy credentials with curl...")
        result = subprocess.run(
            ['curl', '-s', 'https://ff.vpsmail.name.ng/secret.txt'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            # Split by lines and clean up
            lines = result.stdout.strip().split('\n')
            print(f"Raw output: {lines}")
            
            if len(lines) >= 2:
                username = lines[0].strip()
                password = lines[1].strip()
                print(f"Username: {username}")
                print(f"Password: {'*' * len(password)}")
                return username, password
            else:
                print(f"Unexpected output format: {lines}")
        else:
            print(f"Curl failed with return code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("Curl command timed out")
    except Exception as e:
        print(f"Error fetching credentials with curl: {e}")
    
    return None, None

async def random_mouse_activity(page, duration_seconds):
    """Perform random mouse movements and scrolling for specified duration"""
    start_time = time.time()
    
    # Get viewport size
    viewport = page.viewport_size
    if not viewport:
        viewport = {'width': 1920, 'height': 1080}
    
    end_time = start_time + duration_seconds
    while time.time() < end_time:
        # Random mouse movement
        x = random.randint(100, viewport['width'] - 100)
        y = random.randint(100, viewport['height'] - 100)
        mouse.position = (x, y)
        
        # Random scroll
        scroll_y = random.randint(-300, 300)
        await page.evaluate(f"window.scrollBy(0, {scroll_y})")
        
        # Random pause between actions
        await asyncio.sleep(random.uniform(0.5, 2.0))

async def wait_for_iframe(page):
    """Wait for any iframe to appear on the page"""
    iframe_count = 0
    while True:
        iframes = await page.locator('iframe').all()
        current_count = len(iframes)
        
        if current_count > 0:
            print(f"Found {current_count} iframe(s)")
            return True
        
        if iframe_count != current_count:
            print(f"No iframes yet... checking again in 0.5s")
            iframe_count = current_count
            
        await asyncio.sleep(0.5)

async def run_browser_cycle():
    """Execute one complete browser cycle"""
    username, password = await get_proxy_credentials()
    if not username or not password:
        print("Failed to get proxy credentials")
        return False

    # Proxy configuration with port 8080
    proxy = {
        "server": "gateway.aluvia.io:8080",  # Added port 8080
        "username": username,
        "password": password
    }
    
    print(f"Using proxy: gateway.aluvia.io:8080")

    async with async_playwright() as p:
        # Launch browser with proxy
        print("Launching browser with proxy...")
        browser = await p.chromium.launch(
            headless=False,
            proxy=proxy
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            extra_http_headers={
                'Referer': 'https://zerads.com'  # Added referrer header
            }
        )
        page = await context.new_page()
        
        try:
            # Navigate to URL
            print("Navigating to https://lltrco.com/?r=zedred...")
            print("With referrer: https://zerads.com")
            
            # You can also add referrer to the navigation itself as an alternative
            await page.goto('https://lltrco.com/?r=zedred', 
                          wait_until='domcontentloaded',
                          referer='https://zerads.com')  # Added referrer here too for redundancy
            
            print("Page loaded, waiting for iframes...")
            
            # Wait for iframe
            await wait_for_iframe(page)
            
            # Random mouse activity for 11-15 seconds
            duration = random.randint(11, 15)
            print(f"Performing mouse activity for {duration} seconds...")
            await random_mouse_activity(page, duration)
            
            print("Cycle complete, closing browser...")
            
        except Exception as e:
            print(f"Error during cycle: {e}")
        
        await browser.close()
        return True

async def main():
    """Main loop - repeats browser cycles"""
    cycle_count = 0
    
    # Test credentials first
    print("Testing credential fetch...")
    test_user, test_pass = await get_proxy_credentials()
    if test_user and test_pass:
        print("✓ Credential fetch successful")
    else:
        print("✗ Credential fetch failed")
        return
    
    while True:
        cycle_count += 1
        print(f"\n{'='*50}")
        print(f"Starting Cycle #{cycle_count}")
        print(f"{'='*50}")
        
        success = await run_browser_cycle()
        
        if not success:
            print("Cycle failed, waiting 10 seconds before retry...")
            await asyncio.sleep(10)
        else:
            # Small delay between successful cycles
            print("Waiting 3 seconds before next cycle...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript stopped by user")
