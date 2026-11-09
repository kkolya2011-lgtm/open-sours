import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    bot_token: str
    hibp_key: str
    ipinfo_token: str
    serper_key: str
    emailrep_key: str
    numverify_key: str
    github_token: str
    youtube_key: str
    timeout: float
    cache_ttl: int
    rate_limit: int
    sherlock_concurrency: int

cfg = Config(
    bot_token=os.getenv("BOT_TOKEN", ""),
    hibp_key=os.getenv("HIBP_API_KEY", ""),
    ipinfo_token=os.getenv("IPINFO_TOKEN", ""),
    serper_key=os.getenv("SERPER_API_KEY", ""),
    emailrep_key=os.getenv("EMAILREP_KEY", ""),
    numverify_key=os.getenv("NUMVERIFY_API_KEY", ""),
    github_token=os.getenv("GITHUB_TOKEN", ""),
    youtube_key=os.getenv("YOUTUBE_API_KEY", ""),
    timeout=float(os.getenv("HTTP_TIMEOUT", "15")),
    cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
    rate_limit=int(os.getenv("RATE_LIMIT", "10")),
    sherlock_concurrency=int(os.getenv("SHERLOCK_CONCURRENCY", "6")),
)
