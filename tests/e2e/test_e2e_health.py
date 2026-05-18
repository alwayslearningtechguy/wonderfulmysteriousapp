import pytest

@pytest.mark.parametrize("path", [
    "/api/weather",
    "/api/insight",
    "/api/fortune"
])
def test_core_api_endpoints_are_healthy(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
