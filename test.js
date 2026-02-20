import { chromium } from "playwright";
import https from "https";

const TARGET_URL = "https://bot.vpsmail.name.ng";
const TABS = 30;
const PROXY_SERVER = "http://gateway.aluvia.io:8080";
const CREDS_URL = "https://bot.vpsmail.name.ng/secret.txt";

/* fetch username + password */
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
    headless: true,
    proxy: {
      server: PROXY_SERVER,
      username: user,
      password: pass
    }
  });

  const context = await browser.newContext();

  async function createTab(i) {
    const page = await context.newPage();

    page.on("domcontentloaded", async () => {
      try {
        await page.reload({ waitUntil: "domcontentloaded" });
      } catch {}
    });

    await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });
  }

  await Promise.all(
    Array.from({ length: TABS }, (_, i) => createTab(i))
  );
})();
