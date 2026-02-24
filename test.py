import asyncio
import gzip
import random
import aiohttp
import os
import string
from playwright.async_api import async_playwright

try:
    from pynput.mouse import Controller as MouseController
    mouse = MouseController()
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

# ================= CONFIG =================
MOBILE_UA_FILE = 'mobile_user_agents_500k_with_viewport.txt.gz'
DESKTOP_UA_FILE = 'desktop_user_agents_500k_with_viewport.txt.gz'
MOBILE_WEIGHT = 0.8
RARE_UNDERSIZE_CHANCE = 0.05

# ================= PROXY CONFIG =================
PROXY_SERVER = "gateway.aluvia.io:8080"
SECRET_URL = "http://bot.vpsmail.name.ng/secret.txt"
SESSION_FILE = "proxy_session.txt"

def generate_random_string(length=12):
    """Generate a random string of specified length"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

async def get_proxy_credentials():
    """Fetch proxy username and password from secret URL and handle session"""
    # Read existing session if file exists
    existing_session = None
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            existing_session = f.read().strip()
    
    # Decide whether to use existing session or generate new one
    use_existing = False
    if existing_session:
        # 67-82% chance to generate new, 18-33% chance to use existing
        if random.random() < 0.75:  # 75% generate new, 25% use existing (within the 67-82% range)
            use_existing = False
        else:
            use_existing = True
    
    async with aiohttp.ClientSession() as session:
        async with session.get(SECRET_URL) as response:
            text = await response.text()
            lines = text.strip().split('\n')
            if len(lines) >= 2:
                username = lines[0].strip()
                password = lines[1].strip()
                
                if use_existing and existing_session:
                    # Use the existing session
                    session_id = existing_session
                    print(f"Using existing session: {session_id}")
                else:
                    # Generate new session
                    session_id = generate_random_string(12)
                    # Save to file
                    with open(SESSION_FILE, 'w') as f:
                        f.write(session_id)
                    print(f"Generated new session: {session_id}")
                
                # Format username with session
                username_with_session = f"{username}-session-{session_id}"
                return username_with_session, password
            raise ValueError("Invalid secret format")

# ================= REFERRER CONFIG =================
REFERRERS = {
    "ff.vpsmail.name.ng": 0.35,      # frequent
    "zerads.com": 0.30,               # frequent but not like vpsmail
    "miningblocks.club": 0.20,         # less frequent
    "easyhits4u.com": 0.10,            # not too frequent
    "m.facebook.com": 0.05             # rare
}

def get_random_referrer():
    """Returns a random referrer URL based on configured weights"""
    referrers = list(REFERRERS.keys())
    weights = list(REFERRERS.values())
    return f"https://{random.choices(referrers, weights=weights, k=1)[0]}"

# ================= HELPERS =================

def load_uas(path):
    with open(path, 'rb') as f:
        data = gzip.decompress(f.read()).decode()
    return [line.split('|')[0] for line in data.strip().split('\n') if line]

def rand(min_v, max_v):
    return random.randint(min_v, max_v)

def random_desktop_size():
    return {"width": rand(1024, 1920), "height": rand(450, 1080)}

def random_mobile_size(is_android):
    portrait = random.random() > 0.2
    return ({"width": rand(300, 600), "height": rand(600, 1024)} if portrait
            else {"width": rand(600, 1024), "height": rand(300, 600)})

async def human_delay(min_ms=200, max_ms=800):
    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

# ================= VIEWABILITY HELPERS =================

def get_mobile_viewability():
    """Mobile: 92% full view (1.0), 7% poor (0.0-0.4), 1% partial (0.4-0.7)"""
    roll = random.random()
    if roll < 0.92:
        return 1.0
    elif roll < 0.99:
        return random.uniform(0.0, 0.4)
    else:
        return random.uniform(0.4, 0.7)

def get_desktop_viewability():
    """Desktop: 20% poor (0.3-0.6), 50% medium (0.6-0.9), 30% good (0.9-1.0)"""
    return random.choices(
        [
            random.uniform(0.3, 0.6),   # poor
            random.uniform(0.6, 0.9),   # medium
            random.uniform(0.9, 1.0)    # good
        ],
        weights=[0.2, 0.5, 0.3],
        k=1
    )[0]

# ================= MOBILE INTERACTION =================

async def mobile_interact(page, viewport, ua):
    """Touch scroll -> touch on iframe to focus (65-80%) -> second touch to click (10-25% of focused)"""

    # --- Step 1: Real touch scroll ---
    start_x = rand(int(viewport["width"] * 0.3), int(viewport["width"] * 0.7))
    start_y = rand(int(viewport["height"] * 0.5), int(viewport["height"] * 0.7))
    end_y = start_y - rand(150, 400)

    cdp = await page.context.new_cdp_session(page)

    await cdp.send("Input.dispatchTouchEvent", {
        "type": "touchStart",
        "touchPoints": [{"x": start_x, "y": start_y}]
    })
    await human_delay(50, 150)

    steps = rand(5, 12)
    for i in range(1, steps + 1):
        cur_y = start_y + (end_y - start_y) * i / steps
        await cdp.send("Input.dispatchTouchEvent", {
            "type": "touchMove",
            "touchPoints": [{"x": start_x, "y": int(cur_y)}]
        })
        await human_delay(15, 50)

    await cdp.send("Input.dispatchTouchEvent", {
        "type": "touchEnd",
        "touchPoints": []
    })
    await human_delay(300, 700)

    print("[Mobile] Touch scroll done")

    # --- Step 2: Touch ON the iframe ---
    focus_chance = random.uniform(0.65, 0.80)
    if random.random() < focus_chance:
        iframe_el = await page.query_selector("iframe")
        if iframe_el:
            box = await iframe_el.bounding_box()
            if box:

                touch_x = int(box["x"] + rand(10, int(box["width"] - 10)))
                touch_y = int(box["y"] + rand(10, int(box["height"] - 10)))

                is_ios = 'iPhone' in ua or 'iPad' in ua

                if is_ios:
                    await page.touchscreen.tap(touch_x, touch_y)
                    await human_delay(200, 500)
                    print(f"[iOS] Natural tap at ({touch_x}, {touch_y}) — no focus()")
                else:
                    await cdp.send("Input.dispatchTouchEvent", {
                        "type": "touchStart",
                        "touchPoints": [{"x": touch_x, "y": touch_y}]
                    })
                    await human_delay(80, 200)

                    await cdp.send("Input.dispatchTouchEvent", {
                        "type": "touchEnd",
                        "touchPoints": []
                    })
                    await human_delay(200, 500)

                    print(f"[Android] Touched iframe at ({touch_x}, {touch_y})")

                # --- Step 3: Second tap ---
                click_chance = random.uniform(0.10, 0.25)
                if random.random() < click_chance:
                    tap_x = int(box["x"] + rand(10, int(box["width"] - 10)))
                    tap_y = int(box["y"] + rand(10, int(box["height"] - 10)))

                    if is_ios:
                        await page.touchscreen.tap(tap_x, tap_y)
                        print(f"[iOS] Second natural tap at ({tap_x}, {tap_y})")
                    else:
                        await cdp.send("Input.dispatchTouchEvent", {
                            "type": "touchStart",
                            "touchPoints": [{"x": tap_x, "y": tap_y}]
                        })
                        await human_delay(50, 120)

                        await cdp.send("Input.dispatchTouchEvent", {
                            "type": "touchEnd",
                            "touchPoints": []
                        })
                        print(f"[Android] Tapped iframe at ({tap_x}, {tap_y})")
                else:
                    print("[Mobile] Focused but no click (dice roll)")
            else:
                print("[Mobile] Iframe has no bounding box, skip")
        else:
            print("[Mobile] No iframe found on page")
    else:
        print("[Mobile] Skipped iframe focus (dice roll)")

# ================= DESKTOP INTERACTION =================

async def desktop_interact(page, viewport):
    hover_chance = random.uniform(0.50, 0.80)
    if random.random() >= hover_chance:
        print("[Desktop] Skipped iframe hover (dice roll)")
        return

    iframe_el = await page.query_selector("iframe")
    if not iframe_el:
        print("[Desktop] No iframe found on page")
        return

    box = await iframe_el.bounding_box()
    if not box:
        print("[Desktop] Iframe has no bounding box")
        return

    target_x = int(box["x"] + rand(10, int(box["width"] - 10)))
    target_y = int(box["y"] + rand(10, int(box["height"] - 10)))

    if HAS_PYNPUT:
        cur_x, cur_y = mouse.position
        steps = rand(15, 30)
        for i in range(1, steps + 1):
            ix = int(cur_x + (target_x - cur_x) * i / steps)
            iy = int(cur_y + (target_y - cur_y) * i / steps)
            mouse.position = (ix, iy)
            await asyncio.sleep(random.uniform(0.005, 0.02))
        print(f"[Desktop] pynput mouse moved to ({target_x}, {target_y})")
    else:
        await page.mouse.move(target_x, target_y, steps=rand(10, 20))
        print(f"[Desktop] Playwright mouse moved to ({target_x}, {target_y})")

    await human_delay(200, 600)

    await iframe_el.focus()
    print("[Desktop] Iframe focused")
    await human_delay(150, 400)

    click_chance = random.uniform(0.07, 0.12)
    if random.random() < click_chance:
        if HAS_PYNPUT:
            from pynput.mouse import Button
            mouse.click(Button.left, 1)
            print(f"[Desktop] pynput clicked at ({target_x}, {target_y})")
        else:
            await page.mouse.click(target_x, target_y)
            print(f"[Desktop] Playwright clicked at ({target_x}, {target_y})")
    else:
        print("[Desktop] Focused but no click (dice roll)")

# ================= IFRAME DETECTION =================

async def wait_for_iframe(page, timeout=30000):
    """Wait for iframe to appear on the page without waiting for page load"""
    try:
        # Start checking for iframe immediately without waiting for load event
        await page.wait_for_selector("iframe", timeout=timeout, state="attached")
        print("[Iframe] Detected on page")
        return True
    except Exception as e:
        print(f"[Iframe] Not detected within timeout: {e}")
        return False

# ================= MAIN LOOP =================

async def run_session():
    # Fetch proxy credentials
    username, password = await get_proxy_credentials()
    print(f"Proxy credentials fetched - Username: {username}")

    mobile_uas = load_uas(MOBILE_UA_FILE)
    desktop_uas = load_uas(DESKTOP_UA_FILE)

    is_mobile = random.random() < MOBILE_WEIGHT

    if is_mobile:
        ua = random.choice(mobile_uas)
        is_android = 'Android' in ua
        is_iphone = 'iPhone' in ua
        is_ipad = 'iPad' in ua

        if is_android:
            platform_val = "Linux armv8l"
        elif is_iphone:
            platform_val = "iPhone"
        elif is_ipad:
            platform_val = "iPad"
        else:
            platform_val = "Linux armv7l"

        viewport = random_mobile_size(is_android)
    else:
        ua = random.choice(desktop_uas)
        if 'Windows' in ua:
            platform_val = random.choice(["Win32", "Win64"])
        elif 'Mac' in ua:
            platform_val = "MacIntel"
        else:
            platform_val = "Linux x86_64"

        viewport = random_desktop_size()

    # Get random referrer
    referrer = get_random_referrer()
    print(f"Selected referrer: {referrer}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Create context with proxy
        context = await browser.new_context(
            user_agent=ua,
            viewport=viewport,
            is_mobile=is_mobile,
            has_touch=is_mobile,
            device_scale_factor=rand(2, 3) if is_mobile else 1,
            proxy={
                "server": PROXY_SERVER,
                "username": username,
                "password": password
            }
        )
        page = await context.new_page()

        # Add scrollbar removal for mobile only
        if is_mobile:
            await page.add_init_script("""
            (function() {
                const style = document.createElement('style');
                style.innerHTML = `
                    ::-webkit-scrollbar {
                        display: none !important;
                    }
                    body {
                        overflow-y: hidden !important;
                    }
                `;
                document.documentElement.appendChild(style);
            })();
            """)
            print("[Mobile] Vertical scrollbar removal injected")

        await page.add_init_script(f"""
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{platform_val}'
            }});
        """)

        # IntersectionObserver with viewability spoofing
        await page.add_init_script(f"""
            const OriginalObserver = window.IntersectionObserver;
            window.IntersectionObserver = function(callback, options) {{
                const wrapped = function(entries, observer) {{
                    entries.forEach(entry => {{
                        if (!{'true' if is_mobile else 'false'}) {{
                            // Desktop: 20% poor (0.3-0.6), 50% medium (0.6-0.9), 30% good (0.9-1.0)
                            const roll = Math.random();
                            let ratio;
                            if (roll < 0.2) {{
                                ratio = 0.3 + Math.random() * 0.3;  // poor: 0.3-0.6
                            }} else if (roll < 0.7) {{
                                ratio = 0.6 + Math.random() * 0.3;  // medium: 0.6-0.9
                            }} else {{
                                ratio = 0.9 + Math.random() * 0.1;  // good: 0.9-1.0
                            }}
                            Object.defineProperty(entry, 'intersectionRatio', {{ get: () => ratio }});
                            Object.defineProperty(entry, 'isIntersecting', {{ get: () => ratio > 0 }});
                        }} else {{
                            // Mobile: 92% full (1.0), 7% poor (0.0-0.4), 1% partial (0.4-0.7)
                            const roll = Math.random();
                            let ratio;
                            if (roll < 0.92) {{
                                ratio = 1.0;
                            }} else if (roll < 0.99) {{
                                ratio = Math.random() * 0.4;  // 0.0-0.4
                            }} else {{
                                ratio = 0.4 + Math.random() * 0.3;  // 0.4-0.7
                            }}
                            Object.defineProperty(entry, 'intersectionRatio', {{ get: () => ratio }});
                            Object.defineProperty(entry, 'isIntersecting', {{ get: () => ratio > 0 }});
                        }}
                    }});
                    callback(entries, observer);
                }};
                return new OriginalObserver(wrapped, options);
            }};
        """)

        # Navigate without waiting for page load
        await page.goto('https://www.rotate4all.com/ptp/promote-299306', referer=referrer, wait_until="commit")

        print(f"Mode: {'Mobile' if is_mobile else 'Desktop'}")
        print(f"Platform: {platform_val}")
        print(f"Viewport: {viewport}")
        print(f"Referrer: {referrer}")
        print(f"Proxy: {PROXY_SERVER}")

        # Wait for iframe to be detected before proceeding with interactions
        iframe_detected = await wait_for_iframe(page)
        
        if iframe_detected:
            print("[Iframe] Ready for interaction")
            await human_delay(500, 1500)

            if is_mobile:
                await mobile_interact(page, viewport, ua)
            else:
                await desktop_interact(page, viewport)
        else:
            print("[Iframe] No iframe detected - skipping interactions")

        # Determine session duration before closing
        duration_roll = random.random()
        if duration_roll < 0.8:  # 40-95% range (using 80% as middle ground)
            session_duration = random.randint(3, 9)
            print(f"Session duration: {session_duration} seconds (short/frequent)")
        else:  # 5-20% range (using 20% as remaining)
            session_duration = random.randint(10, 14)
            print(f"Session duration: {session_duration} seconds (long/less frequent)")
        
        await asyncio.sleep(session_duration)
        await browser.close()
        print("Browser closed - preparing next session...")

async def main():
    """Main loop that runs continuously"""
    session_count = 0
    while True:
        session_count += 1
        print(f"\n{'='*50}")
        print(f"Starting session #{session_count}")
        print(f"{'='*50}")
        
        try:
            await run_session()
        except Exception as e:
            print(f"Error in session #{session_count}: {e}")
            await asyncio.sleep(5)  # Brief pause before retrying if error occurs
        
        # Small random delay between sessions (1-3 seconds)
        between_sessions_delay = random.randint(1, 3)
        print(f"Waiting {between_sessions_delay} seconds before next session...")
        await asyncio.sleep(between_sessions_delay)

if __name__ == "__main__":
    asyncio.run(main())
