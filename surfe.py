import time
import random
from playwright.sync_api import sync_playwright
from pynput.mouse import Controller as MouseController, Button
import threading
import psutil
import os

def kill_chromium_processes():
    """Kills any remaining chromium/chrome processes to prevent memory pile-up."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and any(browser in proc.info['name'].lower() for browser in ['chromium', 'chrome', 'playwright']):
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except:
        pass  # If psutil fails, just continue

def human_scroll(page):
    """Performs a realistic scroll with random distances."""
    # Generate random page height between 2000-5000 pixels
    page_height = random.randint(2000, 5000)
    page.evaluate(f"document.body.style.height = '{page_height}px';")
    
    # Scroll to random position (not always to bottom)
    target_bottom = random.randint(page_height // 2, page_height)
    current_pos = 0
    
    while current_pos < target_bottom:
        step = random.randint(50, 400)
        current_pos += step
        page.mouse.wheel(0, step)
        time.sleep(random.uniform(0.3, 1.5))
    
    time.sleep(random.uniform(1, 3))
    
    # Sometimes scroll back up to random position
    if random.random() < 0.7:
        target_top = random.randint(0, current_pos // 2)
        while current_pos > target_top:
            step = random.randint(50, 400)
            current_pos -= step
            page.mouse.wheel(0, -step)
            time.sleep(random.uniform(0.3, 1.5))

def human_mouse_movement():
    """Uses pynput to move the actual mouse cursor around the screen."""
    mouse = MouseController()
    
    for _ in range(random.randint(5, 12)):
        x = random.randint(100, 1180)
        y = random.randint(100, 700)
        
        current_pos = mouse.position
        steps = 30
        
        for i in range(steps):
            progress = (i + 1) / steps
            target_x = current_pos[0] + (x - current_pos[0]) * progress + random.randint(-3, 3)
            target_y = current_pos[1] + (y - current_pos[1]) * progress + random.randint(-3, 3)
            mouse.position = (int(target_x), int(target_y))
            time.sleep(random.uniform(0.01, 0.05))
        
        time.sleep(random.uniform(0.5, 2.0))

def human_move_and_hover(page):
    """Moves mouse randomly around the page using both pynput and Playwright."""
    mouse_thread = threading.Thread(target=human_mouse_movement)
    mouse_thread.start()
    
    for _ in range(random.randint(2, 5)):
        x, y = random.randint(100, 1180), random.randint(100, 700)
        page.mouse.move(x, y, steps=random.randint(5, 15))
        time.sleep(random.uniform(0.5, 1.5))
        
        if random.random() < 0.4:
            links = page.locator("a, button, input, ins").all()
            if len(links) > 0:
                random_link = random.choice(links)
                try:
                    random_link.hover()
                    time.sleep(random.uniform(0.5, 1.0))
                except:
                    pass
    
    mouse_thread.join()

def run():
    proxy_server = "http://127.0.0.1:3000"
    
    # List of URLs to choose from
    urls = [
        "https://fconverter.vipb.top/pdf-to-docx.php",
        "https://fconverter.vipb.top/docx-to-pdf.php",
        "https://fconverter.vipb.top/jpeg-to-jpg.php",
        "https://fconverter.vipb.top/doc-to-pdf.php",
        "https://fconverter.vipb.top/mp4-to-avi.php",
        "https://fconverter.vipb.top/png-to-webp.php",
        "https://fconverter.vipb.top/webp-to-png.php"
    ]
    
    # List of possible referrers
    referrers = [
        "http://m.facebook.com",
        "https://google.com",
        "https://t.me",
        "https://www.bing.com",
        "https://www.reddit.com",
        "https://twitter.com",
        "https://www.instagram.com",
        "https://www.youtube.com",
        "https://www.linkedin.com",
        "https://www.pinterest.com",
        "https://duckduckgo.com",
        "https://www.yahoo.com",
        "https://web.telegram.org",
        "https://discord.com",
        "https://www.quora.com"
    ]
    
    browser = None
    context = None
    page = None
    playwright = None
    
    try:
        playwright = sync_playwright().start()
        
        # Select random URL and referrer
        target_url = random.choice(urls)
        target_referrer = random.choice(referrers)
        
        # Launch browser with local proxy
        browser = playwright.chromium.launch(
            headless=False,
            proxy={
                "server": proxy_server
            }
        )
        
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # Set referrer before navigating
        page.set_extra_http_headers({"Referer": target_referrer})
        
        # 1. Open URL
        page.goto(target_url, referer=target_referrer)
        
        # Random stay duration (20-40 seconds)
        stay_duration = random.randint(55, 75)
        start_time = time.time()
        
        # 2. Human actions during the stay (NO CLICKS HERE)
        human_move_and_hover(page)
        human_scroll(page)
        
        if random.random() < 0.5:
            human_mouse_movement()
        
        # WAIT until stay duration is complete
        elapsed = time.time() - start_time
        if elapsed < stay_duration:
            time.sleep(stay_duration - elapsed)
        
        # 3. Random interaction logic (ONLY AFTER stay duration is complete)
        roll = random.random() * 100
        
        if roll <= 90:
            link = page.locator("a[hreef]").first
            if link.count() > 0:
                link.click()
                time.sleep(random.uniform(2, 4))
                page.go_back()
                time.sleep(random.uniform(1, 2))
                
                if random.random() <= 0.01:
                    ins_element = page.locator("ins").first
                    if ins_element.count() > 0:
                        ins_element.click()
                        time.sleep(random.uniform(1, 2))
                        
        elif roll <= 95:
            ins_element = page.locator("ins").first
            if ins_element.count() > 0:
                ins_element.hover()
                time.sleep(random.uniform(0.5, 1.0))
                ins_element.click()
                time.sleep(random.uniform(2, 4))
        
    except Exception as e:
        print(f"Session error: {e}")
    finally:
        # PROPER CLEANUP - Close in reverse order
        try:
            if page:
                page.close()
        except:
            pass
            
        try:
            if context:
                context.close()
        except:
            pass
            
        try:
            if browser:
                browser.close()
        except:
            pass
            
        try:
            if playwright:
                playwright.stop()
        except:
            pass
        
        # Extra safety: kill any remaining chromium processes
        time.sleep(1)  # Give processes time to close gracefully
        kill_chromium_processes()
        
        print("Browser closed and cleaned up successfully.")

if __name__ == "__main__":
    # Install psutil if not already installed
    try:
        import psutil
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'psutil'])
        import psutil
    
    # Run continuously in a loop
    while True:
        try:
            print(f"\n--- Starting new session ---")
            run()
            wait_between_sessions = random.randint(3, 8)
            print(f"Waiting {wait_between_sessions} seconds before next session...")
            time.sleep(wait_between_sessions)
        except KeyboardInterrupt:
            print("\nStopping...")
            kill_chromium_processes()
            break
        except Exception as e:
            print(f"Critical error: {e}")
            print("Cleaning up and restarting in 5 seconds...")
            kill_chromium_processes()
            time.sleep(5)
