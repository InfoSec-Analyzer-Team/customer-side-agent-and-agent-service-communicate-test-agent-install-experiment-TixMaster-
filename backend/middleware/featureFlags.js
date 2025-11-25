/**
 * Feature Flags Middleware
 *
 * Provides server-side feature flag checking and enforcement.
 * Can be used to gate API endpoints or specific functionality.
 */

const db = require('../config/database');

/**
 * Cache for feature flags
 * Refreshed periodically to reduce database queries
 */
let flagCache = {};
let lastCacheUpdate = null;
const CACHE_DURATION = 60 * 1000; // 1 minute

/**
 * Refresh feature flags cache from database
 */
async function refreshFlagCache() {
    try {
        const result = await db.query(
            'SELECT flag_key, flag_value FROM feature_flags'
        );

        flagCache = {};
        result.rows.forEach(row => {
            flagCache[row.flag_key] = row.flag_value;
        });

        lastCacheUpdate = Date.now();
        console.log('[FeatureFlags] Cache refreshed:', flagCache);
    } catch (error) {
        console.error('[FeatureFlags] Failed to refresh cache:', error);
        throw error;
    }
}

/**
 * Get a feature flag value
 * @param {string} key - The feature flag key
 * @returns {Promise<boolean>} - Whether the feature is enabled
 */
async function isEnabled(key) {
    // Refresh cache if expired
    if (!lastCacheUpdate || (Date.now() - lastCacheUpdate) > CACHE_DURATION) {
        await refreshFlagCache();
    }

    return flagCache[key] === true;
}

/**
 * Middleware: Require a feature flag to be enabled
 * Returns 403 if the feature is disabled
 *
 * Usage:
 *   router.get('/some-endpoint', requireFeatureFlag('ENABLE_NEW_FEATURE'), (req, res) => { ... });
 */
function requireFeatureFlag(flagKey) {
    return async (req, res, next) => {
        try {
            const enabled = await isEnabled(flagKey);

            if (!enabled) {
                return res.status(403).json({
                    error: 'Feature not available',
                    message: `The feature "${flagKey}" is currently disabled`
                });
            }

            next();
        } catch (error) {
            console.error('[FeatureFlags] Error checking feature flag:', error);
            // Fail open: allow request if there's an error checking the flag
            next();
        }
    };
}

/**
 * Middleware: Attach feature flags to request object
 * Makes flags available as req.featureFlags
 *
 * Usage:
 *   app.use(attachFeatureFlags);
 *   // In routes:
 *   if (req.featureFlags.isEnabled('SOME_FLAG')) { ... }
 */
async function attachFeatureFlags(req, res, next) {
    try {
        // Refresh cache if expired
        if (!lastCacheUpdate || (Date.now() - lastCacheUpdate) > CACHE_DURATION) {
            await refreshFlagCache();
        }

        // Attach feature flags helper to request
        req.featureFlags = {
            isEnabled: (key) => flagCache[key] === true,
            getAll: () => ({ ...flagCache })
        };

        next();
    } catch (error) {
        console.error('[FeatureFlags] Error attaching feature flags:', error);
        // Fail open: continue with empty feature flags
        req.featureFlags = {
            isEnabled: () => false,
            getAll: () => ({})
        };
        next();
    }
}

/**
 * Express middleware to add feature flags to response headers
 * Useful for client-side debugging
 *
 * Usage:
 *   app.use(addFeatureFlagsToHeaders);
 */
async function addFeatureFlagsToHeaders(req, res, next) {
    try {
        if (!lastCacheUpdate || (Date.now() - lastCacheUpdate) > CACHE_DURATION) {
            await refreshFlagCache();
        }

        // Add as JSON string in header
        res.setHeader('X-Feature-Flags', JSON.stringify(flagCache));
    } catch (error) {
        console.error('[FeatureFlags] Error adding headers:', error);
    }

    next();
}

/**
 * Initialize feature flags cache on server startup
 */
async function initialize() {
    try {
        await refreshFlagCache();
        console.log('[FeatureFlags] Middleware initialized');
    } catch (error) {
        console.error('[FeatureFlags] Failed to initialize:', error);
    }
}

module.exports = {
    isEnabled,
    requireFeatureFlag,
    attachFeatureFlags,
    addFeatureFlagsToHeaders,
    refreshFlagCache,
    initialize
};
