const express = require('express');
const router = express.Router();
const db = require('../config/database');
const logger = require('../config/logger');

// POST /api/analytics/event - 記錄分析事件
router.post('/event', async (req, res, next) => {
    try {
        const { userId, sessionId, eventType, eventData, featureFlagsSnapshot } = req.body;

        if (!eventType) {
            return res.status(400).json({ error: 'eventType is required' });
        }

        await db.query(
            `INSERT INTO analytics_events (user_id, session_id, event_type, event_data, feature_flags_snapshot) 
       VALUES ($1, $2, $3, $4, $5)`,
            [userId || null, sessionId, eventType, JSON.stringify(eventData || {}), JSON.stringify(featureFlagsSnapshot || {})]
        );

        res.status(201).json({ message: 'Event logged successfully' });
    } catch (err) {
        next(err);
    }
});

// GET /api/analytics/events - 取得分析事件 (可用於數據分析)
router.get('/events', async (req, res, next) => {
    try {
        const { eventType, sessionId, limit = 100 } = req.query;

        let query = 'SELECT * FROM analytics_events WHERE 1=1';
        const params = [];
        let paramCount = 1;

        if (eventType) {
            query += ` AND event_type = $${paramCount}`;
            params.push(eventType);
            paramCount++;
        }

        if (sessionId) {
            query += ` AND session_id = $${paramCount}`;
            params.push(sessionId);
            paramCount++;
        }

        query += ` ORDER BY created_at DESC LIMIT $${paramCount}`;
        params.push(parseInt(limit));

        const result = await db.query(query, params);

        res.json({ events: result.rows });
    } catch (err) {
        next(err);
    }
});

// GET /api/analytics/metrics - 計算關鍵指標
router.get('/metrics', async (req, res, next) => {
    try {
        const { start_date, end_date } = req.query;

        req.logger.info('[Analytics Metrics] Calculating metrics', { start_date, end_date });

        // Hypothesis 1: Payment Completion Rate
        const h1Query = `
            WITH checkout_sessions AS (
                SELECT DISTINCT
                    session_id,
                    COALESCE(
                        (feature_flags_snapshot->>'ENABLE_CHECKOUT_TIMER')::boolean,
                        false
                    ) as has_timer
                FROM analytics_events
                WHERE event_type IN ('checkout_timer_shown', 'payment_attempted')
                    ${start_date ? "AND created_at >= $1" : ""}
                    ${end_date ? `AND created_at <= $${start_date ? '2' : '1'}` : ""}
            ),
            payment_completions AS (
                SELECT DISTINCT session_id
                FROM analytics_events
                WHERE event_type = 'payment_completed'
                    ${start_date ? "AND created_at >= $1" : ""}
                    ${end_date ? `AND created_at <= $${start_date ? '2' : '1'}` : ""}
            )
            SELECT
                cs.has_timer,
                COUNT(DISTINCT cs.session_id) as total_sessions,
                COUNT(DISTINCT pc.session_id) as completed_payments,
                ROUND(
                    (COUNT(DISTINCT pc.session_id)::numeric / NULLIF(COUNT(DISTINCT cs.session_id), 0)) * 100,
                    2
                ) as completion_rate_percent
            FROM checkout_sessions cs
            LEFT JOIN payment_completions pc ON cs.session_id = pc.session_id
            GROUP BY cs.has_timer
            ORDER BY cs.has_timer;
        `;

        const params = [];
        if (start_date) params.push(start_date);
        if (end_date) params.push(end_date);

        const h1Result = await db.query(h1Query, params);

        // Hypothesis 2: Buy Now CTR
        const h2Query = `
            WITH viewing_sessions AS (
                SELECT DISTINCT
                    session_id,
                    COALESCE(
                        (feature_flags_snapshot->>'ENABLE_VIEWING_COUNT')::boolean,
                        false
                    ) as has_viewing_count
                FROM analytics_events
                WHERE event_type = 'viewing_count_shown'
                    ${start_date ? "AND created_at >= $1" : ""}
                    ${end_date ? `AND created_at <= $${start_date ? '2' : '1'}` : ""}
            ),
            buy_clicks AS (
                SELECT DISTINCT session_id
                FROM analytics_events
                WHERE event_type = 'buy_now_clicked'
                    ${start_date ? "AND created_at >= $1" : ""}
                    ${end_date ? `AND created_at <= $${start_date ? '2' : '1'}` : ""}
            )
            SELECT
                vs.has_viewing_count,
                COUNT(DISTINCT vs.session_id) as total_views,
                COUNT(DISTINCT bc.session_id) as buy_clicks,
                ROUND(
                    (COUNT(DISTINCT bc.session_id)::numeric / NULLIF(COUNT(DISTINCT vs.session_id), 0)) * 100,
                    2
                ) as ctr_percent
            FROM viewing_sessions vs
            LEFT JOIN buy_clicks bc ON vs.session_id = bc.session_id
            GROUP BY vs.has_viewing_count
            ORDER BY vs.has_viewing_count;
        `;

        const h2Result = await db.query(h2Query, params);

        req.logger.info('[Analytics Metrics] H1 Results', { h1Count: h1Result.rows.length });
        req.logger.info('[Analytics Metrics] H2 Results', { h2Count: h2Result.rows.length });

        res.json({
            hypothesis1: {
                name: 'Urgency Tactic - Payment Completion Rate',
                metric: 'Payment Completion Rate (%)',
                data: h1Result.rows
            },
            hypothesis2: {
                name: 'Social Proof - Buy Now CTR',
                metric: 'Click-Through Rate (%)',
                data: h2Result.rows
            }
        });

    } catch (err) {
        req.logger.error('[Analytics Metrics] Error', { error: err.message, stack: err.stack });
        next(err);
    }
});

// GET /api/analytics/summary - 獲取統計摘要
router.get('/summary', async (req, res, next) => {
    try {
        const result = await db.query(`
            SELECT
                event_type,
                COUNT(*) as count,
                COUNT(DISTINCT session_id) as unique_sessions,
                MAX(created_at) as last_event
            FROM analytics_events
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY event_type
            ORDER BY count DESC;
        `);

        res.json({ summary: result.rows });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
