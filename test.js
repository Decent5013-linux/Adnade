import { chromium } from "playwright";
import https from "https";

const TARGET_URL = "https://bot.vpsmail.name.ng";
const TABS = 30;
const PROXY_SERVER = "http://gateway.aluvia.io:8080";
const CREDS_URL = "https://bot.vpsmail.name.ng/secret.txt";

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

(async () => {
  const { user, pass } = await getCreds();

  const browser = await chromium.launch({
    headless: false,
    proxy: {
      server: PROXY_SERVER,
      username: user,
      password: pass
    }
  });

  /* runs ONE tab forever — auto restarts if it crashes */
  async function runTab(tabIndex) {
    while (true) {
      let context;
      try {
        context = await browser.newContext();
        const page = await context.newPage();

        page.on("domcontentloaded", async () => {
          try {
            await page.reload({ waitUntil: "domcontentloaded" });
          } catch {}
        });

        page.on("crash", () => {
          throw new Error("Page crashed");
        });

        await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });

        /* keep tab alive until crash */
        await new Promise((resolve, reject) => {
          page.on("close", resolve);
          page.on("crash", reject);
        });

      } catch (err) {
        console.log(`Tab ${tabIndex} restarting...`);
      } finally {
        try { await context?.close(); } catch {}
      }

      /* small delay before relaunch so it doesn't loop instantly */
      await new Promise(r => setTimeout(r, 1000));
    }
  }

  /* launch all tabs concurrently */
  await Promise.all(
    Array.from({ length: TABS }, (_, i) => runTab(i))
  );
})();
