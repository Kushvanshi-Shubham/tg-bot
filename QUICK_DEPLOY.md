# 🚀 Quick Deployment Guide

## ⚡ Fastest Ways to Deploy (5-10 minutes)

### Option 1: Render.com (FREE - Recommended) ⭐

**Perfect for:** Free 24/7 hosting with 750 hours/month

1. **Go to** https://render.com and sign up with GitHub

2. **Click** "New +" → "Background Worker"

3. **Connect your GitHub repository:**
   - Select your `tg-bot` repository
   - Give it a name: `telegram-usdt-bot`

4. **Configure build settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m src.bot`
   - **Instance Type:** Select **"Free"**

5. **Add environment variables:**
   - Click "Advanced" → "Add Environment Variable"
   - Add each variable from your `.env` file:
     ```
     BOT_TOKEN=8439656332:AAEXDOnnzT6NXMxYOXIxYm85yGVGmZ6y_fs
     ADMIN_IDS=7468554137
     MAIN_GROUP_ID=-5060298492
     GROUP_CHAT_IDS=-4962738119, -5048892225
     LOGS_GROUP_ID=-1001234567890
     PAYMENT_METHODS=CDM,Cash Deposit
     ADMIN_USDT_BSC=your_bsc_usdt_address
     ADMIN_USDT_TRON=your_tron_usdt_address
     ADMIN_USDT_BASE=your_base_usdt_address
     ADMIN_USDT_SOL=your_sol_usdt_address
     ```
   - **Note:** Set up your logs channel first (see `LOGS_SETUP.md`)

6. **Create Web Service!** Render will:
   - Install dependencies
   - Start your bot
   - Keep it running 24/7

7. **Monitor deployment:**
   - Watch the logs in real-time
   - Wait for "Bot started successfully" message

8. **View logs anytime:**
   - Dashboard → Your service → "Logs" tab
   - Check for any errors

✅ **Done!** Your bot is now live **FREE** on Render! 🎉

**Important Notes:**
- ⚠️ Free tier sleeps after 15 min of inactivity
- ✅ For Telegram bots, this is fine - bot receives updates constantly
- ✅ 750 hours/month = ~31 days of runtime
- 💡 Tip: Enable "Auto-Deploy" for automatic updates from GitHub

---

### Option 2: Railway.app (Alternative - $5 credit/month)

1. **Go to** https://railway.app and sign up with GitHub
2. **Click** "New Project" → "Deploy from GitHub repo"
3. **Select** your repository
4. **Add environment variables:**
   - Click on your project → "Variables"
   - Add each variable from your `.env` file:
     ```
     BOT_TOKEN=8439656332:AAEXDOnnzT6NXMxYOXIxYm85yGVGmZ6y_fs
     ADMIN_IDS=7468554137
     MAIN_GROUP_ID=-5060298492
     GROUP_CHAT_IDS=-4962738119, -5048892225
     LOGS_GROUP_ID=-1001234567890
     PAYMENT_METHODS=CDM,Cash Deposit
     ADMIN_USDT_BSC=your_bsc_usdt_address
     ADMIN_USDT_TRON=your_tron_usdt_address
     ADMIN_USDT_BASE=your_base_usdt_address
     ADMIN_USDT_SOL=your_sol_usdt_address
     ```
   - **Note:** Set up your logs channel first (see `LOGS_SETUP.md`)
### Option 2: Railway.app (Alternative - $5 credit/month)

1. **Go to** https://railway.app and sign up with GitHub
2. **Click** "New Project" → "Deploy from GitHub repo"
3. **Select** your repository
4. **Add environment variables:**
   - Click on your project → "Variables"
   - Add each variable from your `.env` file (same as Render above)
5. **Deploy!** Railway will automatically deploy your bot
6. **Check logs** to see if it's running

✅ Free $5 credit per month (500 hours)

---

### Option 3: VPS with systemd (MOST RELIABLE - Paid)

1. **Get a VPS:**
   - DigitalOcean: https://www.digitalocean.com ($6/month)
   - Vultr: https://www.vultr.com ($5/month)

2. **Connect via SSH:**
   ```bash
   ssh root@your_server_ip
   ```

3. **Install dependencies:**
   ```bash
   apt update && apt install -y python3 python3-pip python3-venv git
   ```

4. **Clone your repo:**
   ```bash
   git clone <your-repo-url>
   cd tg-bot
   ```

5. **Setup environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Create .env file:**
   ```bash
   nano .env
   # Paste your .env content
   # Press Ctrl+X, Y, Enter to save
   ```

7. **Create systemd service:**
   ```bash
   sudo nano /etc/systemd/system/tg-bot.service
   ```
   
   **Paste this:**
   ```ini
   [Unit]
   Description=Telegram USDT Trading Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/tg-bot
   Environment="PATH=/root/tg-bot/.venv/bin"
   ExecStart=/root/tg-bot/.venv/bin/python -m src.bot
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

