-- 创建管理员账户用于测试
-- Email: admin@tixmaster.com
-- 密码: admin123
-- 密码 hash 使用 bcrypt 生成 (salt rounds = 10)

-- 检查是否已存在管理员账户
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@tixmaster.com') THEN
        INSERT INTO users (email, password_hash, name, phone, role, created_at, updated_at)
        VALUES (
            'admin@tixmaster.com',
            '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG',  -- admin123
            'System Admin',
            '0900000000',
            'admin',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        RAISE NOTICE '管理員帳號已創建: admin@tixmaster.com / admin123';
    ELSE
        RAISE NOTICE '管理員帳號已存在: admin@tixmaster.com';
        -- 如果需要更新密码，取消下面的注释
        -- UPDATE users SET password_hash = '$2b$10$SJHcEDF1dBZ03/eJNSXyyeE1Y6pqzgYN/x1X/Si7ivm0gFEe2MUgG' WHERE email = 'admin@tixmaster.com';
    END IF;
END $$;
