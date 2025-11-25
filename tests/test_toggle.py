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


def test_get_flag_structure(base_url):
    """檢查回傳的 flags 結構，確保至少有一個 flag 且包含 `enabled` 欄位"""
    r = requests.get(f"{base_url}/api/feature-flags", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flags = j.get('flags') if isinstance(j, dict) else None
    if not flags:
        pytest.skip('No flags available to inspect structure')
    # 取一個 flag 檢查結構
    key = next(iter(flags))
    flag_obj = flags[key]
    assert isinstance(flag_obj, dict)
    assert 'enabled' in flag_obj


def test_put_missing_enabled_requires_validation(base_url, admin_token):
    """如果沒有提供 `enabled` 欄位，API 應該回傳 400（需 admin token）"""
    if not admin_token:
        pytest.skip('ADMIN_TOKEN not set; skipping validation test that requires auth')
    headers = {'Authorization': f"Bearer {admin_token}"}
    r = requests.put(f"{base_url}/api/feature-flags/some_flag", json={}, headers=headers, timeout=5)
    assert r.status_code == 400


def test_toggle_sequence_with_verification(base_url, admin_token):
    """使用 admin token 依序切換一個已知 flag (ENABLE_CHECKOUT_TIMER) 並在每次切換後驗證狀態"""
    if not admin_token:
        pytest.skip('ADMIN_TOKEN not set; skipping authenticated toggle sequence test')
    headers = {'Authorization': f"Bearer {admin_token}"}
    flag_key = 'ENABLE_CHECKOUT_TIMER'

    # 1) 設為 True
    r = requests.put(f"{base_url}/api/feature-flags/{flag_key}", json={'enabled': True}, headers=headers, timeout=5)
    assert r.status_code == 200

    # 取得並驗證
    r = requests.get(f"{base_url}/api/feature-flags/{flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    # 支援多種回傳格式，嘗試從不同欄位取得 enabled
    flag_data = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert isinstance(flag_data, dict)
    assert flag_data.get('enabled') is True

    # 2) 設為 False
    r = requests.put(f"{base_url}/api/feature-flags/{flag_key}", json={'enabled': False}, headers=headers, timeout=5)
    assert r.status_code == 200

    r = requests.get(f"{base_url}/api/feature-flags/{flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flag_data = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert flag_data.get('enabled') is False

    # 3) 再次設為 True
    r = requests.put(f"{base_url}/api/feature-flags/{flag_key}", json={'enabled': True}, headers=headers, timeout=5)
    assert r.status_code == 200

    r = requests.get(f"{base_url}/api/feature-flags/{flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flag_data = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert flag_data.get('enabled') is True
