# Toggle Test Plan

目的
- 定義針對 Feature Flags（功能開關）的完整測試計畫，包含功能性、回歸與安全測試，用以確保開關在不同角色與情境下行為正確。

範圍
- 針對 API endpoints:
  - `GET /api/feature-flags` (list)
  - `GET /api/feature-flags/{flag_key}` (single)
  - `PUT /api/feature-flags/{flag_key}` (update)
- 目前 repo 中已存在 flag（schema 預設）：
  - `ENABLE_CHECKOUT_TIMER`
  - `ENABLE_VIEWING_COUNT`

角色（Roles）
- `admin` — 可管理 feature flags
- `organizer` — 可能有部分管理權限（視 RBAC 設定）
- `user` — 一般使用者
- `unauthenticated` — 未登入

測試矩陣（概要）
- 標準欄位：Flag × Role × Action × Input × 預期結果 × 優先度

| Flag | Role | Action | Input / Condition | Expected Outcome | Priority |
|---|---:|---|---|---|---:|
| ENABLE_CHECKOUT_TIMER | admin | GET list | N/A | 200, 包含 flags dict | High |
| ENABLE_CHECKOUT_TIMER | admin | GET single | flag exists | 200, `enabled` present (bool) | High |
| ENABLE_CHECKOUT_TIMER | admin | PUT enable true | JSON {enabled: true} | 200, GET 後 `enabled` == true | High |
| ENABLE_CHECKOUT_TIMER | admin | PUT enable false | JSON {enabled: false} | 200, GET 後 `enabled` == false | High |
| ENABLE_CHECKOUT_TIMER | unauthenticated | PUT | JSON {enabled:true} | 401/403 (or 200 only if API allows) — 預期非 200 | High |
| ENABLE_CHECKOUT_TIMER | admin | PUT invalid payload | missing/incorrect `enabled` | 400 (或 4xx) | Medium |
| ENABLE_VIEWING_COUNT | admin | concurrent PUTs | high concurrency on/off | no 5xx errors; eventually stable state | Medium |

（此矩陣可擴充為 CSV 或由 API 動態產生所有 flag 再自動組合）

具體測試案例（Test Cases）
- TC-001: Health & Connectivity
  - Steps: `GET /health` => expect 200 and `status: OK`
  - Evidence: response body + timestamp
- TC-002: List Flags
  - Steps: `GET /api/feature-flags` => expect 200 and `flags` object
- TC-003: Read Single Flag (existing)
  - Steps: `GET /api/feature-flags/ENABLE_CHECKOUT_TIMER` => expect 200 and `enabled` present
- TC-004: Toggle Flow (admin)
  - Steps:
    1. Ensure admin token present
    2. PUT enable true
    3. GET single -> verify `enabled`==true
    4. PUT enable false
    5. GET single -> verify `enabled`==false
    6. PUT enable true
    7. GET single -> verify `enabled`==true
  - Expected: each PUT returns 200; intermediate GETs reflect state
- TC-005: Non-admin attempt
  - Steps: unauthenticated or user token -> PUT -> expect 401/403 (or 404 if resource hidden)
- TC-006: Invalid payloads
  - Inputs: `{}`, `{