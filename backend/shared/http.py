import aiohttp

def create_rest_session() -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=20,
        ttl_dns_cache=300,
        enable_cleanup_closed=True
    )
    return aiohttp.ClientSession(connector=connector, raise_for_status=False)

def create_ws_session() -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(
        limit=50,
        force_close=False,
        enable_cleanup_closed=True
    )
    return aiohttp.ClientSession(connector=connector, raise_for_status=False)
