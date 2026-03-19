import requests, time

def test_health():
    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("ok") is True
