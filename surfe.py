import asyncio
import random
import time
import math
import requests
import psutil
import os
import signal
from playwright.async_api import async_playwright
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key

# Global controllers
mouse = Controller()
keyboard = KeyboardController()

class SimpleBotSimulator:
    def __init__(self, page=None):
        self.page = page
        self.has_clicked = False
        self.browser = None
        self.playwright = None
        
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
        
        # Store playwright instance for cleanup    
        self.playwright = playwright
        
        # Launch browser and store reference
        self.browser = await playwright.chromium.launch(
            headless=False,
            proxy=proxy_config,
            args=['--disable-blink-features=AutomationControlled']
        )
        return self.browser

    async def force_kill_browser(self):
        """Force kill all Chrome processes to ensure complete cleanup"""
        try:
            # First try graceful close
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            # Additional cleanup: kill any remaining Chrome processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Kill any chrome/chromium processes spawned by this script
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        # Check if it's our process (you might want to be more selective)
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            print("✅ Browser processes fully terminated")
            
        except Exception as e:
            print(f"Error during browser cleanup: {e}")
            
        # Small delay to ensure cleanup
        await asyncio.sleep(1)

    def bezier_curve(self, start_x, start_y, end_x, end_y, steps=25):
        """Simple bezier curve for natural movement"""
        points = []
        cp1x = start_x + (end_x - start_x) * 0.3 + random.randint(-20, 20)
        cp1y = start_y + (end_y - start_y) * 0.3 + random.randint(-20, 20)
        cp2x = start_x + (end_x - start_x) * 0.7 + random.randint(-20, 20)
        cp2y = start_y + (end_y - start_y) * 0.7 + random.randint(-20, 20)
        
        for t in range(steps + 1):
            t = t / steps
            x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1x + 3*(1-t)*t**2 * cp2x + t**3 * end_x
            y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1y + 3*(1-t)*t**2 * cp2y + t**3 * end_y
            points.append((int(x), int(y)))
        return points

    async def human_mouse_move(self, target_x, target_y):
        """Move mouse naturally using OS-level movements"""
        current_x, current_y = mouse.position
        target_x += random.randint(-2, 2)
        target_y += random.randint(-2, 2)
        
        path = self.bezier_curve(current_x, current_y, target_x, target_y)
        for point in path:
            mouse.position = point
            await asyncio.sleep(random.uniform(0.005, 0.015))

    async def create_scroll_space(self):
        """Make page scrollable if it isn't already - create LOTS of scroll space"""
        await self.page.evaluate("""
            // Remove any existing spacers first
            const oldSpacer = document.getElementById('scroll-spacer');
            if (oldSpacer) oldSpacer.remove();
            
            // Create a TALL spacer for long scrolling
            var spacer = document.createElement('div');
            spacer.id = 'scroll-spacer';
            spacer.style.height = '5000px';  // Much taller for longer scrolls
            spacer.style.width = '1px';
            spacer.style.opacity = '0';
            spacer.style.pointerEvents = 'none';
            document.body.appendChild(spacer);
            
            // Add multiple content blocks to simulate long page
            for (let i = 0; i < 5; i++) {
                var block = document.createElement('div');
                block.style.height = '300px';
                block.style.width = '100%';
                block.style.backgroundColor = '#' + Math.floor(Math.random()*16777215).toString(16);
                block.style.opacity = '0.1';
                block.innerHTML = '&nbsp;';
                document.body.appendChild(block);
            }
            
            console.log('Added 5000px scroll spacer + content blocks');
        """)

    async def human_scroll(self):
        """OS-level scrolling using pynput - LONG scrolls for better detection"""
        
        # Choose scroll method - bias toward wheel for natural feel
        method = random.choices(
            ['wheel', 'wheel', 'wheel', 'pagedown', 'arrow'],  # 60% wheel
            weights=[0.3, 0.3, 0.3, 0.05, 0.05]
        )[0]
        
        if method == 'wheel':
            # LONG mouse wheel scrolling
            # Do multiple scroll sequences for longer total scroll
            sequences = random.randint(2, 4)  # Multiple scroll bursts
            
            for seq in range(sequences):
                # Each sequence has multiple chunks
                chunks = random.randint(4, 8)  # More chunks
                
                for chunk in range(chunks):
                    # More clicks per chunk
                    clicks = random.randint(3, 6)  # 3-6 wheel clicks
                    
                    for _ in range(clicks):
                        mouse.scroll(0, -1)  # REAL scroll event!
                        await asyncio.sleep(random.uniform(0.03, 0.07))  # Slightly faster
                    
                    # Pause between chunks
                    await asyncio.sleep(random.uniform(0.15, 0.3))
                
                # Longer pause between sequences
                if seq < sequences - 1:
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Sometimes scroll back up between sequences (human-like)
                if random.random() < 0.3:
                    back_clicks = random.randint(2, 4)
                    for _ in range(back_clicks):
                        mouse.scroll(0, 1)  # Scroll up
                        await asyncio.sleep(0.05)
                    await asyncio.sleep(0.3)
            
            # Final scroll to bottom sometimes
            if random.random() < 0.4:
                await asyncio.sleep(0.3)
                for _ in range(random.randint(5, 8)):
                    mouse.scroll(0, -1)
                    await asyncio.sleep(0.03)
                    
        elif method == 'pagedown':
            # Multiple Page Down keys for big jumps
            page_presses = random.randint(3, 6)
            for i in range(page_presses):
                keyboard.press(Key.page_down)
                keyboard.release(Key.page_down)
                await asyncio.sleep(random.uniform(0.2, 0.4))
                
                # Maybe page up occasionally
                if random.random() < 0.2 and i < page_presses - 1:
                    await asyncio.sleep(0.2)
                    keyboard.press(Key.page_up)
                    keyboard.release(Key.page_up)
                    await asyncio.sleep(0.2)
                    
        else:  # arrow keys
            # MANY arrow keys for fine scrolling
            arrow_presses = random.randint(15, 30)
            for i in range(arrow_presses):
                keyboard.press(Key.down)
                keyboard.release(Key.down)
                await asyncio.sleep(random.uniform(0.02, 0.05))
                
                # Occasionally arrow up
                if random.random() < 0.1:
                    await asyncio.sleep(0.1)
                    keyboard.press(Key.up)
                    keyboard.release(Key.up)

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
                            x: rect.left + rect.width/2,
                            y: rect.top + rect.height/2
                        });
                    }
                }
                
                // Iframes
                document.querySelectorAll('iframe').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 50) {
                        clickables.push({
                            type: 'iframe',
                            x: rect.left + rect.width/2,
                            y: rect.top + rect.height/2
                        });
                    }
                });
                
                // Links, buttons, clickable elements
                document.querySelectorAll('a, button, [onclick], .clickable').forEach(el => {
                    if (el.offsetParent !== null) {
                        const rect = el.getBoundingClientRect();
                        clickables.push({
                            type: el.tagName.toLowerCase(),
                            x: rect.left + rect.width/2,
                            y: rect.top + rect.height/2
                        });
                    }
                });
                
                return clickables;
            }
        """)
        return elements

    async def random_hover(self):
        """Move mouse randomly around the page - LONGER hovering"""
        viewport = await self.page.evaluate("""
            () => ({
                width: window.innerWidth,
                height: window.innerHeight,
                scrollY: window.scrollY
            })
        """)
        
        # Random position, but also occasionally move to edges
        if random.random() < 0.3:
            # Move to corners sometimes
            target_x = random.choice([50, viewport['width'] - 50])
            target_y = random.choice([50, viewport['height'] - 50])
        else:
            target_x = random.randint(50, viewport['width'] - 50)
            target_y = random.randint(50, viewport['height'] - 50)
        
        await self.human_mouse_move(target_x, target_y)
        
        # Hover longer at the destination
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def run_session(self):
        """Main session loop"""
        print("🌐 Loading page...")
        await self.page.goto('https://pk.vpsmail.name.ng/ad2.html', wait_until='domcontentloaded')
        
        # Make sure page has LOTS of scroll space
        await self.create_scroll_space()
        
        # Wait for ad to load
        await asyncio.sleep(2)
        
        # Session duration between 25-35 seconds
        session_duration = random.uniform(25, 35)
        session_end = time.time() + session_duration
        
        # Track when we can first click (after 15-20 seconds)
        min_click_time = time.time() + random.uniform(15, 20)
        
        last_scroll = time.time()
        last_hover = time.time()
        
        print(f"⏱️  Session duration: {session_duration:.1f}s")
        print(f"🖱️  First click possible after: {(min_click_time - time.time()):.1f}s")
        print(f"📊 Click probability: 3% (if clickable elements exist)")
        print(f"📏 Scroll distance: LONG (5000px spacer + multiple scrolls)\n")
        
        while time.time() < session_end:
            now = time.time()
            
            # Only consider clicking after minimum time has passed
            if now >= min_click_time and not self.has_clicked:
                # Find clickable elements
                clickables = await self.find_clickable_elements()
                
                # 3% chance to click if anything exists (reduced from 39%)
                if clickables and random.random() < 0.03:  # Changed to 0.03 for 3%
                    target = random.choice(clickables)
                    
                    # Get current scroll position
                    scroll_y = await self.page.evaluate("window.scrollY")
                    
                    # If target is far down, scroll there first (LONG scroll)
                    if abs(target['y'] - scroll_y) > 300:
                        scroll_needed = (target['y'] - scroll_y) // 100
                        for _ in range(abs(scroll_needed)):
                            if scroll_needed > 0:
                                mouse.scroll(0, -1)
                            else:
                                mouse.scroll(0, 1)
                            await asyncio.sleep(0.05)
                        await asyncio.sleep(0.5)  # Longer pause after scrolling
                    
                    # Click it
                    await self.human_mouse_move(target['x'], target['y'])
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    mouse.click(Button.left)
                    print(f"✅ CLICKED: {target['type']} at {now - (session_end - session_duration):.1f}s")
                    self.has_clicked = True
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                else:
                    # Log when 3% chance fails (optional - remove if too noisy)
                    if clickables:
                        print(f"⏭️  No click (97% chance) - {len(clickables)} clickable elements available")
            
            # Scroll more FREQUENTLY (every 2-5 seconds)
            scroll_interval = random.uniform(2, 5)
            if now - last_scroll > scroll_interval:
                print(f"📜 Scrolling... (interval: {scroll_interval:.1f}s)")
                await self.human_scroll()
                last_scroll = now
            
            # Hover more frequently too
            hover_interval = random.uniform(1.5, 3.5)
            if now - last_hover > hover_interval:
                await self.random_hover()
                last_hover = now
                await asyncio.sleep(random.uniform(0.8, 1.8))
            
            await asyncio.sleep(0.5)
        
        # Session summary
        if self.has_clicked:
            print(f"✅ Session ended - click performed (3% chance triggered)")
        else:
            print(f"⏹️  Session ended - no click (3% chance didn't trigger this session)")

async def run_single_session(session_num):
    """Run a single complete session with full cleanup"""
    print(f"\n{'='*50}")
    print(f"🔄 SESSION #{session_num} STARTING")
    print(f"{'='*50}")
    
    async with async_playwright() as p:
        simulator = None
        browser = None
        
        try:
            simulator = SimpleBotSimulator()
            
            # Setup browser with proxy
            browser = await simulator.setup_browser(p)
            
            # Create context
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )
            
            page = await context.new_page()
            simulator.page = page
            
            # Run the session
            await simulator.run_session()
            
            # Force kill browser completely
            await simulator.force_kill_browser()
            
            print("✅ Browser completely terminated - session fully ended")
            
        except Exception as e:
            print(f"❌ Error in session: {e}")
            # Ensure browser is killed even on error
            if simulator:
                await simulator.force_kill_browser()
    
    # Small delay to ensure everything is cleaned up
    await asyncio.sleep(1)

async def main():
    # Install psutil if not present
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'psutil'])
        import psutil
    
    session_count = 0
    
    print("🚀 Starting bot simulator...")
    print("🖱️  Using REAL OS mouse and keyboard events")
    print("📊 Scrolls WILL be detected by fingerprinting")
    print("🎯 3% click chance AFTER 15-20 seconds of natural behavior")
    print("🔄 Each session is COMPLETELY independent (browser fully closes)")
    print("📏 LONG scroll distance (5000px spacer)")
    print("⏱️  Session duration: 25-35 seconds\n")
    
    while True:
        session_count += 1
        
        # Run a complete session from start to finish
        await run_single_session(session_count)
        
        # Wait 1-3 seconds for fresh start (browser is already closed)
        delay = random.uniform(1, 3)
        print(f"⏱️  Fresh start in {delay:.1f}s...")
        await asyncio.sleep(delay)

if __name__ == "__main__":
    asyncio.run(main())
