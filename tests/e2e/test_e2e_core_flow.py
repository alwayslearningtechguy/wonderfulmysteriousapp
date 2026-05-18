def test_full_user_flow_saves_and_reads_favorites(client):
    # Weather
    r = client.get("/api/weather")
    assert r.status_code == 200
    weather = r.json()

    # Insight
    r = client.get("/api/insight")
    assert r.status_code == 200
    insight = r.json()

    # Fortune
    r = client.get("/api/fortune")
    assert r.status_code == 200
    fortune = r.json()

    # Submit
    payload = {
        "user": "e2e-test-user",
        "data": {
            "weather": weather,
            "insight": insight["insight"],
            "fortune": fortune["fortune"],
        }
    }
    
    r = client.post("/api/submit", json=payload)
    assert r.status_code == 201


    # Favorites
    r = client.get("/api/favorites")
    assert r.status_code == 200
    favorites = r.json()
    assert any(f.get("fortune") == fortune["fortune"] for f in favorites)
