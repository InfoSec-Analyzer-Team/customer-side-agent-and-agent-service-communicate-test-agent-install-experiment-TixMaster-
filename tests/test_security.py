import pytest
import requests


def test_protected_route_requires_auth(base_url):
    r = requests.put(f"{base_url}/api/feature-flags/some_flag", json={'enabled': False}, timeout=5)
    assert r.status_code in (401, 403)


def test_put_enabled_type_validation(base_url, admin_token):
    if not admin_token:
        pytest.skip('ADMIN_TOKEN not set; skipping validation test that requires auth')
    headers = {'Authorization': f"Bearer {admin_token}"}
    payload = {'enabled': 'not_boolean'}
    r = requests.put(f"{base_url}/api/feature-flags/some_flag", json=payload, headers=headers, timeout=5)
    assert r.status_code == 400
