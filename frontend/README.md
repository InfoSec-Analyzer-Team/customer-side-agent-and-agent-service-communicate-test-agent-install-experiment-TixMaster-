# Frontend placeholder

This folder is the preferred location for static frontend files (HTML/CSS/JS).

Migration instructions:
- Copy the following files from the repo root into this folder:
  - index.html
  - login.html
  - register.html
  - event-detail.html
  - admin-login.html, admin-dashboard.html (if used)
  - featureFlags.js (or move into `assets/`)
- After copying, start the backend and verify static content is served from `/`.
- Once verified, remove or archive the originals from the repo root.

Keep assets in `frontend/assets/` (JS/CSS/images).
