import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
MRKT_TOKEN: str = os.getenv("MRKT_TOKEN", "")
PORTALS_TOKEN: str = os.getenv("PORTALS_TOKEN", "")
TONNEL_TOKEN: str = os.getenv("TONNEL_TOKEN", "")
CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
