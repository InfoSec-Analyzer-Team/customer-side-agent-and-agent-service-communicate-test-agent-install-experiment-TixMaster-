import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';

const BASE = process.env.BASE_URL || 'http://localhost:3000';

function extractFlag(obj: any) {
  if (!obj) return undefined;
  if (typeof obj === 'object' && 'flag' in obj) return obj.flag;
  return obj;
}

let ADMIN_TOKEN: string | null = null;

test.beforeAll(() => {
  try {
    const out = execSync('node tools/gen_admin_jwt.js', { encoding: 'utf-8' }).trim();
    ADMIN_TOKEN = out;
  } catch (err) {
    console.warn('Could not generate admin token:', err);
    ADMIN_TOKEN = null;
  }
});

test.describe('Feature Flags API (E2E)', () => {
  test('admin can toggle ENABLE_CHECKOUT_TIMER on/off/on', async ({ request }) => {
    if (!ADMIN_TOKEN) test.skip(true, 'ADMIN_TOKEN not available');
    const headers = { Authorization: `Bearer ${ADMIN_TOKEN}` };
    const flagKey = 'ENABLE_CHECKOUT_TIMER';

    // set true
    let r = await request.put(`${BASE}/api/feature-flags/${flagKey}`, {
      data: { enabled: true },
      headers
    });
    expect(r.status()).toBe(200);

    r = await request.get(`${BASE}/api/feature-flags/${flagKey}`);
    expect(r.status()).toBe(200);
    let j = await r.json();
    let flag = extractFlag(j);
    expect(flag).toBeTruthy();
    expect(flag.enabled).toBe(true);

    // set false
    r = await request.put(`${BASE}/api/feature-flags/${flagKey}`, {
      data: { enabled: false },
      headers
    });
    expect(r.status()).toBe(200);

    r = await request.get(`${BASE}/api/feature-flags/${flagKey}`);
    expect(r.status()).toBe(200);
    j = await r.json();
    flag = extractFlag(j);
    expect(flag.enabled).toBe(false);

    // set true again
    r = await request.put(`${BASE}/api/feature-flags/${flagKey}`, {
      data: { enabled: true },
      headers
    });
    expect(r.status()).toBe(200);

    r = await request.get(`${BASE}/api/feature-flags/${flagKey}`);
    expect(r.status()).toBe(200);
    j = await r.json();
    flag = extractFlag(j);
    expect(flag.enabled).toBe(true);
  });

  test('unauthenticated cannot modify flag', async ({ request }) => {
    const flagKey = 'ENABLE_CHECKOUT_TIMER';
    const r = await request.put(`${BASE}/api/feature-flags/${flagKey}`, { data: { enabled: false } });
    expect([401, 403, 404]).toContain(r.status());
  });

  test('admin invalid payload returns 4xx', async ({ request }) => {
    if (!ADMIN_TOKEN) test.skip(true, 'ADMIN_TOKEN not available');
    const headers = { Authorization: `Bearer ${ADMIN_TOKEN}` };
    const flagKey = 'ENABLE_CHECKOUT_TIMER';

    const r = await request.put(`${BASE}/api/feature-flags/${flagKey}`, { data: {}, headers });
    // Accept 400 for validation, or 401/403 if permission problem
    expect((r.status() >= 400 && r.status() < 500) || r.status() === 401 || r.status() === 403).toBeTruthy();
  });
});
