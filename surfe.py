import time
import random
from playwright.sync_api import sync_playwright
from pynput.mouse import Controller as MouseController, Button
import threading
import psutil
import os
import uuid
import shutil

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

def setup_environment():
    """Configure environment for multi-instance virtual display usage."""
    os.environ['DISPLAY'] = os.environ.get('DISPLAY', ':99')
    os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
    os.environ['GALLIUM_DRIVER'] = 'llvmpipe'
    
    # Increase file descriptor limit if possible
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
    except:
        pass

def run():
    proxy_server = "http://127.0.0.1:3000"
    
    browser = None
    context = None
    page = None
    playwright = None
    
    # Generate unique user data dir per instance to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    user_data_dir = f"/tmp/chrome-user-data-{unique_id}"
    
    try:
        playwright = sync_playwright().start()
        
        # Use launch_persistent_context instead of launch for user_data_dir
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            proxy={
                "server": proxy_server
            },
            viewport={'width': 1280, 'height': 800},
            args=[
                # Disable GPU entirely - essential for Xvfb/Xvnc
                '--disable-gpu',
                '--disable-gpu-compositing',
                '--disable-gpu-sandbox',
                '--disable-software-rasterizer',
                
                # Disable D-Bus to avoid connection errors
                '--disable-dbus',
                
                # Memory and performance optimizations
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                
                # Disable extensions and unnecessary features
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-sync',
                '--disable-translate',
                '--disable-features=TranslateUI',
                '--disable-features=VizDisplayCompositor',
                '--disable-features=IsolateOrigins,site-per-process',
                
                # Disable audio
                '--mute-audio',
                '--disable-audio-output',
                
                # Reduce GPU memory usage
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-jpeg-decoding',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-decode',
                
                # WebGL disabled to prevent GPU issues
                '--disable-webgl',
                '--disable-webgl2',
                
                # Other stability improvements
                '--disable-breakpad',
                '--disable-crash-reporter',
                '--disable-logging',
                '--disable-notifications',
                '--no-first-run',
                '--no-default-browser-check',
            ]
        )
        
        # Get browser reference from context
        browser = context.browser
        
        # Create a new page (launch_persistent_context already creates one)
        page = context.pages[0] if context.pages else context.new_page()
        
        # 1. Open URL
        page.goto("https://doc.mail.name.ng/")
        
        # Random stay duration (20-40 seconds)
        stay_duration = random.randint(20, 40)
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
            link = page.locator("a[href]").first
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
        
        # Clean up user data directory
        try:
            if os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass
        
        # Extra safety: kill any remaining chromium processes
        time.sleep(1)  # Give processes time to close gracefully
        kill_chromium_processes()
        
        print("Browser closed and cleaned up successfully.")

if __name__ == "__main__":
    # Setup environment for virtual displays
    setup_environment()
    
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
            print(f"\n--- Starting new session (PID: {os.getpid()}) ---")
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
