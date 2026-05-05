# Utya Gift Price Bot

Tracks prices for 24 Telegram gifts across **GetGems**, **Fragment**, **MRKT**, **Portals**, and **Tonnel** simultaneously and highlights the best deal.

---

## Prerequisites

- Python 3.10+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- *(Optional)* Auth tokens for MRKT, Portals, Tonnel — see [Extracting Tokens](#extracting-marketplace-tokens)

---

## Deployment

### 1. Clone and set up

```bash
git clone https://github.com/the0ry1337/Utya_Gift_Bot.git
cd Utya_Gift_Bot
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
nano .env   # or use any text editor
```

Fill in at minimum:

```
BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Add marketplace tokens if you have them (see below). The bot works without them — it will show `—` for platforms where no token is set.

### 3. Run

```bash
python bot.py
```

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

### 3. Create a systemd service

```bash
sudo nano /etc/systemd/system/utya_gift_bot.service
```

Paste this (adjust `User` and paths as needed):

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

### 4. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable utya_gift_bot
sudo systemctl start utya_gift_bot

# Check logs
sudo journalctl -u utya_gift_bot -f
```

---

## Extracting Marketplace Tokens

All three tokens are **Telegram Web App auth strings** extracted from the browser while the marketplace mini-app is open. They are valid for **at least 24 hours** and can be refreshed by repeating the steps below.

> **Use Chrome or any Chromium-based browser for these steps.**

---

### MRKT (`MRKT_TOKEN`)

**Website:** https://mrkt.fun

1. Open https://mrkt.fun in your browser.
2. Press **F12** to open DevTools, then go to the **Network** tab.
3. In the filter bar, type `saling` to filter requests.
4. In the MRKT interface, browse to any gift collection — this will trigger an API request.
5. Click on the request named `saling` in the Network tab.
6. Go to the **Headers** sub-tab and scroll to **Request Headers**.
7. Find the `Authorization` header. Copy its full value (it looks like a long string, **without** the word `Authorization:`).
8. Paste it into `.env`:
   ```
   MRKT_TOKEN=<paste here>
   ```

**Tip:** If no request appears, refresh the MRKT page while the Network tab is open.

---

### Portals (`PORTALS_TOKEN`)

**Website:** https://portals-market.com

1. Open https://portals-market.com in your browser.
2. Press **F12** → **Network** tab.
3. In the filter bar, type `nfts` to filter requests.
4. Browse any gift listing — this triggers an API call.
5. Click on a request to `portals-market.com/api/nfts/...` in the list.
6. In the **Headers** sub-tab, find the `Authorization` header in **Request Headers**.
7. Copy its full value. It starts with `tma ` followed by a long encoded string.
8. Paste it into `.env`:
   ```
   PORTALS_TOKEN=tma <paste the rest here>
   ```

---

### Tonnel (`TONNEL_TOKEN`)

**Website:** https://market.tonnel.network

Tonnel stores its auth token in the browser's **Local Storage** rather than in request headers.

1. Open https://market.tonnel.network in your browser.
2. Press **F12** → **Application** tab (in Chrome) or **Storage** tab (in Firefox).
3. In the left sidebar expand **Local Storage** → click on `https://market.tonnel.network`.
4. In the table, find the key named **`web-initData`**.
5. Copy the full value from the **Value** column.
6. Paste it into `.env`:
   ```
   TONNEL_TOKEN=<paste here>
   ```

---

## Token Refresh

Tokens expire after some time (typically 24–48 hours). When a platform starts returning errors, repeat the extraction steps for that platform and update `.env`.

After updating `.env`, restart the bot:

```bash
# Local
Ctrl+C, then python bot.py again

# systemd server
sudo systemctl restart utya_gift_bot
```

---

## Configuration reference

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Yes | From [@BotFather](https://t.me/BotFather) |
| `MRKT_TOKEN` | No | Authorization header from mrkt.fun |
| `PORTALS_TOKEN` | No | Authorization header from portals-market.com |
| `TONNEL_TOKEN` | No | `web-initData` value from market.tonnel.network |
| `CACHE_TTL` | No | Price cache lifetime in seconds (default: `300`) |
