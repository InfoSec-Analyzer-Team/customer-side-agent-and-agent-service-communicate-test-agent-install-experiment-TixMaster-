import { test, expect } from '@playwright/test';

const BASE = process.env.BASE_URL || 'http://localhost:3000';

test('health page loads and shows OK', async ({ page }) => {
  const res = await page.request.get(`${BASE}/health`);
  expect(res.status()).toBe(200);
  const j = await res.json();
  expect(j.status.toUpperCase()).toBe('OK');
});

// Example: navigate to the feature flags page (if front-end served)
test('feature flags page loads', async ({ page }) => {
  await page.goto(`${BASE}/test-feature-flags.html`);
  await expect(page.locator('h1')).toContainText('Feature Flags');
});
