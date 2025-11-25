-- Migration: 添加 password_hash 欄位到 users 表
-- 用於支援傳統帳密登入（管理員）

-- 檢查欄位是否已存在
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        -- 添加 password_hash 欄位
        ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
        RAISE NOTICE '✅ password_hash 欄位已添加';
    ELSE
        RAISE NOTICE 'ℹ️ password_hash 欄位已存在';
    END IF;
END $$;
