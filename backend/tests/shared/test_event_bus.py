from uuid import uuid4

from shared.event_bus import EventBus

class TestEventBus:
    async def test_publish_reaches_subscriber(self):
        bus = EventBus()
        uid = uuid4()
        async with bus.subscribe(uid) as q:
            bus.publish(uid, "trade", {"x": 1})
            assert q.get_nowait() == {"type": "trade", "data": {"x": 1}}

    async def test_overflow_evicts_oldest_and_keeps_newest(self):
        bus = EventBus()
        uid = uuid4()
        async with bus.subscribe(uid) as q:
            for i in range(EventBus._QUEUE_MAX + 5):
                bus.publish(uid, "tick", {"i": i})
            first = q.get_nowait()
            assert first["data"]["i"] == 5
            last = None
            while not q.empty():
                last = q.get_nowait()
            assert last["data"]["i"] == EventBus._QUEUE_MAX + 4

    async def test_publish_without_subscribers_is_noop(self):
        EventBus().publish(uuid4(), "trade", {})

    async def test_unsubscribed_queue_no_longer_receives(self):
        bus = EventBus()
        uid = uuid4()
        async with bus.subscribe(uid) as q:
            pass
        bus.publish(uid, "trade", {})
        assert q.empty()
