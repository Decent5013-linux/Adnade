const { chromium } = require('playwright');
const http = require('http');

let currentProxyAuth = null;

async function getProxyAuth() {
    return new Promise((resolve, reject) => {
        http.get('http://telead.mail.name.ng/public.txt', (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                const [username, password] = data.trim().split('\n');
                resolve({ username: username.trim(), password: password.trim() });
            });
        }).on('error', reject);
    });
}

async function browsingLoop(browser, index) {
    while (true) {
        let context = null;
        try {
            context = await browser.newContext({
                proxy: {
                    server: 'http://gateway.aluvia.io:8080',
                    username: currentProxyAuth.username,
                    password: currentProxyAuth.password
                }
            });

            const page = await context.newPage();
            
            await page.route('**/*', (route) => {
                const request = route.request();
                if (request.isNavigationRequest() && request.redirectedFrom()) {
                    return route.abort();
                }
                return route.continue();
            });

            await page.goto('https://telead.mail.name.ng/test.html', { 
                waitUntil: 'domcontentloaded',
                timeout: 10000 
            });
            await page.waitForTimeout(3000);
        } catch (e) {
        } finally {
            if (context) {
                await context.close().catch(() => {});
            }
        }
    }
}

(async () => {
    currentProxyAuth = await getProxyAuth();
    
    const browser = await chromium.launch({
        headless: false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    for (let i = 0; i < 5; i++) {
        browsingLoop(browser, i);
    }

    setInterval(async () => {
        try {
            const newAuth = await getProxyAuth();
            if (newAuth.username !== currentProxyAuth.username || 
                newAuth.password !== currentProxyAuth.password) {
                currentProxyAuth = newAuth;
            }
        } catch (e) {}
    }, 300000);

    process.on('SIGINT', async () => {
        await browser.close();
        process.exit(0);
    });

    process.on('SIGTERM', async () => {
        await browser.close();
        process.exit(0);
    });
})();
