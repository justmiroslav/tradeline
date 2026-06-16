import logging, sys
from datetime import datetime, timezone, timedelta

class _Fmt(logging.Formatter):
    C = {
        "INFO": "\033[32m", "WARNING": "\033[33m",
        "ERROR": "\033[31m", "R": "\033[0m"
    }

    def __init__(self, fmt: str, tz_offset: int = 2) -> None:
        super().__init__(fmt)
        self.timezone = timezone(timedelta(hours=tz_offset))

    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, tz=self.timezone).strftime("%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        c = self.C.get(record.levelname, "")
        if c:
            record.msg = f"{c}{record.msg}{self.C['R']}"
        return super().format(record)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_Fmt("%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s"))

logger = logging.getLogger("trading_journal")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False

def brief(error: Exception, limit: int = 300) -> str:
    text = " ".join(str(error).split())
    return f"{type(error).__name__}: {text[:limit]}"
