/**
 * Generate bcrypt hash for admin password
 * Usage: node create_admin_hash.js
 */

const bcrypt = require('bcrypt');

const password = 'admin123';
const saltRounds = 10;

bcrypt.hash(password, saltRounds, (err, hash) => {
    if (err) {
        console.error('Error generating hash:', err);
        process.exit(1);
    }

    console.log('\n=== Admin Account Hash Generated ===');
    console.log('Password:', password);
    console.log('Hash:', hash);
    console.log('\nSQL Command:');
    console.log(`INSERT INTO users (email, password_hash, name, phone, role) VALUES`);
    console.log(`('admin@tixmaster.com', '${hash}', 'System Admin', '0900000000', 'admin');`);
    console.log('\n=== Copy the SQL command above to create admin account ===\n');
});
