import time
import random
import requests
from playwright.sync_api import sync_playwright
from pynput.mouse import Controller as MouseController, Button
import threading
import sys

def get_credentials():
    """Retrieves username and password from the provided URL."""
    response = requests.get("https://telead.mail.name.ng/public.txt")
    lines = response.text.strip().split('\n')
    return lines[0].strip(), lines[1].strip()

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
        
        if random.random() < 0.3:
            mouse.click(Button.left)
            time.sleep(random.uniform(0.2, 0.5))

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

def keep_page_focused(page):
    """Continuously ensures the page stays focused using Playwright's built-in methods."""
    while True:
        try:
            # Bring page to front using Playwright's method
            page.bring_to_front()
            # Ensure the page has focus by clicking on body
            page.locator('body').click(timeout=1000)
        except:
            pass
        time.sleep(1)  # Check every second

def perform_page_interactions(page, stay_duration):
    """Performs all page interactions ensuring we stay within the time limit."""
    start_time = time.time()
    
    # Start human movements
    human_move_and_hover(page)
    human_scroll(page)
    
    # Calculate remaining time
    elapsed = time.time() - start_time
    remaining_time = stay_duration - elapsed
    
    if remaining_time <= 0:
        return
    
    # Only perform interactions if we have enough time
    if remaining_time > 5:  # Minimum 5 seconds for interactions
        roll = random.random() * 100
        
        if roll <= 90:
            link = page.locator("a[href]").first
            if link.count() > 0:
                # Wait a bit before clicking
                time.sleep(random.uniform(1, 3))
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
                time.sleep(random.uniform(1, 2))
                ins_element.hover()
                time.sleep(random.uniform(0.5, 1.0))
                ins_element.click()
                time.sleep(random.uniform(2, 4))
    
    # Fill remaining time with passive activities
    elapsed = time.time() - start_time
    remaining_time = stay_duration - elapsed
    
    while remaining_time > 0:
        # Do small random movements or scrolling to fill time
        if random.random() < 0.5:
            step = random.randint(50, 200)
            page.mouse.wheel(0, step)
        else:
            x, y = random.randint(100, 1180), random.randint(100, 700)
            page.mouse.move(x, y, steps=5)
        
        time.sleep(random.uniform(0.5, 2))
        elapsed = time.time() - start_time
        remaining_time = stay_duration - elapsed

def run_single_session():
    """Runs a single browser session."""
    username, password = get_credentials()
    proxy_server = "http://gateway.aluvia.io:8080"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            proxy={
                "server": proxy_server,
                "username": username,
                "password": password
            }
        )
        
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # Navigate to the URL first
        page.goto("https://telead.mail.name.ng/ouo.html")
        
        # Bring page to front immediately
        page.bring_to_front()
        
        # Start focus keeper thread
        focus_thread = threading.Thread(target=keep_page_focused, args=(page,), daemon=True)
        focus_thread.start()
        
        # Random stay duration (20-40 seconds)
        stay_duration = random.randint(20, 40)
        print(f"Session starting - Stay duration: {stay_duration} seconds")
        
        # Perform all interactions within the time limit
        perform_page_interactions(page, stay_duration)
        
        print(f"Session completed - Duration: {stay_duration} seconds")
        browser.close()

def run_continuous():
    """Runs the browser session continuously in a loop."""
    session_count = 0
    
    while True:
        try:
            session_count += 1
            print(f"\n=== Starting session {session_count} ===")
            run_single_session()
            
            # Random delay between sessions (5-15 seconds)
            delay = random.randint(5, 15)
            print(f"Waiting {delay} seconds before next session...")
            time.sleep(delay)
            
        except KeyboardInterrupt:
            print("\n\nProgram stopped by user.")
            sys.exit(0)
        except Exception as e:
            print(f"Error in session {session_count}: {str(e)}")
            print("Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    print("Starting continuous browser automation...")
    print("Press Ctrl+C to stop")
    run_continuous()
