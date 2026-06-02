import time
import random
from playwright.sync_api import sync_playwright
from pynput.mouse import Controller as MouseController, Button
import threading
import psutil
import os

# CONFIGURATION - Distance in millimeters to move cursor upwards before clicking
mm = 6  # Change this value to adjust the upward offset distance

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

def scroll_to_top(page):
    """Scrolls the page smoothly to the top."""
    try:
        # Get current scroll position
        current_scroll = page.evaluate("window.scrollY")
        
        if current_scroll > 0:
            # Smooth scroll to top using JavaScript
            page.evaluate("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            
            # Wait for scroll to complete
            time.sleep(1)
            
            # Verify we're at top with a small gradual scroll
            current_scroll = page.evaluate("window.scrollY")
            while current_scroll > 0:
                step = min(current_scroll, random.randint(100, 300))
                page.mouse.wheel(0, -step)
                time.sleep(random.uniform(0.1, 0.3))
                current_scroll = page.evaluate("window.scrollY")
            
            print("Scrolled to top of page")
            
    except Exception as e:
        print(f"Error scrolling to top: {e}")

def click_above_button_with_real_mouse(page, mm_distance):
    """Finds the reward button and clicks above it with the real mouse (pynput)."""
    try:
        # Find the reward button
        reward_button = page.locator("button.reward-btn#rewardBtn")
        
        if reward_button.count() > 0:
            # Scroll the button into view first
            reward_button.scroll_into_view_if_needed()
            time.sleep(0.5)
            
            # Get the button's position on screen
            box = reward_button.bounding_box()
            if box:
                # Calculate the button center
                button_center_x = box['x'] + box['width'] / 2
                button_center_y = box['y'] + box['height'] / 2
                
                # Convert mm to pixels (approximate: 1mm ≈ 3.78 pixels at 96 DPI)
                pixels_up = mm_distance * 3.78
                
                # Calculate the target position (above the button)
                target_x = button_center_x
                target_y = button_center_y - pixels_up
                
                # Ensure target is within viewport
                target_y = max(10, target_y)
                
                # Move real mouse to the target position with human-like movement
                mouse = MouseController()
                current_pos = mouse.position
                steps = 20
                
                for i in range(steps):
                    progress = (i + 1) / steps
                    current_x = current_pos[0] + (target_x - current_pos[0]) * progress + random.randint(-2, 2)
                    current_y = current_pos[1] + (target_y - current_pos[1]) * progress + random.randint(-2, 2)
                    mouse.position = (int(current_x), int(current_y))
                    time.sleep(random.uniform(0.01, 0.03))
                
                # Small pause before clicking
                time.sleep(random.uniform(0.2, 0.5))
                
                # Click with the real mouse
                mouse.click(Button.left, 1)
                print(f"Clicked above reward button at position ({int(target_x)}, {int(target_y)})")
                return True
        
        print("Reward button not found")
        return False
        
    except Exception as e:
        print(f"Error clicking above button: {e}")
        return False

def run():
    browser = None
    context = None
    page = None
    playwright = None
    
    try:
        playwright = sync_playwright().start()
        
        # Launch browser without proxy
        browser = playwright.chromium.launch(
            headless=False
        )
        
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 1. Open URL
        page.goto("https://doc.mail.name.ng/")
        
        # Random stay duration (1 minute 30 seconds to 2 minutes)
        stay_duration = random.randint(90, 120)  # 90 to 120 seconds
        start_time = time.time()
        
        # 2. Human actions during the stay (continuous interactions)
        while time.time() - start_time < stay_duration:
            if random.random() < 0.5:
                human_scroll(page)
            else:
                human_move_and_hover(page)
            
            if random.random() < 0.3:
                human_mouse_movement()
            
            # Small pause between interactions
            time.sleep(random.uniform(1, 3))
        
        # 3. Scroll to top before clicking the button
        print("Stay duration complete. Scrolling to top...")
        scroll_to_top(page)
        time.sleep(random.uniform(1, 2))  # Brief pause after scrolling
        
        # 4. Find and click above the reward button with real mouse
        print("Looking for reward button...")
        click_above_button_with_real_mouse(page, mm)
        
        # Wait a moment after clicking
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
    
    print(f"\n--- Starting session ---")
    run()
    print("Script completed.")
