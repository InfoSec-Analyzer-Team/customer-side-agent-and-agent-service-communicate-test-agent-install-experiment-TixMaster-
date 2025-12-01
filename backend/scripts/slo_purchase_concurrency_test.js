/*
SLO Test: 100 concurrent purchase attempts, error rate must be <= 1%
- Prerequisites: backend running, real DB available (no SKIP_DB), DATABASE_URL set
- Flow:
  1) Discover a published event and one ticket via public APIs
  2) Create 100 users (unique emails) and login to get JWTs
  3) Fire 100 concurrent POST /api/orders (quantity=1)
  4) Compute error rate, write JSON & Markdown reports under backend/test-results
  5) Exit code 0 when errorRate <= 1%, otherwise exit 1
*/

const fs = require('fs');
const path = require('path');
const axios = require('axios');

const BASE_URL = process.env.BASE_URL || 'http://127.0.0.1:3000';
const CONCURRENCY = Number(process.env.CONCURRENCY || 100);
const PASSWORD = process.env.TEST_USER_PASSWORD || 'Test1234!';
const REPORT_DIR = path.join(__dirname, '..', 'test-results');

async function ensureReportDir() {
  try { fs.mkdirSync(REPORT_DIR, { recursive: true }); } catch {}
}

async function getEventAndTicket() {
  const ev = await axios.get(`${BASE_URL}/api/events`);
  const events = ev.data.events || [];
  if (!events.length) throw new Error('No published events found. Seed events first.');
  const eventId = events[0].id;
  const t = await axios.get(`${BASE_URL}/api/events/${eventId}/tickets`);
  const tickets = t.data.tickets || [];
  if (!tickets.length) throw new Error('No tickets found for event. Seed tickets first.');
  // Prefer ticket with availability
  let ticket = tickets.find(x => (x.available_quantity ?? 0) > 0) || tickets[0];
  return { eventId, ticketId: ticket.id };
}

function uniqueEmail(i, suffix = '') {
  const ts = Date.now();
  return `slo_user_${ts}_${i}${suffix}@example.com`;
}

async function registerUser(email, password) {
  try {
    await axios.post(`${BASE_URL}/api/users/register`, {
      email, password, name: email.split('@')[0], phone: ''
    });
  } catch (err) {
    // If duplicate, surface error; most likely we always use unique emails
    throw new Error(`register ${email} failed: ${err.response?.status} ${err.response?.data?.error || err.message}`);
  }
}

async function loginUser(email, password) {
  const res = await axios.post(`${BASE_URL}/api/users/login`, { email, password });
  return res.data.token;
}

async function createOrder(token, eventId, ticketId) {
  const headers = { Authorization: `Bearer ${token}` };
  return axios.post(`${BASE_URL}/api/orders`, {
    eventId, ticketId, quantity: 1, paymentMethod: 'credit_card'
  }, { headers });
}

function summarize(results) {
  const total = results.length;
  let success = 0;
  const errors = [];
  for (const r of results) {
    if (r.status === 'fulfilled') {
      const s = r.value?.status;
      if (s >= 200 && s < 300) success += 1; else errors.push({ code: s, detail: r.value?.data });
    } else {
      const e = r.reason;
      const code = e?.response?.status || 0;
      const detail = e?.response?.data || e?.message;
      errors.push({ code, detail });
    }
  }
  const errorCount = total - success;
  const errorRate = total === 0 ? 0 : errorCount / total;
  return { total, success, errorCount, errorRate, errors };
}

function writeReports(summary, meta) {
  const time = new Date().toISOString().replace(/[:.]/g, '-');
  const jsonPath = path.join(REPORT_DIR, `slo_purchase_${time}.json`);
  const mdPath = path.join(REPORT_DIR, `slo_purchase_${time}.md`);
  const status = summary.errorRate <= 0.01 ? 'Passed' : 'Failed';

  const json = {
    type: 'SLO_CONCURRENCY_PURCHASE',
    status,
    threshold: 'errorRate <= 1%',
    summary,
    meta
  };
  fs.writeFileSync(jsonPath, JSON.stringify(json, null, 2));

  const md = [
    `# SLO Test — Concurrent Purchase (${status})`,
    `- Threshold: errorRate <= 1%`,
    `- Total: ${summary.total}`,
    `- Success: ${summary.success}`,
    `- Errors: ${summary.errorCount}`,
    `- Error Rate: ${(summary.errorRate * 100).toFixed(2)}%`,
    '',
    '## Meta',
    `- Base URL: ${meta.baseUrl}`,
    `- Concurrency: ${meta.concurrency}`,
    `- Event ID: ${meta.eventId}`,
    `- Ticket ID: ${meta.ticketId}`,
    '',
    '## Sample Errors (up to 10)',
    ...summary.errors.slice(0, 10).map((e, i) => `- [${i+1}] code=${e.code} detail=${typeof e.detail === 'string' ? e.detail : JSON.stringify(e.detail)}`)
  ].join('\n');
  fs.writeFileSync(mdPath, md);
  return { jsonPath, mdPath, status };
}

async function main() {
  if (process.env.SKIP_DB === 'true' || !process.env.DATABASE_URL) {
    console.error('[SLO] Real DB required. Set DATABASE_URL and ensure SKIP_DB != true.');
    process.exit(2);
  }

  await ensureReportDir();
  console.log(`[SLO] Base URL: ${BASE_URL}`);
  console.log(`[SLO] Concurrency: ${CONCURRENCY}`);

  // 1) Discover event & ticket
  const { eventId, ticketId } = await getEventAndTicket();
  console.log(`[SLO] Using event ${eventId}, ticket ${ticketId}`);

  // 2) Create users & login
  console.log(`[SLO] Creating & logging in ${CONCURRENCY} users...`);
  const emails = Array.from({ length: CONCURRENCY }, (_, i) => uniqueEmail(i));
  await Promise.all(emails.map((email) => registerUser(email, PASSWORD)));
  const tokens = await Promise.all(emails.map((email) => loginUser(email, PASSWORD)));

  // 3) Fire concurrent purchase requests
  console.log('[SLO] Sending concurrent orders...');
  const tasks = tokens.map((tok) => createOrder(tok, eventId, ticketId));
  const results = await Promise.allSettled(tasks);

  // 4) Summarize and write reports
  const summary = summarize(results);
  const meta = { baseUrl: BASE_URL, concurrency: CONCURRENCY, eventId, ticketId };
  const { jsonPath, mdPath, status } = writeReports(summary, meta);

  console.log(`[SLO] Report JSON: ${jsonPath}`);
  console.log(`[SLO] Report MD:   ${mdPath}`);
  console.log(`[SLO] Status: ${status} (errorRate=${(summary.errorRate * 100).toFixed(2)}%)`);

  // 5) Exit code based on SLO
  process.exit(summary.errorRate <= 0.01 ? 0 : 1);
}

main().catch((err) => {
  console.error('[SLO] Unexpected error:', err.message);
  process.exit(2);
});
