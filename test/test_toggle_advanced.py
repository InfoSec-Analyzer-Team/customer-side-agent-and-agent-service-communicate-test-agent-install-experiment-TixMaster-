import os
import uuid
import time
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.fixture
def existing_flag_key():
    # Use a flag that exists in DB by default
    return 'ENABLE_CHECKOUT_TIMER'


@pytest.fixture
def require_admin(admin_token):
    if not admin_token:
        pytest.skip('ADMIN_TOKEN not set; skipping admin-requiring tests')
    return admin_token


def _headers(token):
    return {'Authorization': f"Bearer {token}"} if token else {}


@pytest.mark.toggle
def test_create_and_get_flag(base_url, require_admin, existing_flag_key):
    """使用 admin token 建立一個臨時 flag，然後讀取確認內容，最後嘗試將其重設為 False"""
    headers = _headers(require_admin)
    # create (PUT should create or update)
    r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': True, 'description': 'temporary test flag'}, headers=headers, timeout=5)
    assert r.status_code == 200, f"create/update failed: {r.status_code} {r.text}"

    # verify GET
    r = requests.get(f"{base_url}/api/feature-flags/{existing_flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flag = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert isinstance(flag, dict)
    assert flag.get('enabled') is True

    # cleanup: set false
    r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': False}, headers=headers, timeout=5)
    assert r.status_code == 200
    r = requests.get(f"{base_url}/api/feature-flags/{existing_flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flag = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert flag.get('enabled') is False


@pytest.mark.toggle
def test_non_admin_cannot_modify(base_url, existing_flag_key):
    """在沒有 token 的情況下，嘗試修改應得到 401/403（或 200 if API allows）；但我們希望檢查最小安全性：不會以 200 表示未授權改動。"""
    r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': True}, timeout=5)
    assert r.status_code in (401, 403, 404)


@pytest.mark.toggle
def test_invalid_payloads(base_url, require_admin, existing_flag_key):
    """測試多種不合法 payload，確保 API 對錯誤輸入回傳 4xx"""
    headers = _headers(require_admin)
    cases = [
        ({}, 400),  # missing enabled (if API validates)
        ({'enabled': 'string'}, 400),
        ({'enabled': None}, 400),
        ({'enabled': 123}, 400),
    ]
    for payload, expected in cases:
        r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json=payload, headers=headers, timeout=5)
        # Accept 401/403 when authorization fails; otherwise expect 400
        if r.status_code in (401, 403):
            continue
        assert 400 <= r.status_code < 500, f"payload {payload} returned {r.status_code}, body: {r.text}"


@pytest.mark.toggle
def test_concurrent_toggle_stress(base_url, require_admin, existing_flag_key):
    """並發執行多次切換（True/False），確保沒有 5xx 錯誤並最終成功回傳 200。"""
    headers = _headers(require_admin)
    # ensure flag exists
    r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': False}, headers=headers, timeout=5)
    assert r.status_code == 200

    def toggle(i):
        val = bool(i % 2)
        rr = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': val}, headers=headers, timeout=10)
        return rr.status_code, rr.text[:200]

    errors = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(toggle, i) for i in range(40)]
        for fut in as_completed(futures):
            code, body = fut.result()
            if code >= 500:
                errors.append((code, body))

    assert not errors, f"Server errors during concurrent toggles: {errors}"

    # final read
    r = requests.get(f"{base_url}/api/feature-flags/{existing_flag_key}", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flag = j.get('flag') if isinstance(j, dict) and 'flag' in j else j
    assert isinstance(flag, dict)
    assert 'enabled' in flag


@pytest.mark.toggle
def test_dynamic_flag_list_contains_created(base_url, require_admin, existing_flag_key):
    """在建立 flag 後，list endpoint 應包含該 flag"""
    headers = _headers(require_admin)
    # create
    r = requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': True}, headers=headers, timeout=5)
    if r.status_code in (401, 403):
        pytest.skip('Cannot create flag; auth required and ADMIN_TOKEN may be invalid')

    assert r.status_code == 200
    # list
    r = requests.get(f"{base_url}/api/feature-flags", timeout=5)
    assert r.status_code == 200
    j = r.json()
    flags = j.get('flags') if isinstance(j, dict) else {}
    assert existing_flag_key in flags

    # cleanup set false
    requests.put(f"{base_url}/api/feature-flags/{existing_flag_key}", json={'enabled': False}, headers=headers, timeout=5)
