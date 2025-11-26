# ⚠️ 重要：Google OAuth 憑證設定指南

## 📝 請填入你的 Google OAuth 憑證

請將以下內容複製到 `backend/.env` 檔案中，並填入你的憑證：

```env
# === 現有設定（保留）===
DATABASE_URL=Exteral PostgreSQL database URL
JWT_SECRET=tixmaster-super-secret-key-change-in-production-2024
PORT=3000

# === 新增：Google OAuth 憑證 ===
GOOGLE_CLIENT_ID=你的CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_CALLBACK_URL=http://localhost:3000/auth/google/callback
```

## 🔍 如何取得憑證？

已經有憑證的話直接填入即可。

### 憑證範例格式：

```
GOOGLE_CLIENT_ID=123456789012-abc123def456ghi789jkl.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-1A2b3C4d5E6f7G8h9I0j
```

## ⚙️ Google Console 設定檢查

確保你在 Google Cloud Console 的設定中包含以下重新導向 URI：

```
http://localhost:3000/auth/google/callback
```

## 🚨 安全提醒

- ❌ 絕對不要將 `.env` commit 到 Git
- ✅ `.env` 已經在 `.gitignore` 中
- ✅ `GOOGLE_CLIENT_SECRET` 是機密資訊，絕不能分享或公開

## 📋 更新步驟

1. 打開 `backend/.env` 檔案
2. 在現有內容後面加入上面的 Google OAuth 設定
3. 填入你的 `GOOGLE_CLIENT_ID` 和 `GOOGLE_CLIENT_SECRET`
4. 儲存檔案
5. 重新啟動伺服器（如果正在運行）

完成後就可以開始測試 Google OAuth 登入了！🎉
