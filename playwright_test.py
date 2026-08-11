from pathlib import Path
from playwright.sync_api import sync_playwright
import random
import time

BASE = "http://localhost:8080"   # nginx (docker-compose.nginx.yml 對外埠 8080) -> backend :3000
SESSION_COUNT = 50                # 要累積幾個使用者 session

UA_POOL = [                       # 共用 UA 池,瀏覽器 session 跟 API request context 都吃這份,避免 Playwright 預設 UA 洩漏
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X) Safari/17",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17) Mobile Safari",
]

ACCOUNTS_FILE = Path(__file__).parent / "accounts.txt"

def load_accounts():
    """從 accounts.txt 讀 5 組固定帳密(name,email,password),檔案不存在就先建立預設值"""
    if not ACCOUNTS_FILE.exists():
        ACCOUNTS_FILE.write_text(
            "測試員一,tester1@example.com,Passw0rd!1\n"
            "測試員二,tester2@example.com,Passw0rd!2\n"
            "測試員三,tester3@example.com,Passw0rd!3\n"
            "測試員四,tester4@example.com,Passw0rd!4\n"
            "測試員五,tester5@example.com,Passw0rd!5\n",
            encoding="utf-8",
        )
    accounts = []
    for line in ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, email, password = line.split(",")
        accounts.append({"name": name, "email": email, "password": password})
    return accounts

ACCOUNTS = load_accounts()

def human_delay():
    """模擬真人思考/閱讀的隨機停頓——關鍵!避免機器規律偽特徵"""
    time.sleep(random.uniform(0.5, 4.0))

def one_user_session(page):
    """一個使用者的一次瀏覽 session,隨機走 TixMaster 實際存在的動線"""
    # 1. 進首頁(events 是前端寫死的資料,不支援 ?cat=/?s= 這類查詢字串)
    page.goto(f"{BASE}/index.html")
    human_delay()

    # 2. 隨機決定這個使用者做什麼(用權重模擬真實比例)
    # register 暫時關閉(先把登入測好),要恢復把它加回 choices/weights 即可
    action = random.choices(
        ["browse_event", "login_email", "login_auth0_click", "guest_checkout"],
        weights=[50, 25, 10, 15]   # 50%看活動 25%email登入 10%點Auth0 15%訪客結帳
    )[0]

    if action == "browse_event":
        # 首頁卡片是 <button onclick="location.href=...">,不是 <a>
        buttons = page.query_selector_all(".card button.btn")
        if buttons:
            random.choice(buttons).click()
            human_delay()           # 停下來「閱讀」活動詳情
            # 有機會調整購票數量(真實存在的 +/- 按鈕)
            plus_btn = page.query_selector(".quantity-btn:last-of-type")
            if plus_btn and random.random() < 0.5:
                for _ in range(random.randint(1, 3)):
                    try:
                        plus_btn.click()
                        human_delay()
                    except Exception:
                        break
            page.go_back()           # 回首頁(產生真實 referer)
            human_delay()

    elif action == "register":
        # 用 accounts.txt 裡固定的 5 組帳號註冊(已註冊過會回 400,屬預期行為,略過即可)
        account = random.choice(ACCOUNTS)
        page.goto(f"{BASE}/register.html")
        human_delay()
        page.fill("#name", account["name"])
        page.fill("#email", account["email"])
        page.fill("#password", account["password"])
        page.fill("#confirmPassword", account["password"])
        human_delay()
        try:
            page.click("#registerBtn")   # 會實際打 /api/users/register + /api/users/login,寫入 Postgres
            page.wait_for_timeout(1500)
        except Exception:
            pass

    elif action == "login_email":
        # 用固定帳號直接呼叫真實的 /api/users/login(login.html 本身沒有 email/password 表單)
        account = random.choice(ACCOUNTS)
        try:
            resp = page.request.post(
                f"{BASE}/api/users/login",
                data={"email": account["email"], "password": account["password"]},
            )
            if resp.ok:
                body = resp.json()
                token = body.get("token")
                user = body.get("user")
                if token and user:
                    # index.html 是看 localStorage 的 currentUser 才會顯示已登入狀態,只存 token 不夠
                    page.evaluate(
                        "([t, u]) => { localStorage.setItem('token', t); "
                        "localStorage.setItem('currentUser', JSON.stringify({...u, token: t})); }",
                        [token, user],
                    )
                    page.goto(f"{BASE}/index.html")   # 重新整理讓畫面反映已登入狀態
                    human_delay()
            else:
                print(f"[login_email] {account['email']} 登入失敗: {resp.status} {resp.text()}")
        except Exception as e:
            print(f"[login_email] {account['email']} 例外: {e}")

    elif action == "login_auth0_click":
        page.goto(f"{BASE}/login.html")
        human_delay()
        try:
            # 會導向 /auth/login -> Auth0(外部網域),不等它完成登入
            page.click("#loginBtn", timeout=3000)
            page.wait_for_timeout(1500)
        except Exception:
            pass

    elif action == "guest_checkout":
        # 未登入狀態直接進結帳頁,前端應會導去 login-required.html
        event_id = random.randint(1, 3)
        page.goto(f"{BASE}/checkout.html?id={event_id}")
        human_delay()

def ensure_accounts_seeded(p):
    """開跑前先確保 accounts.txt 的 5 組帳號都已存在,避免 login_email 一直 401"""
    request_context = p.request.new_context(base_url=BASE, user_agent=random.choice(UA_POOL))
    for account in ACCOUNTS:
        try:
            resp = request_context.post(
                "/api/users/register",
                data={"email": account["email"], "password": account["password"], "name": account["name"]},
            )
            if resp.ok:
                print(f"[seed] 已建立帳號 {account['email']}")
            elif resp.status != 400:   # 400 = 已註冊過,略過即可
                print(f"[seed] {account['email']} 註冊回應異常: {resp.status} {resp.text()}")
        except Exception as e:
            print(f"[seed] {account['email']} 註冊例外: {e}")
    request_context.dispose()

with sync_playwright() as p:
    ensure_accounts_seeded(p)
    browser = p.chromium.launch(headless=False)   # 產生正式流量用 headless;要肉眼檢查就改 False
    for i in range(SESSION_COUNT):
        context = browser.new_context(          # 每個 session 開新 context
            user_agent=random.choice(UA_POOL)   # 隨機 UA,撐開 os_type 特徵
        )
        page = context.new_page()
        try:
            one_user_session(page)
        except Exception as e:
            print(f"session {i} error: {e}")
        context.close()
        time.sleep(random.uniform(0.2, 2.0))   # session 之間也隨機間隔
    browser.close()