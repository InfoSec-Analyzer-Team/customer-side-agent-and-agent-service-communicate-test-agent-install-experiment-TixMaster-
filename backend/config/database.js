const { Pool } = require('pg');
require('dotenv').config();

// If SKIP_DB is set or DATABASE_URL is not provided, export a stubbed DB interface
if (process.env.SKIP_DB === 'true' || !process.env.DATABASE_URL) {
    console.warn('[Database] SKIP_DB is enabled or DATABASE_URL missing — exporting stubbed DB (no actual DB connections)');
    module.exports = {
        // query returns an object with rows array to mimic pg Pool.query
        query: async (text, params) => {
            return { rows: [] };
        },
        pool: null
    };
} else {
    const useSsl = process.env.DATABASE_SSL === 'true' || process.env.NODE_ENV === 'production';
    const pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ...(useSsl ? { ssl: { rejectUnauthorized: false } } : { ssl: false })
    });

    // Test connection
    pool.on('connect', () => {
        console.log('✓ Connected to PostgreSQL database');
    });

    // An idle client can emit 'error' if its connection drops (DB restart, network
    // blip, etc). node-postgres removes that client from the pool automatically;
    // the next query just gets a new connection. No need to crash the whole API
    // over a transient disconnect — that turned a few seconds of DB downtime into
    // a full server outage the last time this happened.
    pool.on('error', (err) => {
        console.error('Unexpected database error (pool will recover):', err);
    });

    module.exports = {
        query: (text, params) => pool.query(text, params),
        pool
    };
}
