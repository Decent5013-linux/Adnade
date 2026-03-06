import { chromium } from "playwright";
import { execSync } from "child_process";
import fs from "fs";

const PATTERN_FILE = "used_patterns.txt";

function generateDotEmail() {
  const base = "decencyawowo2021";
  const gaps = base.length - 1; // 15 gaps

  // load used patterns
  let used = new Set();
  if (fs.existsSync(PATTERN_FILE)) {
    const lines = fs.readFileSync(PATTERN_FILE, "utf8").split("\n").filter(Boolean);
    used = new Set(lines);
  }

  let pattern;
  let selected;

  while (true) {
    const dotCount = Math.floor(Math.random() * (15 - 3 + 1)) + 3;

    const gapIndexes = [...Array(gaps).keys()];

    for (let i = gapIndexes.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [gapIndexes[i], gapIndexes[j]] = [gapIndexes[j], gapIndexes[i]];
    }

    selected = gapIndexes.slice(0, dotCount).sort((a, b) => a - b);

    pattern = selected.join(",");

    if (!used.has(pattern)) {
      fs.appendFileSync(PATTERN_FILE, pattern + "\n");
      break;
    }
  }

  let result = "";

  for (let i = 0; i < base.length; i++) {
    result += base[i];

    if (selected.includes(i)) {
      result += ".";
    }
  }

  return result + "@gmail.com";
}

async function runTask() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto("https://dashboard.aluvia.io/login", {
      waitUntil: "domcontentloaded",
    });

    const emailSelector = 'input[placeholder="Enter your email"]';
    await page.waitForSelector(emailSelector);

    const email = generateDotEmail();
    console.log("Email:", email);

    await page.fill(emailSelector, email);
    await page.getByRole("button", { name: "Get Login Code" }).click();

    await page.waitForSelector(
      'input[aria-label="Verification code digit 1 of 6"]',
      { timeout: 0 }
    );

    console.log("Waiting for OTP...");

    let code = null;

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

    for (let i = 0; i < 6; i++) {
      await page.fill(
        `input[aria-label="Verification code digit ${i + 1} of 6"]`,
        code[i]
      );
    }

    await page.getByRole("button", { name: "Verify" }).click();

    const connectionsLink = page
      .locator('a[href="/connections"].flex')
      .first();

    await connectionsLink.waitFor({ timeout: 0 });
    await connectionsLink.click();

    await page.waitForSelector("td span.font-mono", { timeout: 60000 });

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

async function startLoop() {
  while (true) {
    console.log("=== Running task ===", new Date().toLocaleString());
    await runTask();
    console.log("=== Waiting 1 hour ===");
    await new Promise((r) => setTimeout(r, 3600000));
  }
}

startLoop();
