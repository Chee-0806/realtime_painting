import asyncio
import pytest
from uuid import uuid4
from app.api.realtime_connection_manager import RealtimeConnectionManager
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_get_latest_data_drains_queue():
    mgr = RealtimeConnectionManager()
    user_id = uuid4()

    # simulate connect by creating internal structure
    mgr.active_connections[user_id] = {
        "websocket": None,
        "queue": asyncio.Queue(),
    }

    # put several items
    await mgr.update_data(user_id, SimpleNamespace(value=1))
    await mgr.update_data(user_id, SimpleNamespace(value=2))
    await mgr.update_data(user_id, SimpleNamespace(value=3))

    latest = await mgr.get_latest_data(user_id)
    assert latest is not None
    assert getattr(latest, "value", None) == 3

    # subsequent call should return None (queue was drained)
    latest2 = await mgr.get_latest_data(user_id)
    assert latest2 is None

@pytest.mark.asyncio
async def test_get_latest_data_empty_returns_none():
    mgr = RealtimeConnectionManager()
    user_id = uuid4()
    mgr.active_connections[user_id] = {
        "websocket": None,
        "queue": asyncio.Queue(),
    }

    latest = await mgr.get_latest_data(user_id)
    assert latest is None
