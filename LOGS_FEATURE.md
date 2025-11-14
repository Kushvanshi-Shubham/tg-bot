# 📊 Deal Notifications System

## Overview

Your bot now has a comprehensive notification system that sends detailed receipts and status updates to a dedicated logs channel/group. This gives you a complete audit trail of all deals.

---

## ✅ What's Been Added

### 1. **Logs Channel Integration**
- New environment variable: `LOGS_GROUP_ID`
- Automatic notifications sent to your private channel/group
- All major deal events are tracked and logged

### 2. **Notification Types**

Your logs channel will receive:

| Event | When | Information Included |
|-------|------|---------------------|
| 📝 **Deal Created** | When `/deal` is initiated | Deal ID, Initiator, Counterparty, Status |
| ✅ **Deal Accepted** | When counterparty accepts | Deal ID, Both parties, Amount, Status |
| ❌ **Deal Rejected** | When counterparty rejects | Deal ID, Both parties, Who rejected |
| ❌ **Deal Cancelled** | When someone cancels | Deal ID, Both parties, Who cancelled |
| ✅ **TX Verified** | When admin verifies USDT | Deal ID, Admin name, TX hash, Network |
| 💰 **Fiat Sent** | When buyer sends payment | Deal ID, Buyer, Amount, Payment method |
| 💵 **Fiat Received** | When seller confirms | Deal ID, Seller, Amount, Status |
| 🎉 **Deal Completed** | When both parties confirm | Complete receipt with all details |

### 3. **Files Added**

- `LOGS_SETUP.md` - Complete setup guide
- `test_logs.py` - Test script to verify configuration
- Updated `.env` and `.env.example` with LOGS_GROUP_ID
- Updated deployment guides

---

## 🚀 Quick Setup

### Step 1: Create a Private Channel

1. Open Telegram → New Channel
2. Name it: "USDT Bot Logs"
3. Make it private
4. Add your bot as admin

### Step 2: Get Channel ID

1. Forward a message from the channel to @userinfobot
2. Copy the chat ID (e.g., `-1001234567890`)

### Step 3: Configure

Add to your `.env` file:
```env
LOGS_GROUP_ID=-1001234567890
```

### Step 4: Test

Run the test script:
```powershell
python test_logs.py
```

You should see a test message in your logs channel!

---

## 📋 Sample Notifications

### New Deal:
```
📝 NEW DEAL CREATED

Deal ID: #123
Initiator: @john
Counterparty: @alice
Status: Pending (waiting to join room)

🔗 Deal Room
```

### Deal Completed:
```
🎉 DEAL COMPLETED

Deal ID: #123
Initiator: @john
Counterparty: @alice
Amount: 100 USDT
Payment Method: UPI
Network: BSC
INR Rate: ₹92/USDT
Status: ✅ COMPLETED

Both parties confirmed completion.
```

---

## 🔧 Configuration

**Required in `.env`:**
```env
# Your logs/receipts channel
LOGS_GROUP_ID=-1001234567890
```

**Optional - Leave blank to disable notifications:**
```env
LOGS_GROUP_ID=
```

---

## 📁 File Structure

```
tg-bot/
├── src/
│   ├── bot.py              # ✅ Updated with logging
│   ├── deal_conversation.py # ✅ Updated with logging
│   └── ...
├── .env                    # ✅ Add LOGS_GROUP_ID here
├── .env.example            # ✅ Updated with example
├── LOGS_SETUP.md           # 📖 Setup instructions
├── test_logs.py            # 🧪 Test script
├── DEPLOYMENT.md           # 📖 Updated deployment guide
└── QUICK_DEPLOY.md         # 📖 Updated quick guide
```

---

## 🎯 Features

### Comprehensive Tracking
- Every deal stage is logged
- Timestamps on all events
- User information (username or name)
- Transaction details

### Error Handling
- Failed notifications are logged to console
- Bot continues working even if logs fail
- Graceful degradation

### Privacy
- Only you see the notifications
- Private channel recommended
- No sensitive data exposed publicly

### Audit Trail
- Complete history of all deals
- Easy to review past transactions
- Dispute resolution support

---

## 🔍 How It Works

### Code Implementation

**In `bot.py`:**
```python
# Load logs group ID
LOGS_GROUP_ID = int(os.environ.get("LOGS_GROUP_ID", "0")) if os.environ.get("LOGS_GROUP_ID") else None

# Helper function to send notifications
async def send_log_notification(context, message):
    if LOGS_GROUP_ID:
        try:
            await context.bot.send_message(
                chat_id=LOGS_GROUP_ID, 
                text=message, 
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send log notification: {e}")
```

**Notifications are sent at key points:**
- Deal creation (in `deal_conversation.py`)
- Deal acceptance (in `bot.py`)
- Deal rejection (in `bot.py`)
- Deal cancellation (in `bot.py`)
- TX verification (in `bot.py`)
- Fiat sent/received (in `bot.py`)
- Deal completion (in `bot.py`)

---

## 🆘 Troubleshooting

### Not receiving notifications?

**Check these:**
1. ✅ Bot is added to channel/group
2. ✅ Bot has admin permissions
3. ✅ LOGS_GROUP_ID includes negative sign
4. ✅ Bot is restarted after config change

**Run test script:**
```powershell
python test_logs.py
```

### Wrong chat ID?

- Channel IDs start with `-100`
- Group IDs can be shorter
- Always include the `-` sign
- Use @userinfobot to verify

### Permission errors?

- Make bot an administrator
- Grant "Post Messages" permission
- Check bot is still a member

---

## 📊 Benefits

### For You:
- ✅ Complete audit trail
- ✅ Easy dispute resolution
- ✅ Monitor all activity
- ✅ Track successful deals
- ✅ Identify issues quickly

### For Users:
- ✅ Transparent process
- ✅ Trust building
- ✅ Issue tracking
- ✅ Better support

### For Business:
- ✅ Compliance records
- ✅ Performance metrics
- ✅ Analytics data
- ✅ Growth tracking

---

## 🎓 Advanced Usage

### Multiple Admins

Add multiple people to the logs channel to share monitoring duties.

### Export Records

Telegram allows exporting chat history for backup and analysis.

### Bot Commands

You can add commands to query deal history directly from the logs channel.

### Analytics

Parse notification messages to generate reports and statistics.

---

## 🔐 Security Notes

1. **Keep logs channel private**
2. **Only add trusted admins**
3. **Don't share channel link**
4. **Regular backups recommended**
5. **Monitor for unusual activity**

---

## 🚀 Next Steps

1. **Set up your logs channel** - Follow `LOGS_SETUP.md`
2. **Test configuration** - Run `test_logs.py`
3. **Create a test deal** - Verify notifications work
4. **Deploy your bot** - See `QUICK_DEPLOY.md`
5. **Monitor actively** - Check logs daily

---

**Your bot now has enterprise-grade logging and audit capabilities! 📊✅**
