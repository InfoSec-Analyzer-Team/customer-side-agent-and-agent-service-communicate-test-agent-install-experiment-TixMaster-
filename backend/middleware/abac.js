/**
 * 🎭 ABAC Middleware
 * Attribute-Based Access Control
 */

/**
 * Check if user meets a dynamic policy
 * @param {function} policyFn - Function that returns true if access is allowed
 *                              (user, resource) => boolean
 */
const checkPolicy = (policyFn) => {
    return async (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Unauthorized' });
        }

        try {
            // Resource can be in body, params, or query
            // We pass the entire request object for maximum flexibility, 
            // but usually policies care about specific resources.
            // For simplicity in this middleware, we let the policyFn handle extraction if needed,
            // OR we can pass a standard 'resource' object if we standardize it.

            // Here we pass the full request so the policy can inspect params/body
            const allowed = await policyFn(req.user, req);

            if (!allowed) {
                return res.status(403).json({
                    error: 'Forbidden',
                    message: 'Access denied by policy'
                });
            }

            next();
        } catch (error) {
            console.error('ABAC Policy Error:', error);
            res.status(500).json({ error: 'Internal Server Error' });
        }
    };
};

// --- Common Policies ---

/**
 * Policy: User can only access their own data
 * Checks several common places for IDs and compares as strings to avoid
 * type mismatches (number vs string). Returns true when the user is the
 * target owner. For profile-style endpoints where no target ID is present
 * we treat the requestor as the owner (backwards-compatible behavior).
 */
const isOwner = (user, req) => {
    const userId = user && (user.userId || user.id);

    // If accessing /resources/:id or similar
    if (req.params && req.params.id) {
        return String(userId) === String(req.params.id);
    }

    // If caller provided an explicit target in body (e.g., { id: '...' })
    if (req.body && (req.body.id || req.body.userId)) {
        return String(userId) === String(req.body.id || req.body.userId);
    }

    // Fallback: profile-style endpoints (no explicit target) -> allow
    return Boolean(userId);
};

/**
 * Policy: User is admin OR owner
 */
const isAdminOrOwner = (user, req) => {
    if (user && (user.role === 'admin' || user.role === 'ADMIN')) return true;
    return isOwner(user, req);
};

module.exports = {
    checkPolicy,
    policies: {
        isOwner,
        isAdminOrOwner
    }
};
