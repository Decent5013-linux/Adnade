import { chromium } from "playwright";
import https from "https";

const TARGET_URL = "https://bot.vpsmail.name.ng/ad.html";
const TABS = 30;
const PROXY_SERVER = "http://gateway.aluvia.io:8080";
const CREDS_URL = "https://bot.vpsmail.name.ng/secret.txt";
const CHECK_INTERVAL = 5 * 60 * 1000; // 5 min

/* fetch proxy credentials */
function getCreds() {
  return new Promise((resolve, reject) => {
    https.get(CREDS_URL, res => {
      let data = "";
      res.on("data", c => (data += c));
      res.on("end", () => {
        const [user, pass] = data.trim().split(/\r?\n/);
        resolve({ user: user.trim(), pass: pass.trim() });
      });
    }).on("error", reject);
  });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

/* runs ONE tab forever unless browser closes */
async function runTab(browser, tabIndex, stopSignal) {
  while (!stopSignal.stop) {
    let context;
    try {
      context = await browser.newContext();
      const page = await context.newPage();

      console.log(`Tab ${tabIndex} opened`);

      page.on("domcontentloaded", async () => {
        try {
          await page.reload({ waitUntil: "domcontentloaded" });
        } catch {}
      });

      page.on("crash", () => {
        throw new Error("Page crashed");
      });

      await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });

      await new Promise((resolve, reject) => {
        page.on("close", resolve);
        page.on("crash", reject);
      });

    } catch (err) {
      if (!stopSignal.stop)
        console.log(`Tab ${tabIndex} restarting...`);
    } finally {
      try { await context?.close(); } catch {}
    }

    await sleep(1000);
  }
}

/* MAIN SUPERVISOR LOOP */
(async () => {
  let lastCreds = null;

  while (true) {
    const creds = await getCreds();
    const changed =
      !lastCreds ||
      creds.user !== lastCreds.user ||
      creds.pass !== lastCreds.pass;

    if (!changed) {
      await sleep(CHECK_INTERVAL);
      continue;
    }

    lastCreds = creds;
    console.log("Launching browser with new credentials:", creds.user);

    const browser = await chromium.launch({
      headless: false,
      proxy: {
        server: PROXY_SERVER,
        username: creds.user,
        password: creds.pass
      }
    });

    const stopSignal = { stop: false };

    /* start all tabs */
    const tabPromises = Array.from(
      { length: TABS },
      (_, i) => runTab(browser, i + 1, stopSignal)
    );

    /* credential watcher loop */
    while (true) {
      await sleep(CHECK_INTERVAL);
      const latest = await getCreds();

      if (
        latest.user !== lastCreds.user ||
        latest.pass !== lastCreds.pass
      ) {
        console.log("Credentials changed → restarting browser");
        lastCreds = latest;
        stopSignal.stop = true;

        try { await browser.close(); } catch {}
        break;
      }
    }

    /* wait tabs cleanup */
    await Promise.allSettled(tabPromises);
  }
})();
