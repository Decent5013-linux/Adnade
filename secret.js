import { chromium } from "playwright";
import { execSync } from "child_process";
import fs from "fs";

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

    // generate gmail with random dots
    function generateDotEmail() {
      const base = "decencyawowo2021";
      let result = "";

      for (let i = 0; i < base.length; i++) {
        result += base[i];

        if (i !== base.length - 1) {
          const dotCount = Math.floor(Math.random() * 5) + 1; // 1–5 dots
          result += ".".repeat(dotCount);
        }
      }

      return result + "@gmail.com";
    }

    const email = generateDotEmail();
    console.log("Email:", email);

    await page.fill(emailSelector, email);
    await page.getByRole("button", { name: "Get Login Code" }).click();

    // WAIT OTP INPUTS
    await page.waitForSelector(
      'input[aria-label="Verification code digit 1 of 6"]',
      { timeout: 0 }
    );

    console.log("Waiting for OTP...");

    let code = null;

    // keep running gmail.js until OTP is found
    while (!code) {
      try {
        const result = execSync(`node gmail.js -f ${email}`)
          .toString()
          .trim();

        const match = result.match(/\b\d{6}\b/);
        if (match) {
          code = match[0];
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

    // Wait for the connections link
    const connectionsLink = page
      .locator('a[href="/connections"].flex')
      .first();
    await connectionsLink.waitFor({ timeout: 0 });
    await connectionsLink.click();

    // wait until the actual codes are rendered
    await page.waitForSelector("td span.font-mono", { timeout: 60000 });

    // extract practice + test values
    const data = await page.evaluate(() => {
      const spans = document.querySelectorAll("td span.font-mono");
      if (spans.length < 2) return null;
      return [
        spans[0].textContent.trim(),
        spans[1].textContent.trim(),
      ];
    });

    if (!data) {
      console.log("No data found");
    } else {
      console.log("Extracted:", data);

      const url = `https://ff.vpsmail.name.ng/secret.php?${encodeURIComponent(
        data[0]
      )}&${encodeURIComponent(data[1])}`;

      try {
        const response = execSync(`curl -s "${url}"`)
          .toString()
          .trim();
        console.log("Sent to secret.php");
        console.log("Server response:", response);
      } catch (err) {
        console.error("Failed to send request:", err);
      }
    }
  } catch (err) {
    console.error("Error during task:", err);
  } finally {
    await browser.close();
  }
}

// run immediately, then every 1 hour
async function startLoop() {
  while (true) {
    console.log("=== Running task ===", new Date().toLocaleString());
    await runTask();
    console.log("=== Waiting 1 hour ===");
    await new Promise((r) => setTimeout(r, 3600000));
  }
}

startLoop();
