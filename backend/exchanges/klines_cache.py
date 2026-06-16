from collections import OrderedDict

class KlinesCache:
    _DEFAULT_CAPACITY = 50_000

    def __init__(self, capacity=None):
        self._capacity = capacity or self._DEFAULT_CAPACITY
        self._store = OrderedDict()

    def get(self, exchange, market_type, symbol, interval, time_ms):
        key = (exchange, market_type, symbol, interval, time_ms)
        kline = self._store.get(key)
        if kline is None:
            return None
        self._store.move_to_end(key)
        return kline

    def put(self, exchange, market_type, symbol, interval, kline):
        key = (exchange, market_type, symbol, interval, kline.time_ms)
        self._store[key] = kline
        self._store.move_to_end(key)
        while len(self._store) > self._capacity:
            self._store.popitem(last=False)

    def put_many(self, exchange, market_type, symbol, interval, klines):
        for k in klines:
            self.put(exchange, market_type, symbol, interval, k)

    def size(self):
        return len(self._store)

    def clear(self):
        self._store.clear()
