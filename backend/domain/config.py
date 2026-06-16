from functools import lru_cache
from urllib.parse import urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_user: str
    db_pass: str
    db_name: str
    db_host: str
    db_port: int

    jwt_secret: str
    jwt_expire_minutes: int
    jwt_refresh_expire_days: int
    fernet_key: str

    seed_demo_data: bool
    enable_docs: bool = False
    frontend_url: str = "http://localhost:5173"

    email_from: str
    resend_api_key: str

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.3-70b-instruct"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro_monthly: str = ""
    stripe_price_pro_yearly: str = ""

    google_client_id: str = ""

    telegram_bot_token: str = ""
    telegram_owner_chat_id: str = ""
    telegram_review_chat_id: str = ""

    proxy_pool_csv: str = ""

    seed_binance_key: str = ""
    seed_binance_secret: str = ""
    seed_bybit_key: str = ""
    seed_bybit_secret: str = ""
    seed_okx_key: str = ""
    seed_okx_secret: str = ""
    seed_okx_passphrase: str = ""
    seed_bitget_key_1: str = ""
    seed_bitget_secret_1: str = ""
    seed_bitget_passphrase_1: str = ""
    seed_bitget_key_2: str = ""
    seed_bitget_secret_2: str = ""
    seed_bitget_passphrase_2: str = ""

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def billing_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_owner_chat_id)

    @property
    def proxy_pool(self) -> list[str]:
        return [p.strip() for p in self.proxy_pool_csv.split(",") if p.strip()]

    @property
    def proxy_ips(self) -> list[str]:
        return [host for p in self.proxy_pool if (host := urlparse(p).hostname)]

    @property
    def whitelist_hint(self) -> str:
        ips = self.proxy_ips
        return ", ".join(ips) if ips else "our server's IP"

    def seed_credentials(self) -> dict[str, tuple[str, str, str | None]]:
        pairs = {
            "binance": (self.seed_binance_key, self.seed_binance_secret, None),
            "bybit": (self.seed_bybit_key, self.seed_bybit_secret, None),
            "okx": (self.seed_okx_key, self.seed_okx_secret, self.seed_okx_passphrase or None),
            "bitget1": (self.seed_bitget_key_1, self.seed_bitget_secret_1, self.seed_bitget_passphrase_1 or None),
            "bitget2": (self.seed_bitget_key_2, self.seed_bitget_secret_2, self.seed_bitget_passphrase_2 or None)
        }
        return {slot: c for slot, c in pairs.items() if c[0] and c[1]}

@lru_cache
def get_config() -> Config:
    return Config()  # type: ignore[call-arg]
