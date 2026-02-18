import { chromium } from 'playwright';
import { exec } from 'child_process';
import https from 'https';
import { promisify } from 'util';
const execP = promisify(exec);

const TARGET_URL = 'https://adnade.net/ptp/?user=zedred&subid=';
const TOTAL_TABS = 30;

const PROXY_SERVER = 'http://gateway.aluvia.io:8080';
let BASE_USERNAME = 'W2VnwvuJ';
let PROXY_PASSWORD = 'TfWwyEJH';

const IP_CHECK_URL = 'https://api.ipify.org?format=json';
const SECRET_URL = 'https://bot.vpsmail.name.ng/secret.txt';

const NT = 1;

const pages = []; // track pages only (no worker interference)

function randomSession() {
  return Math.random().toString(36).substring(2, 10);
}

/* ---------------- SECRET FETCH ---------------- */

function fetchSecret() {
  return new Promise(resolve => {
    https.get(SECRET_URL, res => {
      let raw = '';
      res.on('data', d => raw += d);
      res.on('end', () => {
        const lines = raw.trim().split(/\r?\n/).filter(Boolean);
        if (lines.length >= 2) {
          resolve({ user: lines[0], pass: lines[1] });
        } else resolve(null);
      });
    }).on('error', () => resolve(null));
  });
}

/* ---------------- PROXY CHECK ---------------- */

async function proxyAlive(user, pass) {
  try {
    const host = PROXY_SERVER.replace(/^https?:\/\//,'');
    const cmd = `curl -s --max-time 8 -x "http://${user}:${pass}@${host}" ${IP_CHECK_URL}`;
    const { stdout } = await execP(cmd);
    if (!stdout) return false;
    const json = JSON.parse(stdout);
    return !!json.ip;
  } catch {
    return false;
  }
}

/* ---------------- VISIT WITHOUT PROXY ---------------- */

async function visitNoProxy() {
  try {
    const b = await chromium.launch({ headless: true });
    const p = await b.newPage();
    await p.goto('https://bot.vpsmail.name.ng',{ timeout:15000 }).catch(()=>{});
    await b.close();
  } catch {}
}

/* ---------------- REFRESH ALL TABS ---------------- */

async function refreshAllTabs() {
  for (const p of pages) {
    try {
      if (!p.isClosed())
        await p.reload({ waitUntil:'domcontentloaded', timeout:0 }).catch(()=>{});
    } catch {}
  }
}

/* ---------------- SECRET POLLING PROCESS ---------------- */

let polling = false;

async function startSecretPolling() {
  if (polling) return;
  polling = true;

  if (NT === 1) await visitNoProxy();

  console.log("Polling secret.txt every 10s for new creds...");

  while (true) {
    const s = await fetchSecret();
    if (s && (s.user !== BASE_USERNAME || s.pass !== PROXY_PASSWORD)) {

      console.log("New proxy credentials detected.");

      BASE_USERNAME = s.user;
      PROXY_PASSWORD = s.pass;

      await refreshAllTabs();

      break;
    }
    await new Promise(r=>setTimeout(r,10000));
  }

  polling = false;
}

/* ---------------- PROXY MONITOR PROCESS ---------------- */

setInterval(async ()=>{
  const ok = await proxyAlive(BASE_USERNAME, PROXY_PASSWORD);
  if (!ok) {
    console.log("Proxy not working — waiting for new creds...");
    startSecretPolling();
  }
}, 5000);

/* ---------------- WORKER (UNCHANGED LOGIC) ---------------- */

async function createWorker(tabIndex) {

  let browser, context, page;
  let lastIP = null;
  let sessionId = randomSession();
  let sessionUsername = `${BASE_USERNAME}-session-${sessionId}`;

  async function launch() {
    try {
      browser = await chromium.launch({
        headless: false,
        proxy: {
          server: PROXY_SERVER,
          username: sessionUsername,
          password: PROXY_PASSWORD
        },
        args: ['--no-sandbox', '--ignore-certificate-errors']
      });

      context = await browser.newContext({
        ignoreHTTPSErrors: true
      });

      context.setDefaultTimeout(0);
      context.setDefaultNavigationTimeout(0);

      page = await context.newPage();
      pages.push(page); // only addition

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
    sessionUsername = `${BASE_USERNAME}-session-${sessionId}`;
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
}

/* ---------------- INITIAL START ---------------- */

(async () => {

  console.log("Checking secret.txt for initial credentials...");
  const init = await fetchSecret();
  if (init) {
    BASE_USERNAME = init.user;
    PROXY_PASSWORD = init.pass;
    console.log("Using credentials from secret.txt");
  }

  console.log(`Launching ${TOTAL_TABS} workers...`);

  await Promise.all(
    Array.from({ length: TOTAL_TABS }, (_, i) => createWorker(i))
  );

  console.log('All workers active.');

  process.on('SIGINT', async () => {
    console.log('\nShutting down...');
    process.exit(0);
  });

})();
      
