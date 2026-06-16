from shared.rate_limit import RateLimiter

class TestRateLimiter:
    def test_allows_within_limit_then_blocks(self):
        limiter = RateLimiter({("POST", "/auth/login"): (3, 60)})
        for _ in range(3):
            assert limiter.allow("POST", "/auth/login", "1.1.1.1", now=100.0) is True
        assert limiter.allow("POST", "/auth/login", "1.1.1.1", now=100.0) is False

    def test_window_expiry_resets_the_counter(self):
        limiter = RateLimiter({("POST", "/auth/login"): (1, 60)})
        assert limiter.allow("POST", "/auth/login", "1.1.1.1", now=100.0)
        assert not limiter.allow("POST", "/auth/login", "1.1.1.1", now=159.0)
        assert limiter.allow("POST", "/auth/login", "1.1.1.1", now=161.0)

    def test_ips_are_counted_independently(self):
        limiter = RateLimiter({("POST", "/auth/login"): (1, 60)})
        assert limiter.allow("POST", "/auth/login", "1.1.1.1", now=100.0)
        assert limiter.allow("POST", "/auth/login", "2.2.2.2", now=100.0)
        assert not limiter.allow("POST", "/auth/login", "1.1.1.1", now=100.0)

    def test_unlisted_routes_are_unlimited(self):
        limiter = RateLimiter({("POST", "/auth/login"): (1, 60)})
        for _ in range(100):
            assert limiter.allow("GET", "/analytics/overview", "1.1.1.1", now=100.0)

    def test_rule_matches_by_method_and_normalized_path(self):
        limiter = RateLimiter({("POST", "/api-keys"): (1, 60)})
        assert limiter.allow("POST", "/api-keys/", "1.1.1.1", now=100.0)
        assert not limiter.allow("POST", "/api-keys", "1.1.1.1", now=100.0)
        assert limiter.allow("GET", "/api-keys", "1.1.1.1", now=100.0)
