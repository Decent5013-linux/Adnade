import { chromium } from 'playwright';

const TARGET_URL = 'https://adnade.net/ptp/?user=zedred&subid=';
const TOTAL_TABS = 30;

const PROXY_SERVER = 'http://gateway.aluvia.io:8080';
const SECRET_URL = 'https://bot.vpsmail.name.ng/secret.txt';

const IP_CHECK_URL = 'https://api.ipify.org?format=json';

function randomSession() {
  return Math.random().toString(36).substring(2, 10);
}

// 🔥 Fetch proxy credentials from remote file
async function fetchProxyCreds() {
  try {
    const res = await fetch(SECRET_URL);
    const text = await res.text();
    const [username, password] = text.trim().split('\n');
    if (username && password) {
      return {
        username: username.trim(),
        password: password.trim()
      };
    }
  } catch (err) {
    console.log('Failed to fetch proxy creds.');
  }
  return null;
}

async function createWorker(tabIndex, getCreds) {

  let browser, context, page;
  let lastIP = null;
  let sessionId = randomSession();

  async function launch() {
    const proxyCreds = await getCreds();
    const sessionUsername = `${proxyCreds.username}-session-${sessionId}`;
    const sessionPassword = proxyCreds.password;

    try {
      browser = await chromium.launch({
        headless: false,
        proxy: {
          server: PROXY_SERVER,
          username: sessionUsername,
          password: sessionPassword
        },
        args: ['--no-sandbox', '--ignore-certificate-errors']
      });

      context = await browser.newContext({
        ignoreHTTPSErrors: true
      });

      context.setDefaultTimeout(0);
      context.setDefaultNavigationTimeout(0);

      page = await context.newPage();

      page.setDefaultTimeout(0);
      page.setDefaultNavigationTimeout(0);

      await page.goto(TARGET_URL, {
        waitUntil: 'domcontentloaded',
        timeout: 0
      }).catch(() => {});

      const res = await page.request.get(IP_CHECK_URL).catch(() => null);
      if (res) {
        const data = await res.json().catch(() => null);
        if (data) lastIP = data.ip;
      }

      console.log(`Tab ${tabIndex} started | Session ${sessionId} | IP: ${lastIP}`);

    } catch (err) {
      console.log(`Tab ${tabIndex} launch failed. Retrying...`);
      await restart();
    }
  }

  async function restart() {
    try {
      if (browser) await browser.close().catch(() => {});
    } catch {}

    sessionId = randomSession();
    lastIP = null;

    await launch();
  }

  async function monitor() {
    setInterval(async () => {
      try {
        if (!page || page.isClosed()) {
          console.log(`Tab ${tabIndex} page closed. Restarting...`);
          return restart();
        }

        const res = await page.request.get(IP_CHECK_URL).catch(() => null);
        if (!res) return;

        const data = await res.json().catch(() => null);
        if (!data) return;

        const currentIP = data.ip;

        if (lastIP && currentIP !== lastIP) {
          console.log(
            `Tab ${tabIndex} IP changed: ${lastIP} → ${currentIP}`
          );

          lastIP = currentIP;

          await page.goto(TARGET_URL, {
            waitUntil: 'domcontentloaded',
            timeout: 0
          }).catch(() => {});
        }

      } catch (err) {
        console.log(`Tab ${tabIndex} crashed. Restarting...`);
        await restart();
      }
    }, 2000);
  }

  await launch();
  monitor();

  return {
    restart
  };
}

// ---- START ALL SIMULTANEOUSLY ----
(async () => {
  console.log(`Launching ${TOTAL_TABS} workers...`);

  let currentCreds = await fetchProxyCreds();
  if (!currentCreds) {
    console.log('Could not retrieve initial proxy credentials.');
    process.exit(1);
  }

  const workers = await Promise.all(
    Array.from({ length: TOTAL_TABS }, (_, i) =>
      createWorker(i, fetchProxyCreds)
    )
  );

  console.log('All workers active.');

  // 🔁 GLOBAL credential watcher (every 5 minutes)
  setInterval(async () => {
    try {
      const latest = await fetchProxyCreds();
      if (!latest) return;

      if (
        latest.username !== currentCreds.username ||
        latest.password !== currentCreds.password
      ) {
        console.log('Global credential update detected. Restarting all workers...');

        currentCreds = latest;

        for (const worker of workers) {
          await worker.restart();
        }
      }
    } catch {}
  }, 5 * 60 * 1000);

  process.on('SIGINT', async () => {
    console.log('\nShutting down...');
    process.exit(0);
  });

})();
        
