const express = require('express');
const router = express.Router();
const db = require('../config/database');
const authenticateToken = require('../middleware/auth');
const { checkPermission } = require('../middleware/rbac');
const { PERMISSIONS } = require('../config/roles');

// GET /api/feature-flags - 取得所有功能開關
router.get('/', async (req, res, next) => {
    try {
        const result = await db.query(
            'SELECT flag_key, flag_value, description, updated_at FROM feature_flags ORDER BY flag_key'
        );

        // Convert to key-value format for easier frontend consumption
        const flags = {};
        result.rows.forEach(row => {
            flags[row.flag_key] = {
                enabled: row.flag_value,
                description: row.description,
                updatedAt: row.updated_at
            };
        });

        res.json({ flags });
    } catch (err) {
        next(err);
    }
});

// GET /api/feature-flags/:key - 取得單一功能開關
router.get('/:key', async (req, res, next) => {
    try {
        const { key } = req.params;

        const result = await db.query(
            'SELECT flag_key, flag_value, description, updated_at FROM feature_flags WHERE flag_key = $1',
            [key]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Feature flag not found' });
        }

        const flag = result.rows[0];

        res.json({
            key: flag.flag_key,
            enabled: flag.flag_value,
            description: flag.description,
            updatedAt: flag.updated_at
        });
    } catch (err) {
        next(err);
    }
});

// PUT /api/feature-flags/:key - 更新功能開關 (管理員用)
// Require authentication and manage-feature-flags permission
router.put('/:key', authenticateToken, checkPermission(PERMISSIONS.MANAGE_FEATURE_FLAGS), async (req, res, next) => {
    try {
        const { key } = req.params;
        const { enabled } = req.body;

        if (typeof enabled !== 'boolean') {
            return res.status(400).json({ error: 'enabled must be a boolean value' });
        }

        const result = await db.query(
            'UPDATE feature_flags SET flag_value = $1, updated_at = CURRENT_TIMESTAMP WHERE flag_key = $2 RETURNING *',
            [enabled, key]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Feature flag not found' });
        }

        res.json({
            message: 'Feature flag updated',
            flag: {
                key: result.rows[0].flag_key,
                enabled: result.rows[0].flag_value,
                description: result.rows[0].description
            }
        });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
