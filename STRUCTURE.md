# Project Structure and Migration Plan

This document describes a recommended, orderly structure for the TixMaster repository and step-by-step migration actions that are low-risk and non-destructive.

## Goal
- Separate frontend static assets from backend code.
- Make server static serving deterministic (prefer `frontend/`).
- Avoid committing build artifacts and node_modules.
- Provide a clear migration checklist for moving files later.

## Recommended Layout

TixMaster/
├── frontend/                 # Static site (HTML/CSS/JS). New canonical location for static assets
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── event-detail.html
│   └── assets/               # JS/CSS/images
├── backend/                  # Node/Express API and server
│   ├── server.js
│   ├── routes/
│   ├── config/
│   └── ...
├── test/                     # Pytest + Playwright tests (recommended canonical folder)
├── admin/                    # Admin-specific static UI (optional separate folder)
├── docs/                     # Documentation, guides
├── STRUCTURE.md
└── README.md

## Non-destructive migration plan (suggested)
1. Add `frontend/` directory and update server to prefer it (already done).
2. Update `.gitignore` to exclude build artifacts and node_modules (already done).
3. Copy (not delete) static files from repo root into `frontend/` and verify server still serves them.
4. Update any internal references (if necessary) to use relative paths inside `frontend/`.
5. After verification, move originals into `archive/legacy-static/` or delete once safe.
6. Consider splitting repository into two (monorepo vs separate repos) if backend and frontend will be evolved independently.

## Next actionable steps (low risk)
- Create `frontend/` and copy key HTML/asset files.
- Run local server and test `http://localhost:3000` to ensure static content served.
- Once confirmed, remove legacy static files from repo or move to archive.
- Replace express-session MemoryStore with a persistent store (connect-pg-simple) for production readiness.

## Notes
- This change is intentionally non-destructive—static files remain at their original locations until you confirm the migration.
- If you prefer I can perform the copy/move operations for you in a dedicated branch and test locally.
