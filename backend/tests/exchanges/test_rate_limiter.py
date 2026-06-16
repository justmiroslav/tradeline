import time

from domain.enums import Exchange
from exchanges.proxy_pool import ProxyRouter
from exchanges.rate_limiter import TokenBucket
from exchanges.types import BucketSpec

class TestTokenBucket:
    async def test_burst_within_capacity_then_blocks_when_drained(self):
        b = TokenBucket(BucketSpec(capacity=2, refill_per_sec=20))
        await b.acquire(1)
        await b.acquire(1)
        t0 = time.monotonic()
        await b.acquire(1)
        assert 0.04 < time.monotonic() - t0 < 0.20

    async def test_weight_consumes_multiple_tokens(self):
        b = TokenBucket(BucketSpec(capacity=20, refill_per_sec=20))
        await b.acquire(15)
        t0 = time.monotonic()
        await b.acquire(15)
        assert time.monotonic() - t0 >= 0.45

    async def test_try_acquire_true_then_false_when_drained(self):
        b = TokenBucket(BucketSpec(capacity=1, refill_per_sec=1))
        assert await b.try_acquire(1) is True
        assert await b.try_acquire(1) is False

    async def test_penalize_blocks_acquire_and_try_acquire(self):
        b = TokenBucket(BucketSpec(capacity=10, refill_per_sec=100))
        b.penalize(0.10)
        assert await b.try_acquire(1) is False
        t0 = time.monotonic()
        await b.acquire(1)
        assert time.monotonic() - t0 >= 0.09

    async def test_observe_remaining_and_used_headers(self):
        rem = TokenBucket(BucketSpec(100, 10, header_remaining_key="X-Remaining"))
        rem.observe({"X-Remaining": "42"})
        assert rem._tokens == 42

        used = TokenBucket(BucketSpec(6000, 100, header_used_key="X-MBX-USED-WEIGHT-1M"))
        used.snap(6000)
        used.observe({"X-MBX-USED-WEIGHT-1M": "5500"})
        assert used._tokens == 500

    async def test_observe_bad_input_is_a_noop(self):
        b = TokenBucket(BucketSpec(100, 10, header_remaining_key="X-Remaining"))
        before = b._tokens
        b.observe({"X-Remaining": "n/a"})
        b.observe({"Other": "1"})
        assert b._tokens == before

_FAST = {Exchange.BINANCE: {"spot": BucketSpec(2, 1000)}}
_TIGHT = {Exchange.BINANCE: {"spot": BucketSpec(1, 1), "fut": BucketSpec(5, 1000, per_ip=False)}}

class TestProxyRouter:
    async def test_direct_connection_without_a_pool(self):
        r = ProxyRouter([], _FAST)
        proxy, bucket = await r.acquire(Exchange.BINANCE, "spot", 1)
        assert proxy is None and isinstance(bucket, TokenBucket)
        assert r.next_ws() is None

    async def test_single_proxy_is_used(self):
        r = ProxyRouter(["http://p0"], _FAST)
        proxy, _ = await r.acquire(Exchange.BINANCE, "spot", 1)
        assert proxy == "http://p0"

    async def test_saturated_lane_escalates_to_the_next_proxy(self):
        r = ProxyRouter(["http://p0", "http://p1"], _TIGHT)
        first, _ = await r.acquire(Exchange.BINANCE, "spot", 1)
        second, _ = await r.acquire(Exchange.BINANCE, "spot", 1)
        assert {first, second} == {"http://p0", "http://p1"}
        assert r.snapshot()["binance:spot"] == 2

    async def test_other_lanes_keep_their_assignment(self):
        r = ProxyRouter(["http://p0", "http://p1"], _TIGHT)
        await r.acquire(Exchange.BINANCE, "spot", 1)
        await r.acquire(Exchange.BINANCE, "spot", 1)
        await r.acquire(Exchange.BINANCE, "fut", 1)
        assert r.snapshot()["binance:spot"] == 2
        assert r.snapshot()["binance:fut"] == 1

    async def test_per_key_pool_throttles_globally_without_escalating(self):
        configs = {Exchange.BITGET: {"account": BucketSpec(10, 1000, per_ip=False)}}
        r = ProxyRouter(["http://p0", "http://p1"], configs)
        proxies = set()
        for _ in range(4):
            proxy, _ = await r.acquire(Exchange.BITGET, "account", 1)
            proxies.add(proxy)
        assert r.snapshot()["bitget:account"] == 1
        assert proxies == {"http://p0", "http://p1"}

    async def test_next_ws_round_robins_the_pool(self):
        r = ProxyRouter(["http://p0", "http://p1"], _FAST)
        assert [r.next_ws() for _ in range(3)] == ["http://p0", "http://p1", "http://p0"]
