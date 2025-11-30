const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const db = require('../config/database');
const authenticateToken = require('../middleware/auth');
const { metrics } = require('../config/metrics'); // Import metrics

// POST /api/orders - 建立訂單 (需認證)
router.post('/', authenticateToken, async (req, res, next) => {
    const client = await db.pool.connect();

    try {
        const { eventId, ticketId, quantity, paymentMethod } = req.body;
        const userId = req.user.userId;

        if (!eventId || !ticketId || !quantity) {
            return res.status(400).json({ error: 'Event ID, ticket ID and quantity are required' });
        }

        await client.query('BEGIN');

        // Check ticket availability
        const ticketResult = await client.query(
            'SELECT id, price, available_quantity FROM tickets WHERE id = $1 FOR UPDATE',
            [ticketId]
        );

        if (ticketResult.rows.length === 0) {
            await client.query('ROLLBACK');
            return res.status(404).json({ error: 'Ticket not found' });
        }

        const ticket = ticketResult.rows[0];

        if (ticket.available_quantity < quantity) {
            await client.query('ROLLBACK');
            return res.status(400).json({ error: 'Not enough tickets available' });
        }

        // Calculate total amount
        const totalAmount = ticket.price * quantity;

        // Generate order number
        const orderNumber = `TIX-${Date.now()}-${uuidv4().substring(0, 8).toUpperCase()}`;

        // Set expiration time (15 minutes from now)
        const expiredAt = new Date(Date.now() + 15 * 60 * 1000);

        // Create order
        const orderResult = await client.query(
            `INSERT INTO orders (order_number, user_id, event_id, ticket_id, quantity, total_amount, status, payment_method, expired_at) 
       VALUES ($1, $2, $3, $4, $5, $6, 'pending', $7, $8) 
       RETURNING *`,
            [orderNumber, userId, eventId, ticketId, quantity, totalAmount, paymentMethod, expiredAt]
        );

        const order = orderResult.rows[0];

        // Update ticket availability
        await client.query(
            'UPDATE tickets SET available_quantity = available_quantity - $1 WHERE id = $2',
            [quantity, ticketId]
        );

        // Create order items (individual tickets)
        const orderItems = [];
        for (let i = 0; i < quantity; i++) {
            const ticketCode = `${orderNumber}-${i + 1}`;
            const itemResult = await client.query(
                'INSERT INTO order_items (order_id, ticket_code, status) VALUES ($1, $2, $3) RETURNING *',
                [order.id, ticketCode, 'valid']
            );
            orderItems.push(itemResult.rows[0]);
        }

        await client.query('COMMIT');

        // 記錄訂單 Metrics
        metrics.ordersTotal.inc({
            event_id: eventId,
            payment_method: paymentMethod
        });

        res.status(201).json({
            message: 'Order created successfully',
            order: {
                ...order,
                items: orderItems
            }
        });
    } catch (err) {
        await client.query('ROLLBACK');
        next(err);
    } finally {
        client.release();
    }
});

// GET /api/orders/:orderNumber - 取得訂單詳情
router.get('/:orderNumber', async (req, res, next) => {
    try {
        const { orderNumber } = req.params;

        const result = await db.query(
            `SELECT o.*, e.title as event_title, e.event_date, t.ticket_type 
       FROM orders o
       JOIN events e ON o.event_id = e.id
       JOIN tickets t ON o.ticket_id = t.id
       WHERE o.order_number = $1`,
            [orderNumber]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Order not found' });
        }

        res.json({ order: result.rows[0] });
    } catch (err) {
        next(err);
    }
});

// GET /api/orders/user/me - 取得當前使用者所有訂單 (需認證)
router.get('/user/me', authenticateToken, async (req, res, next) => {
    try {
        const userId = req.user.userId;

        const result = await db.query(
            `SELECT o.*, e.title as event_title, e.event_date, t.ticket_type 
       FROM orders o
       JOIN events e ON o.event_id = e.id
       JOIN tickets t ON o.ticket_id = t.id
       WHERE o.user_id = $1
       ORDER BY o.created_at DESC`,
            [userId]
        );

        res.json({ orders: result.rows });
    } catch (err) {
        next(err);
    }
});

// PUT /api/orders/:orderNumber/payment - 更新訂單付款狀態
router.put('/:orderNumber/payment', async (req, res, next) => {
    try {
        const { orderNumber } = req.params;
        const { status } = req.body; // 'paid' or 'cancelled'

        if (!['paid', 'cancelled'].includes(status)) {
            return res.status(400).json({ error: 'Invalid status. Must be "paid" or "cancelled"' });
        }

        const paidAt = status === 'paid' ? new Date() : null;

        const result = await db.query(
            'UPDATE orders SET status = $1, paid_at = $2 WHERE order_number = $3 RETURNING *',
            [status, paidAt, orderNumber]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Order not found' });
        }

        res.json({
            message: 'Order payment status updated',
            order: result.rows[0]
        });
    } catch (err) {
        next(err);
    }
});

// GET /api/orders/:orderNumber/tickets - 取得訂單票券 (含 QR code)
router.get('/:orderNumber/tickets', async (req, res, next) => {
    try {
        const { orderNumber } = req.params;

        // Get order
        const orderResult = await db.query(
            'SELECT id FROM orders WHERE order_number = $1',
            [orderNumber]
        );

        if (orderResult.rows.length === 0) {
            return res.status(404).json({ error: 'Order not found' });
        }

        const orderId = orderResult.rows[0].id;

        // Get order items
        const itemsResult = await db.query(
            'SELECT id, ticket_code, qr_code, status, used_at FROM order_items WHERE order_id = $1',
            [orderId]
        );

        res.json({ tickets: itemsResult.rows });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
