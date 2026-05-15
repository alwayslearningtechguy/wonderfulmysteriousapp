def test_rate_limit_enforced(client):
    # First 100 requests allowed
    for _ in range(100):
        res = client.get("/api/weather")
        assert res.status_code == 200

    # 101th request blocked
    res = client.get("/api/weather")
    assert res.status_code == 429
