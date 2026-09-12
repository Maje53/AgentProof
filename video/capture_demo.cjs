const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const output = path.resolve(__dirname, "assets");
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1600, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: "dark",
  });
  const page = await context.newPage();
  await page.goto("https://agent-proof-coral.vercel.app", { waitUntil: "networkidle" });
  await page.screenshot({ path: path.join(output, "brief.png") });

  await page.click('[data-tab="evidence"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(output, "evidence.png") });

  await page.click('[data-tab="brief"]');
  await page.click("#evaluateButton");
  await page.waitForSelector("#verdictResult:not([hidden])");
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(output, "verdict.png") });

  await page.click("#settleButton");
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(output, "settled.png") });
  await browser.close();
  console.log(`Captured four demo states in ${output}`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
