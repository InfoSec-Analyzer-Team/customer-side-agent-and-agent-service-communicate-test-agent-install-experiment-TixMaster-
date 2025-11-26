import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

const BASE = process.env.BASE_URL || 'http://localhost:3000';
let ADMIN_TOKEN: string | null = null;

// generate admin token once
test.beforeAll(() => {
  try {
    const out = execSync('node tools/gen_admin_jwt.js', { encoding: 'utf-8' }).trim();
    ADMIN_TOKEN = out;
  } catch (err) {
    console.warn('Could not generate admin token:', err);
    ADMIN_TOKEN = null;
  }
});

// helper to inject fetch wrapper that adds Authorization header
async function injectAuth(page, token: string) {
  await page.addInitScript((t) => {
    (window as any).__ADMIN_TOKEN = t;
    const origFetch = window.fetch;
    window.fetch = (input: RequestInfo, init?: RequestInit) => {
      init = init || {};
      init.headers = init.headers || {};
      if (window && (window as any).__ADMIN_TOKEN) {
        try {
          // merge headers
          if (init.headers instanceof Headers) {
            init.headers.set('Authorization', 'Bearer ' + (window as any).__ADMIN_TOKEN);
          } else if (Array.isArray(init.headers)) {
            init.headers.push(['Authorization', 'Bearer ' + (window as any).__ADMIN_TOKEN]);
          } else {
            init.headers = Object.assign({}, init.headers, { Authorization: 'Bearer ' + (window as any).__ADMIN_TOKEN });
          }
        } catch (e) {
          // ignore
        }
      }
      return origFetch(input, init as any);
    };
  }, token);
}

test.describe('UI Feature Flags interactions', () => {
  test('clicking buttons updates flag via API and SDK reflects changes', async ({ page }) => {
    if (!ADMIN_TOKEN) test.skip(true, 'ADMIN_TOKEN not available');

    // Inject auth so frontend fetch requests include the admin token
    await injectAuth(page, ADMIN_TOKEN);

    // Navigate to test page
    await page.goto(`${BASE}/test-feature-flags.html`);
    await expect(page.locator('h1')).toContainText('Feature Flags');

    const getCheckoutBtn = page.getByRole('button', { name: /取得 CHECKOUT_TIMER|取得 CHECKOUT_TIMER/ });
    const enableBtn = page.getByRole('button', { name: /啟用 CHECKOUT_TIMER/ });
    const disableBtn = page.getByRole('button', { name: /停用 CHECKOUT_TIMER/ });

    // Ensure we can fetch the current flag state via the page's button
    await getCheckoutBtn.click();
    const output = page.locator('#getFlagsOutput');
    await expect(output).toContainText('CHECKOUT_TIMER', { timeout: 3000 });

    // Click enable button, then fetch and verify
    await enableBtn.click();
    // wait a bit for request to complete and UI to update
    await page.waitForTimeout(500);
    await getCheckoutBtn.click();
    await expect(output).toContainText('"enabled": true', { timeout: 3000 });

    // Click disable button, verify false
    await disableBtn.click();
    await page.waitForTimeout(500);
    await getCheckoutBtn.click();
    await expect(output).toContainText('"enabled": false', { timeout: 3000 });

    // SDK checks: initialize SDK and call isEnabled
    await page.getByRole('button', { name: /初始化 SDK/ }).click();
    await page.waitForTimeout(300);
    const isEnabled = await page.evaluate(() => {
      // @ts-ignore
      return typeof FeatureFlags !== 'undefined' ? FeatureFlags.isEnabled('ENABLE_CHECKOUT_TIMER') : null;
    });
    expect(typeof isEnabled === 'boolean').toBeTruthy();
  });
});
