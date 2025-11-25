import os
import subprocess
import pytest


@pytest.fixture(scope='session')
def base_url():
    return os.getenv('BASE_URL', 'http://localhost:3000')


@pytest.fixture(scope='session')
def admin_token():
    # Prefer explicit ADMIN_TOKEN. If missing, but JWT_SECRET exists, generate token via Node script.
    token = os.getenv('ADMIN_TOKEN')
    if token:
        return token

    jwt_secret = os.getenv('JWT_SECRET')
    if not jwt_secret:
        # fallback: try to read backend/.env for JWT_SECRET (CI step writes the file)
        try:
            with open('backend/.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('JWT_SECRET='):
                        jwt_secret = line.strip().split('=', 1)[1]
                        break
        except Exception:
            jwt_secret = None
    if not jwt_secret:
        return None

    # Attempt to generate ADMIN_TOKEN using the repository's Node helper.
    try:
        # run from repo root; node script reads backend/.env fallback if needed
        proc = subprocess.run([
            'node', 'tools/gen_admin_jwt.js'
        ], check=True, capture_output=True, text=True)
        token = proc.stdout.strip()
        if token:
            # export into environment for any downstream code
            os.environ['ADMIN_TOKEN'] = token
            return token
    except Exception:
        # if generation fails, return None so tests skip as before
        return None
