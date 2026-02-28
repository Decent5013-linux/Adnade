import { chromium } from "playwright";                                 import { execSync } from "child_process";                              import fs from "fs";
                                                                       async function runTask() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
                                                                         try {
    // LOGIN PAGE
    await page.goto("https://dashboard.aluvia.io/login", {
      waitUntil: "domcontentloaded",
    });

    const emailSelector = 'input[placeholder="Enter your email"]';
    await page.waitForSelector(emailSelector);
                                                                           // create webhook uuid
    const uuid = execSync(
      `curl -s -X POST https://webhook.site/token | grep -o '"uuid":"[^"]*"' | cut -d'"' -f4`                                                     ).toString().trim();

    const email = `${uuid}@emailhook.site`;
    console.log("Email:", email);

    await page.fill(emailSelector, email);
    await page.getByRole("button", { name: "Get Login Code" }).click();
                                                                           // WAIT OTP INPUTS
    await page.waitForSelector(
  'input[aria-label="Verification code digit 1 of 6"]',                  { timeout: 0 }
);                                                                         console.log("Waiting for OTP...");

    let code = null;                                                   
    // poll webhook until OTP arrives
    while (!code) {
      try {
        const result = execSync(                                                 `curl -s https://webhook.site/token/${uuid}/requests | jq -r '.data[0].text_content' | grep -o '[0-9]\\{6\\}'`
        )
          .toString()
          .trim();

        if (result && result.length === 6) {
          code = result;
          break;
        }
      } catch {}

      await new Promise((r) => setTimeout(r, 3000));
    }

    console.log("OTP:", code);

    // fill OTP digits
    for (let i = 0; i < 6; i++) {
      await page.fill(
        `input[aria-label="Verification code digit ${i + 1} of 6"]`,
        code[i]
      );
    }

    // click verify
    await page.getByRole("button", { name: "Verify" }).click();

    // Wait for the connections link to be available (no timeout)
    const connectionsLink = page.locator('a[href="/connections"].flex').first();
    await connectionsLink.waitFor({ timeout: 0 });
    await connectionsLink.click();

    // wait until the actual codes are rendered
    await page.waitForSelector("td span.font-mono", { timeout: 60000 });

    // extract practice + test values
    const data = await page.evaluate(() => {
      const spans = document.querySelectorAll("td span.font-mono");
      if (spans.length < 2) return null;
      return [spans[0].textContent.trim(), spans[1].textContent.trim()];
    });

    if (!data) {                                                             console.log("No data found");
    } else {                                                                 console.log("Extracted:", data);
      // save raw values to secret.txt                                       fs.writeFileSync("secret.txt", `${data[0]}\n${data[1]}`);              console.log("Saved to secret.txt");
    }                                                                    } catch (err) {
    console.error("Error during task:", err);
  } finally {
    await browser.close();
  }                                                                    }

// run immediately, then every 1 hour
async function startLoop() {
  while (true) {                                                           console.log("=== Running task ===", new Date().toLocaleString());
    await runTask();
    console.log("=== Waiting 1 hour ===");                                 await new Promise((r) => setTimeout(r, 3600000)); // 1 hour
  }
}

startLoop();
