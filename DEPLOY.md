# Deployment Guide

Complete guide for deploying the Utya Gift Price Bot to a free cloud platform.

---

## Free Hosting Options

| Platform | Free Tier | Persistent Storage | Ease | Best For |
|---|---|---|---|---|
| [Oracle Cloud](#1-oracle-cloud-always-free) | 2 VMs forever, no expiry | ✅ Yes | Medium | Best overall — true VPS, no limits |
| [Railway](#2-railway) | $5 credit/month (~500 h) | ⚠️ Ephemeral | Easy | Quickest setup, Git-based deploy |
| [Fly.io](#3-flyio) | 3 micro VMs + 3 GB volume | ✅ Yes (volume) | Medium | Good free tier, Docker-based |
| [Render](#4-render) | 750 h/month | ⚠️ Ephemeral | Easy | Simple but service sleeps when idle |

**Recommendation:** Use **Oracle Cloud** for a permanent 24/7 deployment. Use **Railway** if you want the fastest setup.

---

## Before You Start — Local Preparation

These steps must be done **on your own computer** before deploying to any platform. You only do this once.

### 1. Get a Telegram Bot Token

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, follow the prompts.
3. Copy the token (looks like `123456789:AAFxxxxxxxx`).

### 2. Get Telegram API Credentials

1. Go to **https://my.telegram.org/apps** and sign in with your phone number.
2. Click **"API development tools"** → **"Create new application"**.
3. Fill in any app name (e.g. `utya`), platform: Other.
4. Copy your **`api_id`** (a number) and **`api_hash`** (a hex string).

### 3. Clone the repo and install dependencies

```bash
git clone https://github.com/the0ry1337/Utya_Gift_Bot.git
cd Utya_Gift_Bot
pip install -r requirements.txt
```

### 4. Create a Pyrogram session

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
BOT_TOKEN=123456789:AAFxxxxxxxx
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
```

Then run:

```bash
python setup_auth.py
```

Telegram will send you an OTP. Enter it. You will see:

```
✅  Session created for John Doe @johndoe
    File: utya_session.session

────────────────────────────────────────────────────────────
SESSION_STRING (copy this for cloud platforms):
────────────────────────────────────────────────────────────
BQHMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
────────────────────────────────────────────────────────────
```

**Copy and save both:**
- The `utya_session.session` **file** — for VPS platforms (Oracle Cloud, Fly.io with volume).
- The **`SESSION_STRING`** value — for platforms without persistent storage (Railway, Render).

---

## 1. Oracle Cloud (Always Free)

**What you get for free:** 2 AMD VMs with 1 GB RAM each, or up to 4 ARM cores + 24 GB RAM (Ampere). No expiry, no credit card charges as long as you stay within the Always Free tier.

### Step 1 — Create an account

1. Go to **https://cloud.oracle.com** and sign up.
2. Choose your home region (pick one close to you — it cannot be changed later).
3. You need a credit/debit card to verify identity — you will **not** be charged on the Always Free tier.

### Step 2 — Create a VM

1. In the Oracle Cloud Console go to **Compute → Instances → Create Instance**.
2. Change the image to **Canonical Ubuntu 22.04**.
3. Under **Shape**, click **Change shape** → **Ampere** (ARM, free) or **VM.Standard.E2.1.Micro** (AMD, free).
4. Under **Add SSH keys**, paste your public SSH key (generate one with `ssh-keygen` if you don't have one).
5. Click **Create**.

### Step 3 — Open firewall for the bot

Oracle Cloud blocks all incoming traffic by default. Your bot only makes outgoing connections, so you do **not** need to open any ports — skip this step.

### Step 4 — Connect to the VM

```bash
ssh ubuntu@<YOUR_VM_PUBLIC_IP>
```

### Step 5 — Install Python 3.11

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip git
```

### Step 6 — Clone the repo and set up

```bash
git clone https://github.com/the0ry1337/Utya_Gift_Bot.git
cd Utya_Gift_Bot
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Fill in all variables: `BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`.

### Step 7 — Upload the session file

From your **local machine**:

```bash
scp utya_session.session ubuntu@<YOUR_VM_PUBLIC_IP>:/home/ubuntu/Utya_Gift_Bot/
```

### Step 8 — Create a systemd service

```bash
sudo nano /etc/systemd/system/utya_gift_bot.service
```

Paste:

```ini
[Unit]
Description=Utya Gift Price Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Utya_Gift_Bot
EnvironmentFile=/home/ubuntu/Utya_Gift_Bot/.env
ExecStart=/usr/bin/python3 /home/ubuntu/Utya_Gift_Bot/bot.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 9 — Start the bot

```bash
sudo systemctl daemon-reload
sudo systemctl enable utya_gift_bot
sudo systemctl start utya_gift_bot
```

Check it's running:

```bash
sudo systemctl status utya_gift_bot
sudo journalctl -u utya_gift_bot -f
```

### Updating the bot later

```bash
cd ~/Utya_Gift_Bot
git pull
sudo systemctl restart utya_gift_bot
```

---

## 2. Railway

**What you get for free:** $5 of compute credit per month, which covers roughly 500 hours of a small service — enough for one bot running 24/7.

Railway uses an **ephemeral filesystem** (files reset on every deploy), so you must use `SESSION_STRING` instead of the `.session` file.

### Step 1 — Create an account

1. Go to **https://railway.app** and sign up with GitHub.

### Step 2 — Push your code to GitHub

If the repo is not yet on your GitHub:

```bash
git remote set-url origin https://github.com/YOUR_USERNAME/Utya_Gift_Bot.git
git push -u origin main
```

### Step 3 — Create a new project

1. In Railway dashboard click **"New Project"**.
2. Select **"Deploy from GitHub repo"** → choose `Utya_Gift_Bot`.
3. Railway will detect Python and start building automatically. **Let it fail for now** — we need to add env vars first.

### Step 4 — Add environment variables

1. Click on your service → **"Variables"** tab.
2. Add each variable individually using **"New Variable"**:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | Your bot token |
| `TELEGRAM_API_ID` | Your api_id |
| `TELEGRAM_API_HASH` | Your api_hash |
| `SESSION_STRING` | The long string printed by `setup_auth.py` |
| `MRKT_TOKEN` | *(leave empty — auto-refreshed)* |
| `PORTALS_TOKEN` | *(leave empty — auto-refreshed)* |
| `TONNEL_TOKEN` | *(leave empty — auto-refreshed)* |

### Step 5 — Set the start command

1. Go to **Settings** tab of your service.
2. Under **"Start Command"** enter:
   ```
   python bot.py
   ```

### Step 6 — Deploy

Click **"Deploy"** (or push a new commit to trigger auto-deploy). Open the **"Logs"** tab and watch for:

```
Pyrogram configured — token auto-refresh is enabled
Starting Utya Gift Price Bot…
```

### Updating the bot later

Just push to GitHub — Railway redeploys automatically.

---

## 3. Fly.io

**What you get for free:** 3 shared-CPU VMs, 256 MB RAM each, plus **3 GB of persistent volume storage**. This means you can use the `.session` file without `SESSION_STRING`.

### Step 1 — Create an account and install CLI

1. Sign up at **https://fly.io**.
2. Install the CLI:
   ```bash
   # macOS / Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```
3. Log in:
   ```bash
   fly auth login
   ```

### Step 2 — Create a `fly.toml` config

In the project root, create `fly.toml`:

```toml
app = "utya-gift-bot"
primary_region = "ams"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[[mounts]]
  source = "bot_data"
  destination = "/data"

[processes]
  app = "python bot.py"
```

### Step 3 — Update the session file path

Because Fly.io uses a mounted volume at `/data`, tell the bot to store the session there. In `.env` (or as a secret) add:

```
FLY_VOLUME_PATH=/data
```

Update `token_refresher.py` line:
```python
SESSION_FILE = os.getenv("FLY_VOLUME_PATH", ".") + "/utya_session"
```

Or simply keep `SESSION_STRING` and skip the volume entirely — both work.

### Step 4 — Launch

```bash
fly launch --no-deploy
```

When prompted:
- App name: `utya-gift-bot` (or any unique name)
- Region: choose one close to you
- Postgres / Redis: **No**

### Step 5 — Create the volume

```bash
fly volumes create bot_data --size 1 --region ams
```

### Step 6 — Set secrets

```bash
fly secrets set \
  BOT_TOKEN="123456789:AAFxxxxxxxx" \
  TELEGRAM_API_ID="12345678" \
  TELEGRAM_API_HASH="abcdef..." \
  SESSION_STRING="BQHMxxxxxx..."
```

### Step 7 — Deploy

```bash
fly deploy
```

Follow logs:

```bash
fly logs
```

### Updating the bot later

```bash
git push   # then:
fly deploy
```

---

## 4. Render

**What you get for free:** 750 hours/month of a free web service. Note: free services **spin down after 15 minutes of inactivity** and take ~30 seconds to wake up. This means the bot could miss messages during sleep. For a Telegram bot using long-polling this is acceptable since Telegram queues updates — but the bot will be slow to respond after a period of silence.

> If uptime matters, use Oracle Cloud or Railway instead.

Render also has an **ephemeral filesystem**, so use `SESSION_STRING`.

### Step 1 — Create an account

1. Go to **https://render.com** and sign up with GitHub.

### Step 2 — Push to GitHub

Same as Railway Step 2.

### Step 3 — Create a new Web Service

1. In Render dashboard click **"New" → "Web Service"**.
2. Connect your GitHub repo.
3. Configure:
   - **Name:** `utya-gift-bot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free

### Step 4 — Add environment variables

In the **"Environment"** tab add:

| Key | Value |
|---|---|
| `BOT_TOKEN` | Your bot token |
| `TELEGRAM_API_ID` | Your api_id |
| `TELEGRAM_API_HASH` | Your api_hash |
| `SESSION_STRING` | The string from `setup_auth.py` |

### Step 5 — Deploy

Click **"Create Web Service"**. Render builds and starts the bot automatically.

To prevent the service from sleeping you can add a free uptime monitor (e.g. **https://uptimerobot.com**) that pings the Render URL every 5 minutes — but free Render services don't expose a port by default when running as a background worker. The simplest fix is to switch the service type to **Background Worker** in Render settings, which never sleeps.

> In the Render dashboard: **Settings → Instance Type → Background Worker** (still free).

---

## Environment Variables — Full Reference

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ Always | Telegram bot token from @BotFather |
| `TELEGRAM_API_ID` | For auto-refresh | From my.telegram.org/apps |
| `TELEGRAM_API_HASH` | For auto-refresh | From my.telegram.org/apps |
| `SESSION_STRING` | For cloud platforms | Printed by `setup_auth.py`; replaces `.session` file |
| `MRKT_TOKEN` | Auto-refreshed | Leave empty if auto-refresh is on |
| `PORTALS_TOKEN` | Auto-refreshed | Leave empty if auto-refresh is on |
| `TONNEL_TOKEN` | Auto-refreshed | Leave empty if auto-refresh is on |
| `MRKT_APP_SHORT_NAME` | No | MRKT mini-app short name (default: `market`) |
| `CACHE_TTL` | No | Price cache in seconds (default: `300`) |

---

## Troubleshooting

**Bot starts but MRKT/Portals/Tonnel show `—`**
→ Tokens are not set yet. Wait 15 seconds for the initial auto-refresh, or check logs for errors.

**`No Pyrogram session found`**
→ Either upload `utya_session.session` to the server, or set `SESSION_STRING` in env vars.

**`MRKT token refresh failed`**
→ The MRKT mini-app short name may be wrong. Open `@main_mrkt_bot` in Telegram, press the web app button, copy the URL suffix, and set `MRKT_APP_SHORT_NAME=<that suffix>` in env vars.

**`KeyError: 'BOT_TOKEN'`**
→ `.env` file is missing or `BOT_TOKEN` is not set.

**Bot stops responding after a few hours (Render only)**
→ Switch the Render service to **Background Worker** type (see Render section above).
