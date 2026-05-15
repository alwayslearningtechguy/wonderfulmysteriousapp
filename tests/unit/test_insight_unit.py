import pytest
from app.main import get_insight, INSIGHTS


@pytest.mark.asyncio
async def test_insight_default_topic():
    result = await get_insight()
    assert "id" in result
    assert "topic" in result
    assert "insight" in result
    assert "available_topics" in result
    assert result["topic"] == "general"
    assert isinstance(result["insight"], str)
    assert len(result["insight"]) > 0


@pytest.mark.asyncio
async def test_insight_known_topic():
    result = await get_insight(topic="technology")
    assert result["topic"] == "technology"
    assert result["insight"] in INSIGHTS["technology"]


@pytest.mark.asyncio
async def test_insight_unknown_topic_falls_back_to_general():
    # Topics not in INSIGHTS fall back to "general" pool
    result = await get_insight(topic="AI")
    assert result["topic"] == "general"
    assert result["insight"] in INSIGHTS["general"]


@pytest.mark.asyncio
async def test_insight_available_topics_listed():
    result = await get_insight()
    assert set(result["available_topics"]) == set(INSIGHTS.keys())
