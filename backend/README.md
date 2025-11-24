# TixMaster Backend API

TixMaster 票務系統後端 API 服務器

## 快速開始

### 1. 安裝依賴

```bash
cd backend
npm install
```

### 2. 環境設定

複製 `.env.example` 為 `.env`（已設定完成）

### 3. 啟動伺服器

```bash
npm start
```

伺服器將在 `http://localhost:3000` 啟動

## API 端點

### Health Check

```bash
GET http://localhost:3000/health
```

### 使用者 API

- `POST /api/users/register` - 註冊
- `POST /api/users/login` - 登入
- `GET /api/users/profile` - 取得個人資料（需認證）
- `PUT /api/users/profile` - 更新個人資料（需認證）
- `POST /api/users/change-password` - 修改密碼（需認證）

### 活動 API

- `GET /api/events` - 取得所有活動
- `GET /api/events/:id` - 取得活動詳情
- `GET /api/events/:id/tickets` - 取得活動票種

### 訂單 API

- `POST /api/orders` - 建立訂單（需認證）
- `GET /api/orders/:orderNumber` - 取得訂單
- `GET /api/orders/user/me` - 取得我的訂單（需認證）
- `PUT /api/orders/:orderNumber/payment` - 更新付款狀態

### 功能開關 API

- `GET /api/feature-flags` - 取得所有功能開關
- `GET /api/feature-flags/:key` - 取得單一功能開關
- `PUT /api/feature-flags/:key` - 更新功能開關

### 數據分析 API

- `POST /api/analytics/event` - 記錄事件
- `GET /api/analytics/events` - 取得事件記錄

## 認證

需要認證的端點請在 Header 加入：

```
Authorization: Bearer <your-jwt-token>
```

## 測試範例

### 註冊使用者

```bash
curl -X POST http://localhost:3000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User","phone":"0912345678"}'
```

### 登入

```bash
curl -X POST http://localhost:3000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 取得功能開關

```bash
curl http://localhost:3000/api/feature-flags
```

## 技術棧

- Node.js + Express
- PostgreSQL (Render.com)
- JWT Authentication
- bcrypt 密碼加密

## 開發工具

建議使用 **nodemon** 進行開發：

```bash
npm install -g nodemon
nodemon server.js
```

## 注意事項

⚠️ `.env` 檔案包含敏感資訊，已加入 `.gitignore`，請勿 commit 到 GitHub
