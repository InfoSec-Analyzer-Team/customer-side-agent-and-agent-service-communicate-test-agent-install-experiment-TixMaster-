/**
 * TixMaster Feature Flags Service
 *
 * A client-side service for fetching and managing feature flags.
 * Includes caching to minimize API calls and improve performance.
 *
 * Usage:
 *   await FeatureFlags.init();
 *   if (FeatureFlags.isEnabled('ENABLE_VIEWING_COUNT')) {
 *     // Show viewing count
 *   }
 */

const FeatureFlags = (() => {
    const API_BASE_URL = 'http://localhost:3000/api';
    const CACHE_KEY = 'tixmaster_feature_flags';
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

    let flags = {};
    let lastFetchTime = null;
    let initialized = false;

    /**
     * Initialize the feature flags service
     * Automatically loads flags from cache or fetches from API
     */
    async function init() {
        if (initialized) {
            return;
        }

        // Try to load from cache first
        const cached = loadFromCache();
        if (cached) {
            flags = cached;
            initialized = true;
            console.log('[FeatureFlags] Loaded from cache:', flags);
        }

        // Fetch fresh data from API
        try {
            await refresh();
            initialized = true;
        } catch (error) {
            console.error('[FeatureFlags] Failed to initialize:', error);
            // If cache exists, continue with cached data
            if (Object.keys(flags).length > 0) {
                console.warn('[FeatureFlags] Using cached data due to API error');
                initialized = true;
            } else {
                throw new Error('Failed to initialize feature flags and no cache available');
            }
        }
    }

    /**
     * Fetch feature flags from API and update cache
     */
    async function refresh() {
        try {
            const response = await fetch(`${API_BASE_URL}/feature-flags`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            flags = data.flags || {};
            lastFetchTime = Date.now();

            // Save to cache
            saveToCache();

            console.log('[FeatureFlags] Refreshed from API:', flags);
            return flags;
        } catch (error) {
            console.error('[FeatureFlags] Failed to fetch:', error);
            throw error;
        }
    }

    /**
     * Check if a feature flag is enabled
     * @param {string} key - The feature flag key
     * @returns {boolean} - Whether the feature is enabled
     */
    function isEnabled(key) {
        if (!initialized) {
            console.warn(`[FeatureFlags] Not initialized yet. Checking flag: ${key}`);
            return false;
        }

        const flag = flags[key];
        if (!flag) {
            console.warn(`[FeatureFlags] Unknown flag: ${key}`);
            return false;
        }

        return flag.enabled === true;
    }

    /**
     * Get all feature flags
     * @returns {Object} - All feature flags
     */
    function getAll() {
        return { ...flags };
    }

    /**
     * Get a specific feature flag details
     * @param {string} key - The feature flag key
     * @returns {Object|null} - Feature flag details or null if not found
     */
    function getFlag(key) {
        return flags[key] || null;
    }

    /**
     * Update a feature flag (admin only)
     * @param {string} key - The feature flag key
     * @param {boolean} enabled - Whether to enable the flag
     * @returns {Promise<Object>} - Updated flag data
     */
    async function updateFlag(key, enabled) {
        try {
            // Ensure enabled is a boolean
            const booleanEnabled = Boolean(enabled);

            console.log(`[FeatureFlags] Updating ${key} to ${booleanEnabled} (type: ${typeof booleanEnabled})`);

            const requestBody = { enabled: booleanEnabled };
            console.log('[FeatureFlags] Request body:', JSON.stringify(requestBody));

            // Get admin token from localStorage
            const adminUser = JSON.parse(localStorage.getItem('adminUser') || 'null');
            const token = adminUser ? adminUser.token : null;

            if (!token) {
                throw new Error('管理員未登入或 token 已過期');
            }

            const response = await fetch(`${API_BASE_URL}/feature-flags/${key}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[FeatureFlags] Server error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('[FeatureFlags] Server response:', data);

            // Update local cache
            await refresh();

            console.log(`[FeatureFlags] Successfully updated ${key} to ${booleanEnabled}`);
            return data;
        } catch (error) {
            console.error('[FeatureFlags] Failed to update flag:', error);
            throw error;
        }
    }

    /**
     * Check if cache is still valid
     * @returns {boolean}
     */
    function isCacheValid() {
        if (!lastFetchTime) return false;
        return (Date.now() - lastFetchTime) < CACHE_DURATION;
    }

    /**
     * Load feature flags from localStorage
     * @returns {Object|null}
     */
    function loadFromCache() {
        try {
            const cached = localStorage.getItem(CACHE_KEY);
            if (!cached) return null;

            const data = JSON.parse(cached);

            // Check if cache is expired
            if (data.timestamp && (Date.now() - data.timestamp) < CACHE_DURATION) {
                lastFetchTime = data.timestamp;
                return data.flags;
            }

            return null;
        } catch (error) {
            console.error('[FeatureFlags] Failed to load from cache:', error);
            return null;
        }
    }

    /**
     * Save feature flags to localStorage
     */
    function saveToCache() {
        try {
            const data = {
                flags: flags,
                timestamp: lastFetchTime || Date.now()
            };
            localStorage.setItem(CACHE_KEY, JSON.stringify(data));
        } catch (error) {
            console.error('[FeatureFlags] Failed to save to cache:', error);
        }
    }

    /**
     * Clear cache
     */
    function clearCache() {
        try {
            localStorage.removeItem(CACHE_KEY);
            console.log('[FeatureFlags] Cache cleared');
        } catch (error) {
            console.error('[FeatureFlags] Failed to clear cache:', error);
        }
    }

    // Public API
    return {
        init,
        refresh,
        isEnabled,
        getAll,
        getFlag,
        updateFlag,
        isCacheValid,
        clearCache
    };
})();

// Auto-initialize on page load (optional)
if (typeof window !== 'undefined') {
    window.FeatureFlags = FeatureFlags;
}
