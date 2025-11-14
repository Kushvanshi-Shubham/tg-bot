# 🚀 Deployment Guide

This guide covers multiple ways to deploy your Telegram USDT Trading Bot.

---

## 📋 Prerequisites

Before deploying, ensure:
- ✅ Your `.env` file is properly configured with your bot token
- ✅ Database is working locally
- ✅ All features tested and working

---

## 🎯 Deployment Options

### Option 1: **VPS/Cloud Server (Recommended)**

Best for: Full control, reliability, 24/7 uptime

#### Providers:
- **DigitalOcean** ($4-6/month) - https://www.digitalocean.com
- **Linode** ($5/month) - https://www.linode.com
- **Vultr** ($3.50-6/month) - https://www.vultr.com
- **AWS EC2** (Free tier available) - https://aws.amazon.com
- **Google Cloud** (Free tier available) - https://cloud.google.com

#### Steps:

1. **Create a VPS** (Ubuntu 22.04 recommended)

2. **Connect via SSH:**
   ```bash
   ssh root@your_server_ip
   ```

3. **Install Python and Git:**
   ```bash
   apt update
   apt install -y python3 python3-pip python3-venv git
   ```

4. **Clone your repository:**
   ```bash
   git clone <your-repo-url>
   cd tg-bot
   ```

5. **Set up environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Configure .env file:**
   ```bash
   nano .env
   # Paste your configuration
   # Press Ctrl+X, then Y, then Enter to save
   ```

7. **Run with systemd (auto-restart):**
   ```bash
   sudo nano /etc/systemd/system/tg-bot.service
   ```
   
   Paste this:
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

8. **Start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tg-bot
   sudo systemctl start tg-bot
   ```

9. **Check status:**
   ```bash
   sudo systemctl status tg-bot
   sudo journalctl -u tg-bot -f  # View logs
   ```

---

### Option 2: **Docker Deployment**

Best for: Easy deployment, containerized environment

#### Steps:

1. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop bot:**
   ```bash
   docker-compose down
   ```

---

### Option 3: **Railway.app** (Easiest)

Best for: Beginners, free tier available

#### Steps:

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables from your `.env` file
6. Railway will auto-deploy!

**Important:** Add these variables in Railway dashboard:
- `BOT_TOKEN`
- `ADMIN_IDS`
- `MAIN_GROUP_ID`
- `GROUP_CHAT_IDS`
- `PAYMENT_METHODS`
- All USDT/USDC addresses

---

### Option 4: **Heroku**

Best for: Simple deployment with free tier

#### Steps:

1. Install Heroku CLI:
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. Login and create app:
   ```bash
   heroku login
   heroku create your-bot-name
   ```

3. Set environment variables:
   ```bash
   heroku config:set BOT_TOKEN=your_token
   heroku config:set ADMIN_IDS=your_admin_id
   # ... add all other env vars
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

5. Scale worker:
   ```bash
   heroku ps:scale worker=1
   ```

6. View logs:
   ```bash
   heroku logs --tail
   ```

---

### Option 5: **Render.com**

Best for: Free hosting, easy setup

#### Steps:

1. Go to https://render.com
2. Sign up with GitHub
3. Create new "Background Worker"
4. Connect your repository
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `python -m src.bot`
7. Add environment variables
8. Deploy!

---

### Option 6: **Local Server / Raspberry Pi**

Best for: Self-hosting, learning

#### Steps:

1. **Install Python:**
   ```bash
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd tg-bot
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run in background:**
   ```bash
   nohup python -m src.bot > bot.log 2>&1 &
   ```

4. **Or use screen:**
   ```bash
   screen -S tgbot
   python -m src.bot
   # Press Ctrl+A, then D to detach
   # screen -r tgbot to reattach
   ```

---

## 🔧 Maintenance Commands

### View logs:
```bash
# Systemd service
sudo journalctl -u tg-bot -f

# Docker
docker-compose logs -f

# Screen
screen -r tgbot
```

### Restart bot:
```bash
# Systemd
sudo systemctl restart tg-bot

# Docker
docker-compose restart

# PM2 (if using)
pm2 restart tg-bot
```

### Update code:
```bash
git pull
sudo systemctl restart tg-bot  # or docker-compose restart
```

---

## 📊 Monitoring

### Check if bot is running:
```bash
# Systemd
sudo systemctl status tg-bot

# Docker
docker ps

# Process
ps aux | grep python
```

### Database backup:
```bash
# Backup
cp deals.db deals.db.backup

# Automated backup (add to crontab)
0 0 * * * cp /root/tg-bot/deals.db /root/backups/deals-$(date +\%Y\%m\%d).db
```

---

## 🔐 Security Checklist

- ✅ Never commit `.env` to Git
- ✅ Use strong passwords for VPS
- ✅ Enable firewall (only open SSH port 22)
- ✅ Keep bot token secret
- ✅ Regular database backups
- ✅ Update system packages regularly

---

## 🆘 Troubleshooting

### Bot not starting:
```bash
# Check logs
sudo journalctl -u tg-bot -n 50

# Check Python path
which python
python --version

# Check dependencies
pip list
```

### Database errors:
```bash
# Check database file
ls -lh deals.db
sqlite3 deals.db "SELECT * FROM deals LIMIT 1;"
```

### Connection issues:
- Check internet connection
- Verify bot token is correct
- Ensure Telegram API is accessible

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Railway | 500 hours/month | $5/month |
| Heroku | Limited (eco dyno) | $7/month |
| Render | 750 hours/month | $7/month |
| DigitalOcean | No | $6/month |
| AWS EC2 | 12 months free | $3-10/month |
| Raspberry Pi | One-time cost | $35-75 |

---

## 🎯 Recommended Setup

**For Production:** VPS (DigitalOcean/Vultr) with systemd service
- Most reliable
- Full control
- Easy to maintain

**For Testing:** Railway.app or Render.com
- Quick setup
- Free tier available
- Good for development

---

## 📞 Need Help?

If you encounter issues:
1. Check logs first
2. Verify environment variables
3. Test database connection
4. Ensure bot token is valid

---

**Your bot is now ready to deploy! Choose the option that best fits your needs.** 🚀
