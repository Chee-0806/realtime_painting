import asyncio
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.websockets import WebSocketState

from app.connection_manager import ConnectionManager

@pytest.mark.asyncio
async def test_get_latest_data_drains_queue():
    mgr = ConnectionManager()
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
    mgr = ConnectionManager()
    user_id = uuid4()
    mgr.active_connections[user_id] = {
        "websocket": None,
        "queue": asyncio.Queue(),
    }

    latest = await mgr.get_latest_data(user_id)
    assert latest is None


@pytest.mark.asyncio
async def test_receive_message_binary_packets_are_parsed():
    mgr = ConnectionManager()
    user_id = uuid4()

    payload = {"status": "next_frame", "params": {"prompt": "hi"}}
    json_bytes = json.dumps(payload).encode("utf-8")
    packet = len(json_bytes).to_bytes(4, byteorder="big") + json_bytes + b"image-bytes"

    mgr.active_connections[user_id] = {
        "websocket": _DummyWebSocket({"bytes": packet}),
        "queue": asyncio.Queue(),
    }

    data, image = await mgr.receive_message(user_id)
    assert data["status"] == "next_frame"
    assert data["prompt"] == "hi"
    assert image == b"image-bytes"


@pytest.mark.asyncio
async def test_receive_message_json_packets_are_parsed():
    mgr = ConnectionManager()
    user_id = uuid4()

    payload = json.dumps({"status": "next_frame", "params": {"strength": 0.5}})
    mgr.active_connections[user_id] = {
        "websocket": _DummyWebSocket({"text": payload}),
        "queue": asyncio.Queue(),
    }

    data, image = await mgr.receive_message(user_id)
    assert data["strength"] == 0.5
    assert image == b""


@pytest.mark.asyncio
async def test_all_strategy_processes_queue_in_order():
    mgr = ConnectionManager(drain_strategy="all")
    user_id = uuid4()

    mgr.active_connections[user_id] = {
        "websocket": None,
        "queue": asyncio.Queue(),
    }

    await mgr.update_data(user_id, SimpleNamespace(value=1))
    await mgr.update_data(user_id, SimpleNamespace(value=2))

    first = await mgr.get_latest_data(user_id)
    second = await mgr.get_latest_data(user_id)
    assert getattr(first, "value") == 1
    assert getattr(second, "value") == 2


@pytest.mark.asyncio
async def test_all_strategy_blocks_until_data_available():
    mgr = ConnectionManager(drain_strategy="all")
    user_id = uuid4()

    mgr.active_connections[user_id] = {
        "websocket": None,
        "queue": asyncio.Queue(),
    }

    async def delayed_update():
        await asyncio.sleep(0.01)
        await mgr.update_data(user_id, SimpleNamespace(value="ready"))

    asyncio.create_task(delayed_update())

    result = await asyncio.wait_for(
        mgr.get_latest_data(user_id, wait=True), timeout=0.5
    )

    assert getattr(result, "value") == "ready"


class _DummyWebSocket:
    def __init__(self, message):
        self._message = message
        self.client_state = WebSocketState.CONNECTED

    async def receive(self):
        return self._message
