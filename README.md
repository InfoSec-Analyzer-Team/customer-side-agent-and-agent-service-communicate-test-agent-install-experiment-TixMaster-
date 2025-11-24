# 🎫 TixMaster - Secure Ticket Sales System

> **Course:** Assignment 11 — Team-Based DevSecOps Feature Experimentation
> **Team:** Tame

## 📖 Project Overview

**TixMaster** 是一個結合 **DevSecOps** 流程與 **HDD (Hypothesis-Driven Development)** 方法論的安全售票系統模擬平台。

本專案的核心目標不在於傳統的功能開發，而在於建立一套安全的開發維運流程，並透過 **Feature Toggling (功能開關)** 技術，在不重新部署的情況下進行商業假設驗證 (A/B Testing)。我們致力於解決高併發售票場景下的使用者體驗問題，同時確保嚴格的身份驗證與資料安全。

---

## 👥 Team & Responsibilities (Role Allocation)

| Role | Member Name | Core Responsibilities |
| :--- | :--- | :--- |
| **Project Manager** | **YeMiao1026** | • 定義商業假設 (HDD) 與驗證指標<br>• 專案進度管理 (Jira/Timeline)<br>• 安全治理策略制定 (Governance)<br>• 實驗數據分析與報告撰寫 |
| **Full-Stack Developer** | yuchen | • 前端介面開發 (React/Vue) 與 UI 設計<br>• 實作 Feature Toggles 邏輯<br>• 整合 OAuth 2.0 身份驗證<br>• API 開發與單元測試 |
| **DB Manager / Ops** | EnSai | • 資料庫架構設計與雲端託管<br>• **Secret Management** (GitHub Secrets / .env)<br>• **SCA** 軟體成分分析工具設定 (Dependabot)<br>• CI/CD 流水線與自動化部署 |
| **Tester** | Isforuse | • 撰寫測試矩陣 (Test Matrix)<br>• 執行 Feature Toggle 開關切換測試<br>• 安全性測試 (Security Testing)<br>• 迴歸測試與品質保證 |

---

## 🧪 HDD & Feature Experiments

本專案基於兩個核心商業假設進行開發，並透過 Feature Toggles 進行驗證：

### Hypothesis 1: Urgency Tactic (急迫感設計)
* **Hypothesis:** 若在結帳頁面加入「倒數計時器」，將能製造稀缺感，進而提升用戶的結帳完成率。
* **Metric:** Payment Completion Rate (付款完成率)。
* **Toggle Key:** `ENABLE_CHECKOUT_TIMER`

### Hypothesis 2: Social Proof (社交證明)
* **Hypothesis:** 若在活動頁顯示「當前瀏覽人數」，利用從眾心理 (FOMO)，將能提升購票按鈕的點擊率。
* **Metric:** "Buy Now" Click-Through Rate (CTR)。
* **Toggle Key:** `ENABLE_VIEWING_COUNT`

---

## 🛡️ Security Implementation (DevSecOps)

我們在開發生命週期中整合了以下安全措施：

1.  **Authentication & Authorization (A&A)**
    * 採用 **Auth0 / Firebase Auth** 進行 OAuth 2.0 身份驗證。
    * JWT Token 驗證機制，確保 API 存取安全。

2.  **Software Composition Analysis (SCA)**
    * 啟用 **GitHub Dependabot** 自動掃描相依套件漏洞。
    * 定期審查 `npm audit` 報告並修補高風險漏洞。

3.  **Secret Management**
    * **Development:** 使用 `.env` 檔案管理環境變數，並透過 `.gitignore` 排除。
    * **Production:** 使用 **GitHub Actions Secrets** 注入敏感資訊 (DB Connection, API Keys)，嚴禁明文寫入程式碼。

---

## 🛠️ Tech Stack & Architecture

* **Frontend:** React.js / Next.js (Web Application)
* **Backend:** Node.js (Express) / Python (FastAPI)
* **Database:** PostgreSQL / MongoDB (Cloud Hosted)
* **Auth:** Auth0 / Firebase Authentication
* **DevOps Tools:** GitHub Actions (CI/CD), Dependabot (SCA), Vercel/Render (Deployment)

### 📂 Project Structure

```text
TixMaster/
├── .github/
│   ├── workflows/      # CI/CD Pipelines
│   └── dependabot.yml  # SCA Configuration
├── src/
│   ├── components/     # UI Components (Login, Timer, TicketCard)
│   ├── config/         # Feature Flags / Toggles logic
│   ├── pages/          # Application Pages
│   └── utils/          # Auth & Helper functions
├── tests/              # Unit & Integration Tests
├── .env.example        # Template for environment variables (No Secrets!)
├── .gitignore          # Security rule: Ignore .env and node_modules
├── package.json        # Dependencies
└── README.md           # Project Documentation