8. **Start the bot:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tg-bot
   sudo systemctl start tg-bot
   ```

9. **Check status:**
   ```bash
   sudo systemctl status tg-bot
   ```

✅ **Done!** Your bot is running with auto-restart!

---

### Option 4: Docker (CLEAN & PORTABLE)

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Start bot:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

✅ **Done!** Bot is running in container!

---

## 🔧 Common Commands

### Render.com:
```bash
# View logs
Dashboard → Your service → "Logs" tab

# Restart service
Dashboard → Your service → "Manual Deploy" → "Clear build cache & deploy"

# Stop service
Dashboard → Your service → "Suspend"
```

### Railway:
```bash
# View logs
Dashboard → Check logs in real-time

# Restart
Dashboard → Redeploy

# Stop
Dashboard → Remove deployment
```

### Check if bot is running (VPS):
```bash
# Systemd
sudo systemctl status tg-bot

# Docker
docker ps
```

### View logs (VPS):
```bash
# Systemd
sudo journalctl -u tg-bot -f

# Docker
docker-compose logs -f
```

### Restart bot:
```bash
# Systemd
sudo systemctl restart tg-bot

# Docker
docker-compose restart
```

### Stop bot:
```bash
# Systemd
sudo systemctl stop tg-bot

# Docker
docker-compose down
```

---

## ⚠️ Important Notes

1. **Database:** Your `deals.db` will be created automatically
2. **Backup:** Regularly backup your database
3. **Security:** NEVER commit your `.env` file to Git
4. **Updates:** Pull latest code and restart service

---

## 🆘 Troubleshooting

**Bot not responding?**
- Check logs for errors
- Verify BOT_TOKEN is correct
- Ensure bot is added to your group

**Database errors?**
- Check file permissions
- Verify sqlite3 is installed

**Environment variable errors?**
- Double-check all variables in .env
- Ensure no spaces around `=` in .env file

---

## 📊 Monitoring

### Check bot health:
```bash
# CPU and memory usage
top

# Bot process
ps aux | grep python

# Network connections
netstat -tlnp | grep python
```

### Automated backup (crontab):
```bash
crontab -e
# Add this line:
0 0 * * * cp /root/tg-bot/deals.db /root/backups/deals-$(date +\%Y\%m\%d).db
```

---

## 🎯 Next Steps After Deployment

1. ✅ **Set up logs channel** - See `LOGS_SETUP.md` to receive deal receipts
2. ✅ Test bot in Telegram
3. ✅ Verify all commands work
4. ✅ Test popup alerts
5. ✅ Create a test deal and check logs channel
6. ✅ Monitor logs for errors
7. ✅ Set up database backups

---

**Important Files:**
- `LOGS_SETUP.md` - Set up receipt notifications channel
- `DEPLOYMENT.md` - Complete deployment guide
- `README.md` - Bot features and usage

**Your bot is ready to go live! 🚀**
