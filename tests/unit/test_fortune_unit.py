import pytest
from app.main import get_fortune, FORTUNES


@pytest.mark.asyncio
async def test_fortune_structure():
    result = await get_fortune()
    assert "id" in result
    assert "fortune" in result
    assert "lucky_number" in result
    assert "lucky_color" in result
    assert "advice" in result


@pytest.mark.asyncio
async def test_fortune_values_are_strings():
    result = await get_fortune()
    assert isinstance(result["fortune"], str)
    assert isinstance(result["lucky_color"], str)
    assert isinstance(result["advice"], str)


@pytest.mark.asyncio
async def test_fortune_id_in_range():
    result = await get_fortune()
    assert 1 <= result["id"] <= 100


@pytest.mark.asyncio
async def test_fortune_content_from_pool():
    result = await get_fortune()
    fortune_texts = [f["fortune"] for f in FORTUNES]
    assert result["fortune"] in fortune_texts
