import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

# Marketplace auth tokens (optional — auto-refreshed if Pyrogram is configured)
MRKT_TOKEN: str = os.getenv("MRKT_TOKEN", "")
PORTALS_TOKEN: str = os.getenv("PORTALS_TOKEN", "")
TONNEL_TOKEN: str = os.getenv("TONNEL_TOKEN", "")

# Pyrogram credentials for auto token refresh (get from https://my.telegram.org/apps)
TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")

# MRKT mini-app short name (from t.me/main_mrkt_bot/<short_name>)
# If MRKT token refresh fails, check the actual URL and update this value.
MRKT_APP_SHORT_NAME: str = os.getenv("MRKT_APP_SHORT_NAME", "market")

CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
