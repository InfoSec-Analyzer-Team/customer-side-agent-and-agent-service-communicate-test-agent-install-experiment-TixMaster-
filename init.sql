-- 1. 建立 ENUM 類型 (PostgreSQL 特有)
CREATE TYPE event_status AS ENUM ('draft', 'published', 'sold_out', 'cancelled');
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'cancelled', 'expired');
CREATE TYPE ticket_item_status AS ENUM ('valid', 'used', 'cancelled');
CREATE TYPE queue_status AS ENUM ('waiting', 'processing', 'completed');
CREATE TYPE discount_type AS ENUM ('percentage', 'fixed_amount');

-- 2. Users (使用者)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- 修正：這裡存放的是 Hash 值，對 OAuth-only 帳號允許 NULL
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) DEFAULT 'user', -- RBAC 角色
    attributes JSONB DEFAULT '{}',   -- ABAC 屬性
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Login Sessions (登入 Session)
CREATE TABLE login_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45), -- 支援 IPv6
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sessions_user_id ON login_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON login_sessions(expires_at);

-- 4. OAuth Accounts (第三方登入)
CREATE TABLE oauth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    provider VARCHAR(50) NOT NULL, -- google, facebook, etc.
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT, -- 建議加密儲存 (Application Level Encryption)
    refresh_token TEXT, -- 建議加密儲存
    token_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider, provider_user_id)
);

-- 5. Events (活動)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date TIMESTAMPTZ NOT NULL,
    location VARCHAR(200) NOT NULL,
    image_url VARCHAR(500),
    status event_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tickets (票種)
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id),
    ticket_type VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    total_quantity INT NOT NULL,
    available_quantity INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_tickets_event_id ON tickets(event_id);

-- 7. Orders (訂單)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT REFERENCES users(id),
    event_id INT REFERENCES events(id),
    ticket_id INT REFERENCES tickets(id),
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status order_status DEFAULT 'pending',
    payment_method VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ -- 訂單逾期時間
);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);

-- 8. Order Items (訂單明細 - 每張票)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    qr_code TEXT,
    status ticket_item_status DEFAULT 'valid',
    used_at TIMESTAMPTZ
);

-- 9. Feature Flags (功能開關 - for HDD Hypothesis)
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) UNIQUE NOT NULL, -- e.g., ENABLE_CHECKOUT_TIMER
    flag_value BOOLEAN DEFAULT FALSE,
    description VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 10. Analytics Events (數據分析 - for HDD Validation)
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    session_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL, -- e.g., page_view, button_click
    event_data JSONB, -- Postgres 使用 JSONB 效能更好
    feature_flags_snapshot JSONB, -- 記錄當下的開關狀態
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);

-- 初始化 HDD 實驗開關資料 (根據 README)
INSERT INTO feature_flags (flag_key, flag_value, description) VALUES 
('ENABLE_CHECKOUT_TIMER', FALSE, 'Hypothesis 1: Urgency Tactic'),
('ENABLE_VIEWING_COUNT', FALSE, 'Hypothesis 2: Social Proof');