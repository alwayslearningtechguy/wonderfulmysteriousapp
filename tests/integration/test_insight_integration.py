def test_insight_default(client):
    res = client.get("/api/insight")
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "topic" in data
    assert "insight" in data
    assert "available_topics" in data
    assert data["topic"] == "general"
    assert isinstance(data["insight"], str)


def test_insight_known_topic(client):
    res = client.get("/api/insight?topic=productivity")
    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == "productivity"
    assert isinstance(data["insight"], str)
    assert len(data["insight"]) > 0


def test_insight_unknown_topic_falls_back(client):
    # "finance" is not a known topic — should fall back to "general"
    res = client.get("/api/insight?topic=finance")
    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == "general"
    assert isinstance(data["insight"], str)


def test_insight_available_topics_present(client):
    res = client.get("/api/insight")
    assert res.status_code == 200
    topics = res.json()["available_topics"]
    assert "general" in topics
    assert "technology" in topics
    assert "productivity" in topics
    assert "leadership" in topics
    assert "creativity" in topics
