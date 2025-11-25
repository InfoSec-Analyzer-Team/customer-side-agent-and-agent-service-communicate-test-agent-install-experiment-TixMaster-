-- ============================================
-- TixMaster PostgreSQL Schema
-- ============================================

-- 1. users (使用者)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- bcrypt 雜湊；允許 NULL 以支援 OAuth-only 帳號
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_email ON users(email);

-- 觸發器：自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================

-- 2. login_sessions (登入 Session)
CREATE TABLE login_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),  -- 支援 IPv6
    user_agent VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE UNIQUE INDEX idx_sessions_token ON login_sessions(session_token);
CREATE INDEX idx_sessions_user_id ON login_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON login_sessions(expires_at);

-- ============================================

-- 3. oauth_accounts (第三方登入)
CREATE TABLE oauth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'facebook', 'line'
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,  -- 加密儲存
    refresh_token TEXT,  -- 加密儲存
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_oauth_user_id ON oauth_accounts(user_id);
CREATE UNIQUE INDEX idx_oauth_provider_user ON oauth_accounts(provider, provider_user_id);

CREATE TRIGGER update_oauth_accounts_updated_at BEFORE UPDATE ON oauth_accounts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================

-- 4. events (活動)
CREATE TYPE event_status AS ENUM ('draft', 'published', 'sold_out', 'cancelled');

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    location VARCHAR(200) NOT NULL,
    image_url VARCHAR(500),
    status event_status DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_date ON events(event_date);

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================

-- 5. tickets (票種)
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    ticket_type VARCHAR(50) NOT NULL,  -- 例如：一般票、VIP票
    price DECIMAL(10,2) NOT NULL,
    total_quantity INTEGER NOT NULL,
    available_quantity INTEGER NOT NULL,  -- 剩餘數量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_quantity CHECK (available_quantity >= 0 AND available_quantity <= total_quantity)
);

-- 索引
CREATE INDEX idx_tickets_event_id ON tickets(event_id);

-- ============================================

-- 6. orders (訂單)
CREATE TYPE order_status AS ENUM ('pending', 'paid', 'cancelled', 'expired');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,  -- 例如：TM20251124-001
    user_id INTEGER NOT NULL REFERENCES users(id),
    event_id INTEGER NOT NULL REFERENCES events(id),
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    quantity INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status order_status DEFAULT 'pending',
    payment_method VARCHAR(50),  -- 例如：信用卡、ATM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    expired_at TIMESTAMP  -- 建立後 10 分鐘
);

