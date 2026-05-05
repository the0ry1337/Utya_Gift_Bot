# Utya Gift Price Bot

Tracks prices for 24 Telegram gifts across **GetGems**, **Fragment**, **MRKT**, **Portals**, and **Tonnel** simultaneously and highlights the best deal.

---

## Prerequisites

- Python 3.10+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- *(Optional but recommended)* Telegram API credentials for auto token refresh

---

## Quick start

```bash
git clone https://github.com/the0ry1337/Utya_Gift_Bot.git
cd Utya_Gift_Bot
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in at minimum:

```
BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Run:

```bash
python bot.py
```

The bot works immediately for **GetGems** and **Fragment** (no tokens needed).  
MRKT, Portals, and Tonnel show `—` until their tokens are configured.

---

## Token Auto-Refresh (recommended)

Instead of manually updating tokens every 24 hours, the bot can refresh them automatically every 20 hours using **Pyrogram** — a Telegram MTProto client that logs in as your personal account and fetches fresh credentials from each marketplace mini-app.

### Step 1 — Get Telegram API credentials

1. Go to **https://my.telegram.org/apps** and sign in with your phone number.
2. Click **"Create new application"**, fill in any name (e.g. `utya_bot`).
3. Copy your **`api_id`** (a number) and **`api_hash`** (a hex string).

### Step 2 — Add credentials to .env

```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890abcdef12
```

### Step 3 — Create the session (one-time only)

```bash
python setup_auth.py
```

Pyrogram will ask for:
- Your phone number (international format, e.g. `+79001234567`)
- The OTP code Telegram sends you

After entering the code you will see:

```
✅  Session created for John Doe @johndoe
    File: utya_session.session
```

**This step happens only once.** The session file is saved to disk and reused silently on every subsequent run.

### Step 4 — Start the bot normally

```bash
python bot.py
```

You will see in the logs:

```
Pyrogram configured — token auto-refresh is enabled
```

On first start, if any marketplace token is missing, a refresh runs automatically within 15 seconds. After that, tokens are refreshed every 20 hours with no action needed.

> **Security note:** `utya_session.session` contains your Telegram session credentials. Keep it private — it is already listed in `.gitignore` and will never be committed.

---

## Deploying on a Server (systemd)

### 1. Copy files to the server

```bash
scp -r Utya_Gift_Bot user@your-server:/opt/utya_gift_bot
```

### 2. Install dependencies on the server

```bash
ssh user@your-server
cd /opt/utya_gift_bot
pip install -r requirements.txt
```

### 3. Set up the session on the server

If you created `utya_session.session` locally, copy it to the server:

```bash
scp utya_session.session user@your-server:/opt/utya_gift_bot/
```

Or run `python setup_auth.py` directly on the server.

### 4. Create a systemd service

```bash
sudo nano /etc/systemd/system/utya_gift_bot.service
```

```ini
[Unit]
Description=Utya Gift Price Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/utya_gift_bot
EnvironmentFile=/opt/utya_gift_bot/.env
ExecStart=/usr/bin/python3 /opt/utya_gift_bot/bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable utya_gift_bot
sudo systemctl start utya_gift_bot

# Follow logs
sudo journalctl -u utya_gift_bot -f
```

---

## Manual Token Extraction

If you prefer not to use Pyrogram, you can extract tokens manually from your browser. They need to be re-extracted every 24–48 hours.

> Use Chrome or any Chromium-based browser.

---

### MRKT (`MRKT_TOKEN`)

**Website:** https://mrkt.fun

1. Open https://mrkt.fun in your browser.
2. Press **F12** → **Network** tab.
3. In the filter bar type `saling`.
4. Browse to any gift collection — this triggers an API request.
5. Click the `saling` request → **Headers** → **Request Headers**.
6. Find the `Authorization` header. Copy the full value (everything after `Authorization: `).
7. Paste into `.env`:
   ```
   MRKT_TOKEN=<paste here>
   ```

---

### Portals (`PORTALS_TOKEN`)

**Website:** https://portals-market.com

1. Open https://portals-market.com in your browser.
2. Press **F12** → **Network** tab.
3. In the filter bar type `nfts`.
4. Browse any gift listing.
5. Click a request to `portals-market.com/api/nfts/…` → **Headers** → **Request Headers**.
6. Find the `Authorization` header. Its value starts with `tma `.
7. Paste the full value into `.env`:
   ```
   PORTALS_TOKEN=tma eyJhbGci...
   ```

---

### Tonnel (`TONNEL_TOKEN`)

**Website:** https://market.tonnel.network

Tonnel stores its token in **Local Storage**, not in request headers.

1. Open https://market.tonnel.network in your browser.
2. Press **F12** → **Application** tab (Chrome) or **Storage** tab (Firefox).
3. In the left sidebar expand **Local Storage** → click `https://market.tonnel.network`.
4. Find the key **`web-initData`** in the table.
5. Copy the full value and paste into `.env`:
   ```
   TONNEL_TOKEN=<paste here>
   ```

---

## Configuration reference

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Yes | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_API_ID` | For auto-refresh | From [my.telegram.org/apps](https://my.telegram.org/apps) |
| `TELEGRAM_API_HASH` | For auto-refresh | From [my.telegram.org/apps](https://my.telegram.org/apps) |
| `MRKT_TOKEN` | No | JWT from mrkt.fun (auto-refreshed) |
| `PORTALS_TOKEN` | No | `tma …` from portals-market.com (auto-refreshed) |
| `TONNEL_TOKEN` | No | `web-initData` from market.tonnel.network (auto-refreshed) |
| `MRKT_APP_SHORT_NAME` | No | MRKT mini-app short name (default: `market`) |
| `CACHE_TTL` | No | Price cache in seconds (default: `300`) |
