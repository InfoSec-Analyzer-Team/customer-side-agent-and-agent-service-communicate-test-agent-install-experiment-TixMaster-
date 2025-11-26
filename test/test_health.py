import requests


def test_health_ok(base_url):
    r = requests.get(f"{base_url}/health", timeout=5)
    assert r.status_code == 200
    j = r.json()
    assert j.get('status', '').upper() == 'OK'