-- 索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_event_id ON orders(event_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ============================================

-- 7. order_items (訂單明細/票券)
CREATE TYPE ticket_status AS ENUM ('valid', 'used', 'cancelled');

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,  -- 例如：TM-ABC123
    qr_code TEXT,  -- Base64 或路徑
    status ticket_status DEFAULT 'valid',
    used_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE UNIQUE INDEX idx_order_items_ticket_code ON order_items(ticket_code);

-- ============================================

-- 8. waiting_queue (等待隊列)
CREATE TYPE queue_status AS ENUM ('waiting', 'processing', 'completed');

CREATE TABLE waiting_queue (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    event_id INTEGER REFERENCES events(id),
    queue_position INTEGER,
    status queue_status DEFAULT 'waiting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_queue_session_id ON waiting_queue(session_id);
CREATE INDEX idx_queue_event_id ON waiting_queue(event_id);
CREATE INDEX idx_queue_status ON waiting_queue(status);

-- ============================================

-- 9. feature_flags (功能開關)
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) UNIQUE NOT NULL,  -- 例如：ENABLE_CHECKOUT_TIMER
    flag_value BOOLEAN DEFAULT FALSE,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_feature_flags_updated_at BEFORE UPDATE ON feature_flags
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 預設功能開關
INSERT INTO feature_flags (flag_key, flag_value, description) VALUES
('ENABLE_CHECKOUT_TIMER', true, '結帳倒數計時器'),
('ENABLE_VIEWING_COUNT', true, '活動觀看人數顯示');

-- ============================================

-- 10. analytics_events (分析數據)
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,  -- 例如：page_view, button_click
    event_data JSONB,  -- 彈性的 JSON 資料
    feature_flags JSONB,  -- 當時的功能開關狀態
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_analytics_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created_at ON analytics_events(created_at);
-- JSONB 索引（加速 JSON 查詢）
CREATE INDEX idx_analytics_event_data ON analytics_events USING GIN (event_data);

-- ============================================

-- 函數：自動產生訂單編號
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS VARCHAR AS $$
DECLARE
    new_order_number VARCHAR;
    max_sequence INTEGER;
BEGIN
    -- 取得今天的最大序號
    SELECT COALESCE(MAX(CAST(SUBSTRING(order_number FROM 12) AS INTEGER)), 0) + 1
    INTO max_sequence
    FROM orders
    WHERE order_number LIKE 'TM' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-%';
    
    -- 產生新的訂單編號
    new_order_number := 'TM' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || LPAD(max_sequence::TEXT, 3, '0');
    
    RETURN new_order_number;
END;
$$ LANGUAGE plpgsql;

-- ============================================

-- 函數：扣除票券庫存（防止超賣）
CREATE OR REPLACE FUNCTION reserve_tickets(
    p_ticket_id INTEGER,
    p_quantity INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    available INTEGER;
BEGIN
    -- 鎖定票券列，檢查庫存
    SELECT available_quantity INTO available
    FROM tickets
    WHERE id = p_ticket_id
    FOR UPDATE;  -- 列級鎖定
    
    -- 檢查庫存是否足夠
    IF available >= p_quantity THEN
        -- 扣除庫存
        UPDATE tickets
        SET available_quantity = available_quantity - p_quantity
        WHERE id = p_ticket_id;
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================

-- 函數：釋放票券庫存（訂單取消或逾期）
CREATE OR REPLACE FUNCTION release_tickets(
    p_ticket_id INTEGER,
    p_quantity INTEGER
) RETURNS VOID AS $$
BEGIN
    UPDATE tickets
    SET available_quantity = available_quantity + p_quantity
    WHERE id = p_ticket_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================

-- 觸發器：訂單建立時自動設定 expired_at
CREATE OR REPLACE FUNCTION set_order_expiration()
RETURNS TRIGGER AS $$
BEGIN
    NEW.expired_at := NEW.created_at + INTERVAL '10 minutes';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_order_expiration_trigger
BEFORE INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION set_order_expiration();

-- ============================================

-- 觸發器：訂單取消時自動釋放票券
CREATE OR REPLACE FUNCTION release_tickets_on_cancel()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('cancelled', 'expired') AND OLD.status = 'pending' THEN
        PERFORM release_tickets(NEW.ticket_id, NEW.quantity);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER release_tickets_on_cancel_trigger
AFTER UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION release_tickets_on_cancel();

-- ============================================
-- 範例資料
-- ============================================

-- 插入測試活動
INSERT INTO events (title, description, event_date, location, image_url, status) VALUES
('Neon Dreams 演唱會', '體驗未來音樂的視聽饗宴', '2025-12-15 19:00:00', '台北 Cyber Arena', 'https://images.unsplash.com/photo-1459749411177-718bf998e889?w=1000', 'published'),
('科技峰會 2025', '與科技界領袖一同探索創新與未來', '2025-11-30 09:00:00', '台北國際會議中心', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1000', 'published'),
('聖誕交響樂之夜', '與國家交響樂團共度浪漫的聖誕夜', '2025-12-24 20:00:00', '國家音樂廳', 'https://images.unsplash.com/photo-1465847899078-b413929f7120?w=1000', 'published');

-- 插入測試票種
INSERT INTO tickets (event_id, ticket_type, price, total_quantity, available_quantity) VALUES
(1, '一般票', 2500.00, 1000, 1000),
(1, 'VIP票', 5000.00, 100, 100),
(2, '一般票', 1200.00, 500, 500),
(3, '一般票', 3000.00, 800, 800);
