# 📊 Logs Group Setup Guide

This guide helps you set up a private channel or group to receive all deal notifications and receipts.

---

## 🎯 What You'll Receive

Your logs group will get detailed notifications for:

- 📝 **New Deal Created** - When a deal is initiated
- ✅ **Deal Accepted** - When counterparty accepts
- ❌ **Deal Rejected** - When counterparty rejects
- ❌ **Deal Cancelled** - When someone cancels
- ✅ **TX Verified** - When admin verifies USDT payment
- 💰 **Fiat Sent** - When buyer sends fiat payment
- 💵 **Fiat Received** - When seller confirms receipt
- 🎉 **Deal Completed** - Full receipt when both parties confirm

---

## 📱 Setup Steps

### Option 1: Create a Private Channel (Recommended)

1. **Open Telegram** and tap the menu (☰)

2. **Create New Channel:**
   - Tap "New Channel"
   - Name it: "USDT Bot Logs" (or any name you prefer)
   - Description: "Deal receipts and notifications"

3. **Make it Private:**
   - Choose "Private Channel"
   - Skip adding subscribers (just you)

4. **Add Your Bot:**
   - Open the channel
   - Tap channel name → "Administrators"
   - Tap "Add Administrator"
   - Search for your bot username
   - Add it as admin with "Post Messages" permission

5. **Get Channel ID:**
   - Forward any message from the channel to @userinfobot
   - It will show you the channel ID (e.g., `-1001234567890`)
   - Copy this number

6. **Add to .env file:**
   ```env
   LOGS_GROUP_ID=-1001234567890
   ```

7. **Restart your bot**

✅ **Done!** You'll now receive all deal notifications in this channel.

---

### Option 2: Create a Private Group

1. **Create New Group:**
   - Tap menu → "New Group"
   - Name it: "USDT Bot Logs"
   - Add yourself as member

2. **Add Your Bot:**
   - Open group info
   - Tap "Add Members"
   - Add your bot

3. **Make Bot Admin:**
   - Group info → "Administrators"
   - Add bot as admin

4. **Get Group ID:**
   - Add @userinfobot to the group
   - It will show the group ID
   - Copy the ID (includes negative sign)

5. **Add to .env:**
   ```env
   LOGS_GROUP_ID=-1234567890
   ```

6. **Restart your bot**

---

## 🔍 How to Get Chat ID (Alternative Methods)

### Method 1: Using @userinfobot
1. Add @userinfobot to your channel/group
2. It will automatically show the chat ID
3. Remove the bot after getting the ID

### Method 2: Using @RawDataBot
1. Add @RawDataBot to your channel/group
2. It shows detailed JSON with chat ID
3. Look for `"id": -1001234567890`

### Method 3: Using Python Script
Create `get_chat_id.py`:
```python
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

async def print_chat_id(update: Update, context):
    print(f"Chat ID: {update.effective_chat.id}")
    await update.message.reply_text(f"Chat ID: {update.effective_chat.id}")

app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.ALL, print_chat_id))
app.run_polling()
```

Run it and send a message in your channel/group.

---

## 📋 Sample Notification Examples

### Deal Created:
```
📝 NEW DEAL CREATED

Deal ID: #123
Initiator: @john
Counterparty: @alice
Status: Pending (waiting to join room)

🔗 Deal Room
```

### Deal Accepted:
```
✅ DEAL ACCEPTED

Deal ID: #123
Initiator: @john
Counterparty: @alice
Amount: 100 USDT
Status: Awaiting rate confirmation
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

## ⚙️ Configuration

**In your `.env` file:**
```env
# Logs/Admin group where you receive all deal receipts
LOGS_GROUP_ID=-1001234567890
```

**Leave blank** if you don't want logs (not recommended for production):
```env
LOGS_GROUP_ID=
```

---

## 🔒 Security Tips

1. **Keep it Private:** Don't share the logs channel publicly
2. **Admin Only:** Only add trusted admins
3. **Regular Backups:** Export important receipts periodically
4. **Monitor Daily:** Check logs daily for suspicious activity

---

## 🆘 Troubleshooting

**Not receiving notifications?**
- ✅ Check bot is admin in channel/group
- ✅ Verify LOGS_GROUP_ID is correct (with negative sign)
- ✅ Restart bot after adding LOGS_GROUP_ID
- ✅ Check bot logs for errors

**Wrong chat ID?**
- The ID must include the negative sign: `-1001234567890`
- Channels usually start with `-100`
- Groups can be shorter like `-123456789`

**Bot can't send messages?**
- Make sure bot has "Post Messages" permission
- Check bot is still a member/admin
- Verify the channel/group still exists

---

## 📊 Using Multiple Channels (Advanced)

You can create separate channels for different purposes:

**Logs Channel:**
```env
LOGS_GROUP_ID=-1001111111111  # All deal receipts
```

**Main Group:**
```env
MAIN_GROUP_ID=-1002222222222  # Public deal announcements
```

**Deal Rooms:**
```env
GROUP_CHAT_IDS=-1003333333333, -1004444444444  # Private rooms
```

---

## 🎯 Best Practices

1. **Create Before Launch:** Set up logs before going live
2. **Test First:** Create a test deal to verify logs work
3. **Pin Important Messages:** Pin critical receipts
4. **Export Regularly:** Save important transaction records
5. **Monitor Closely:** Check for failed deals or disputes

---

**Your logs channel is now ready to track all deals! 📊**
