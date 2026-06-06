from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from inquisitool.constants import CAMPAIGNS_COLLECTION


@pytest.fixture
def mock_db():
    """Returns a mock db with a configurable collection mock."""
    col = MagicMock()
    col.insert_one = AsyncMock()
    col.find_one = AsyncMock()
    col.update_one = AsyncMock()
    col.delete_one = AsyncMock()
    col.count_documents = AsyncMock()

    cursor = AsyncMock()
    cursor.to_list = AsyncMock()
    col.find = MagicMock(return_value=cursor)

    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=col)
    return db, col, cursor


# ── campaigns ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_create_campaign(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.insert_one.return_value = MagicMock()

    from inquisitool.db.mongodb import create_campaign

    result = await create_campaign({"campaign_name": "Test"})

    assert "campaign_id" in result
    col.insert_one.assert_called_once()


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_get_campaign(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.find_one.return_value = {"campaign_id": "c1", "_id": "oid1", "campaign_name": "Test"}

    from inquisitool.db.mongodb import get_campaign

    result = await get_campaign("c1")

    assert result["campaign_id"] == "c1"
    assert result["_id"] == "oid1"


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_get_campaign_not_found(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.find_one.return_value = None

    from inquisitool.db.mongodb import get_campaign

    with pytest.raises(ValueError, match="Campaign not found"):
        await get_campaign("missing")


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_update_campaign(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.update_one.return_value = MagicMock(modified_count=1)

    from inquisitool.db.mongodb import update_campaign

    result = await update_campaign("c1", {"campaign_name": "Updated"})

    assert result["modified_count"] == 1


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_update_campaign_not_found(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.update_one.return_value = MagicMock(modified_count=0)

    from inquisitool.db.mongodb import update_campaign

    with pytest.raises(ValueError, match="Campaign not found"):
        await update_campaign("missing", {})


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_delete_campaign(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.delete_one.return_value = MagicMock(deleted_count=1)

    from inquisitool.db.mongodb import delete_campaign

    result = await delete_campaign("c1")

    assert result["deleted_count"] == 1


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_delete_campaign_not_found(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.delete_one.return_value = MagicMock(deleted_count=0)

    from inquisitool.db.mongodb import delete_campaign

    with pytest.raises(ValueError, match="Campaign not found"):
        await delete_campaign("missing")


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_list_campaigns(mock_get_db):
    db = MagicMock()
    mock_get_db.return_value = db
    cursor = MagicMock()
    cursor.to_list = AsyncMock(
        return_value=[
            {"campaign_id": "c1", "_id": "oid1"},
            {"campaign_id": "c2", "_id": "oid2"},
        ]
    )
    db[CAMPAIGNS_COLLECTION].find.return_value.skip.return_value.limit.return_value = cursor

    from inquisitool.db.mongodb import list_campaigns

    result = await list_campaigns()

    assert len(result) == 2
    assert all(isinstance(c["_id"], str) for c in result)


# ── interactions ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_create_interaction(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.count_documents.return_value = 0
    col.insert_one.return_value = MagicMock()

    from inquisitool.db.mongodb import create_interaction

    result = await create_interaction({"user_id": "u1", "campaign_id": "c1"})

    assert "session_id" in result
    assert result["session_number"] == 1


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_get_interaction(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.find_one.return_value = {"session_id": "s1", "answers": []}

    from inquisitool.db.mongodb import get_interaction

    result = await get_interaction("s1")

    assert result["session_id"] == "s1"


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_get_interaction_not_found(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.find_one.return_value = None

    from inquisitool.db.mongodb import get_interaction

    with pytest.raises(ValueError, match="Interaction not found"):
        await get_interaction("missing")


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_update_interaction(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.update_one.return_value = MagicMock(modified_count=1)

    from inquisitool.db.mongodb import update_interaction

    result = await update_interaction("s1", {"answers": ["yes"]})

    assert result["modified_count"] == 1


@pytest.mark.asyncio
@patch("inquisitool.db.mongodb.get_mongodb", new_callable=AsyncMock)
async def test_update_interaction_not_found(mock_get_db, mock_db):
    db, col, _ = mock_db
    mock_get_db.return_value = db
    col.update_one.return_value = MagicMock(modified_count=0)

    from inquisitool.db.mongodb import update_interaction

    with pytest.raises(ValueError, match="Interaction not found"):
        await update_interaction("missing", {})
