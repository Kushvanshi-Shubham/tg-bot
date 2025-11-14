# 📋 Quick Reference: Logs Channel Setup

## 🎯 5-Minute Setup

### 1. Create Channel
- Open Telegram → Menu → **New Channel**
- Name: **"USDT Bot Logs"**
- Type: **Private**

### 2. Add Bot
- Open channel → **Administrators**
- **Add Administrator** → Select your bot
- Grant: **Post Messages** permission

### 3. Get Chat ID
- Forward any channel message to **@userinfobot**
- Copy the chat ID (e.g., `-1001234567890`)

### 4. Configure
Edit `.env`:
```env
LOGS_GROUP_ID=-1001234567890
```

### 5. Test
```powershell
python test_logs.py
```

✅ **Done!** Check your channel for test message.

---

## 📊 What You'll Receive

| Icon | Event | When |
|------|-------|------|
| 📝 | Deal Created | Initiator starts deal |
| ✅ | Deal Accepted | Counterparty accepts |
| ❌ | Deal Rejected | Counterparty rejects |
| ❌ | Deal Cancelled | Someone cancels |
| ✅ | TX Verified | Admin verifies payment |
| 💰 | Fiat Sent | Buyer sends payment |
| 💵 | Fiat Received | Seller confirms |
| 🎉 | Deal Completed | Both confirm complete |

---

## 🔧 Quick Commands

**Test logs:**
```powershell
python test_logs.py
```

**Check config:**
```powershell
Get-Content .env | Select-String "LOGS_GROUP_ID"
```

**Restart bot:**
```powershell
# If running locally:
Ctrl+C
python -m src.bot

# If deployed:
# See DEPLOYMENT.md for your platform
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| No messages | Check bot is admin in channel |
| Permission error | Grant "Post Messages" to bot |
| Wrong ID | Include negative sign: `-1001...` |
| Still not working | Run `python test_logs.py` |

---

## 📖 Detailed Guides

- **Full Setup:** `LOGS_SETUP.md`
- **Feature Info:** `LOGS_FEATURE.md`
- **Deploy Bot:** `QUICK_DEPLOY.md`

---

**Need help? Check the detailed guides above! 📚**
