import asyncio
import time
from playwright.async_api import async_playwright
from pynput.mouse import Button, Controller
import os
import signal
import psutil

# ============================================
# SET YOUR OFFSET VALUES HERE (from center of page)
# ============================================
up = 0      # positive = move up from center
down = 250    # positive = move down from center
left = 0    # positive = move left from center
right = 0   # positive = move right from center
# ============================================

async def cleanup_browser(browser_pid=None):
    """Clean up browser processes"""
    try:
        # Kill any chromium processes spawned by this script
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'chromium' in cmdline.lower() and 'playwright' in cmdline.lower():
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except:
        pass

async def main():
    mouse = Controller()
    
    async with async_playwright() as p:
        # Launch browser with specific args for Linux server
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        try:
            # Navigate to URL
            print("Opening URL...")
            await page.goto('https://telead.mail.name.ng/ouo.html', wait_until='load')
            
            # Wait 10 seconds
            print("Waiting 10 seconds...")
            await asyncio.sleep(10)
            
            # Get page center coordinates
            viewport_size = page.viewport_size
            center_x = viewport_size['width'] / 2
            center_y = viewport_size['height'] / 2
            
            # Calculate target position from center with offsets
            target_x = center_x + right - left
            target_y = center_y + down - up
            
            print(f"Page center: ({center_x}, {center_y})")
            print(f"Target position on page: ({target_x}, {target_y})")
            
            # Get browser window position
            browser_js = await page.evaluate("""
                () => {
                    return {
                        x: window.screenX || 0,
                        y: window.screenY || 0
                    }
                }
            """)
            
            # Calculate screen position (adding browser UI offset)
            screen_x = browser_js['x'] + target_x
            screen_y = browser_js['y'] + target_y + 80  # Browser titlebar/toolbar offset
            
            print(f"Moving mouse to screen position: ({screen_x}, {screen_y})")
            mouse.position = (screen_x, screen_y)
            await asyncio.sleep(0.5)
            mouse.click(Button.left, 1)
            print("Clicked!")
            
            # Wait 3 seconds
            print("Waiting 3 seconds...")
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"Error occurred: {e}")
        
        finally:
            # Close browser properly
            print("Closing browser gracefully...")
            try:
                await context.close()
                await browser.close()
            except:
                pass
            
            # Force cleanup any remaining processes
            await cleanup_browser()
            print("Browser closed successfully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        # Cleanup on interrupt
        asyncio.run(cleanup_browser())
    finally:
        print("Script ended")
        # Final cleanup
        os.system('pkill -f "chromium" 2>/dev/null || true')
