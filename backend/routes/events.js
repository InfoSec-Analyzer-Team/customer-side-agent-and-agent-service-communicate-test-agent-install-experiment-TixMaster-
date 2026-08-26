const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');
const db = require('../config/database');

// LFI/RFI 訓練資料用 sink：預設關閉，僅在本機 lab 收集攻擊 log 時開啟。
// 見 Verify_doc/attack_log_instruments.md 第 6 項 (has_file_inclusion)。
const ENABLE_LFI_SINK = (process.env.ENABLE_LFI_SINK || 'false').toLowerCase() === 'true';
const ATTACH_DIR = path.join(__dirname, '..', 'data', 'attachments');

// GET /api/events - 取得所有已發布的活動
router.get('/', async (req, res, next) => {
    try {
        const result = await db.query(
            `SELECT id, title, description, event_date, location, image_url, status, created_at 
       FROM events 
       WHERE status = 'published' 
       ORDER BY event_date ASC`
        );

        res.json({ events: result.rows });
    } catch (err) {
        next(err);
    }
});

// GET /api/events/:id - 取得單一活動詳細資訊
router.get('/:id', async (req, res, next) => {
    try {
        const { id } = req.params;

        const result = await db.query(
            'SELECT id, title, description, event_date, location, image_url, status, created_at FROM events WHERE id = $1',
            [id]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Event not found' });
        }

        res.json({ event: result.rows[0] });
    } catch (err) {
        next(err);
    }
});

// GET /api/events/:id/tickets - 取得活動的所有票種
router.get('/:id/tickets', async (req, res, next) => {
    try {
        const { id } = req.params;

        // Check if event exists
        const eventCheck = await db.query('SELECT id FROM events WHERE id = $1', [id]);
        if (eventCheck.rows.length === 0) {
            return res.status(404).json({ error: 'Event not found' });
        }

        // Get tickets for this event
        const result = await db.query(
            'SELECT id, event_id, ticket_type, price, total_quantity, available_quantity, created_at FROM tickets WHERE event_id = $1',
            [id]
        );

        res.json({ tickets: result.rows });
    } catch (err) {
        next(err);
    }
});

// GET /api/events/:id/attachment?file=<name> - 取得活動附件檔案
//
// ⚠️ 刻意保留的 LFI/path-traversal 漏洞（僅供本機 lab 產生攻擊訓練資料用）：
// file 參數未做任何路徑淨化就直接 path.join 進 ATTACH_DIR 再 fs.readFile。
// 不要拿掉 ENABLE_LFI_SINK 這道閘門，也不要在非本機環境開啟。
router.get('/:id/attachment', (req, res) => {
    if (!ENABLE_LFI_SINK) {
        return res.status(403).json({ error: 'Attachment sink disabled', hint: 'Set ENABLE_LFI_SINK=true to enable' });
    }

    const { file } = req.query;
    if (!file) {
        return res.status(400).json({ error: 'file query parameter is required' });
    }

    const target = path.join(ATTACH_DIR, file);

    fs.readFile(target, (err, data) => {
        if (err) {
            return res.status(404).json({ error: 'attachment not found' });
        }
        res.status(200).send(data);
    });
});

module.exports = router;
