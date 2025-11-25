import pytest
import requests


@pytest.mark.toggle
def test_get_all_flags(base_url):
    r = requests.get(f"{base_url}/api/feature-flags", timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert 'flags' in j and isinstance(j['flags'], dict)


@pytest.mark.toggle
def test_get_single_flag_not_found(base_url):
    r = requests.get(f"{base_url}/api/feature-flags/INVALID_FLAG", timeout=5)
    assert r.status_code == 404


@pytest.mark.toggle
def test_update_requires_auth(base_url):
    payload = {'enabled': True}
    r = requests.put(f"{base_url}/api/feature-flags/some_flag", json=payload, timeout=5)
    assert r.status_code in (401, 403)


@pytest.mark.toggle
def test_update_with_admin_token(base_url, admin_token):
    if not admin_token:
        pytest.skip('ADMIN_TOKEN not set; skipping authenticated update test')
    headers = {'Authorization': f"Bearer {admin_token}"}
    payload = {'enabled': True}
    r = requests.put(f"{base_url}/api/feature-flags/some_flag", json=payload, headers=headers, timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert 'flag' in j
