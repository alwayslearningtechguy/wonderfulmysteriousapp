def test_fortune(client):
    res = client.get("/api/fortune")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "fortune" in data
    assert "lucky_number" in data
    assert "lucky_color" in data
    assert "advice" in data


def test_fortune_field_types(client):
    res = client.get("/api/fortune")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["fortune"], str)
    assert isinstance(data["lucky_number"], int)
    assert isinstance(data["lucky_color"], str)
    assert isinstance(data["advice"], str)


def test_fortune_non_empty_strings(client):
    res = client.get("/api/fortune")
    assert res.status_code == 200
    data = res.json()
    assert len(data["fortune"]) > 0
    assert len(data["lucky_color"]) > 0
    assert len(data["advice"]) > 0
