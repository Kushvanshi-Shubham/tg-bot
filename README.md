# Telegram P2P Deal Bot

Automated Telegram bot to manage peer-to-peer USDT deals between two users using a pool of pre-created private groups.

**Developer:** [@killerbesto](https://t.me/killerbesto)  
**Copyright:** © 2025 - All Rights Reserved

---

## Features
- 📝 `/deal` — Interactive deal creation with step-by-step guidance:
  - Select your role (Buyer or Seller)
  - Enter deal amount
  - Choose payment method (UPI, Bank Transfer, CDM, etc.)
  - Enter counterparty username
  - Confirm and create deal
- 🔘 Group-based deal flow with inline buttons:
  - Seller: Accept/Reject
  - Seller: Send Payment (submit TX hash)
  - Admin: Verify payment
  - Buyer: I've Sent Fiat
  - Seller: Fiat Received
  - Admin: Release USDT
- 📊 **Comprehensive Logging System:**
  - All deals logged to private admin channel
  - Real-time notifications for every deal event
  - Complete audit trail with receipts
  - See `LOGS_SETUP.md` for setup
- 💾 SQLite storage for deals and group pool tracking
- 👨‍💼 Admin commands: `/list_groups`, `/release_group`, `/deal_status`
- 🔔 Popup alerts for unauthorized button clicks
- 🌐 Multi-network support (BSC, TRON, BASE, SOL)

## Requirements
- Python 3.10+
- A Telegram bot token (from BotFather)
- 5–10 pre-created Telegram groups with the bot added as admin

## Setup

### 1. Create pre-created deal groups
- Create 5–10 private Telegram groups (one for each concurrent deal).
- Add your bot to each group and make it an admin with these permissions:
  - Send messages
  - Delete messages (optional, for cleanup)
  - Invite users via link (required)
  - Manage chat (optional, for restricting members)

### 2. Get group chat IDs
- Use a tool like @RawDataBot or @getidsbot: add the bot to each group and it will report the chat ID (negative number like `-1001234567890`).
- Or use this quick method: send a message in the group, then call `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` and look for `"chat":{"id":-1001234567890,...}`.

### 3. Configure environment
- Copy `.env.example` to `.env`.
- Fill in:
  - `BOT_TOKEN` — your bot token from BotFather.
  - `ADMIN_IDS` — comma-separated numeric Telegram user IDs of admins.
  - `USDT_ADDRESS` — wallet address for receiving USDT.
  - `GROUP_CHAT_IDS` — comma-separated group chat IDs (e.g., `-1001234567890,-1009876543210`).
  - `LOGS_GROUP_ID` — (Optional but recommended) Private channel/group for deal receipts. See `LOGS_SETUP.md`.
  - `PAYMENT_METHODS` — comma-separated payment methods (e.g., `UPI,Bank Transfer,CDM,Cash Deposit,PayPal`).
  - Network-specific USDT/USDC addresses (BSC, TRON, BASE, SOL)
  - (Optional) `FEE_INFO` — fee text displayed after acceptance.

### 4. Install dependencies
Create and activate a virtualenv, then install:
```pwsh
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

### 5. Run the bot
```pwsh
python -m src.bot
```
- Expected: console prints "Bot started" and begins polling.

## Deal Flow (Automated)

1. **User runs `/deal` (with optional mention)**
   - Option 1: Reply to someone's message and type `/deal`
   - Option 2: Type `/deal @username` or `/deal` and mention user
   - Option 3: Just `/deal` and enter username later
   
   Bot shows interactive prompts:
   - Select role (Buyer or Seller)
   - Select currency (Crypto/USDT or INR)
   - Enter amount (just the number)
   - Choose payment method from buttons
   - Enter counterparty username (if not already mentioned)
   - Confirm deal details
   
   - Bot finds a free group from the pool.
   - Bot creates a unique invite link (limited to 2 members).
   - Bot sends the invite link to both users via DM.

2. **Both users click the invite link and join the group**
   - Once both are present, the bot posts an Accept/Reject button for the Seller.
   - **Note**: Only the deal initiator's inputs are accepted during the creation flow.

3. **Seller clicks [✅ Accept]**
   - Bot marks deal as accepted and shows [💰 Send Payment] button.

4. **Seller clicks [💰 Send Payment]**
   - Bot displays USDT address and asks seller to use `/submit_tx <deal_id> <tx_hash> <amount> <network>`.

5. **Seller sends USDT and runs `/submit_tx`**
   - Bot stores TX hash and notifies Admin with [✅ Verified] button.

6. **Admin clicks [✅ Verified]**
   - Bot marks payment as verified and shows Buyer a [✅ I've Sent Fiat] button.

7. **Buyer sends fiat and clicks [✅ I've Sent Fiat]**
   - Bot shows Seller a [✅ Fiat Received] button.

8. **Seller receives fiat and clicks [✅ Fiat Received]**
   - Bot shows Admin a [🔓 Release USDT] button.

9. **Admin manually transfers USDT to Seller's wallet and clicks [🔓 Release USDT]**
   - Bot marks deal as released and closed.
   - Bot frees the group for the next deal.

## Admin Commands
- `/list_groups` — show all groups in pool with status (Free/Occupied).
- `/release_group <chat_id>` — manually free a group.
- `/deal_status` or `/deal_status <deal_id>` — show deal info.

## Bot Permissions (Required)
The bot must be an **admin** in each group with at least:
- **Can invite users via link** (to create invite links).
- **Send messages** (to post buttons and instructions).
- (Optional) **Delete messages** and **Restrict members** for cleanup/moderation.

## Testing Checklist
1. ✅ Add bot to 5–10 groups as admin; get chat IDs
2. ✅ Set up logs channel (see `LOGS_SETUP.md`) and test with `python test_logs.py`
3. ✅ Set `GROUP_CHAT_IDS` and `LOGS_GROUP_ID` in `.env`
4. ✅ Run bot: `python -m src.bot`
5. ✅ Buyer: `/deal @seller` → both receive invite link
6. ✅ Both click link and join group
7. ✅ Seller: tap [Accept] → Check logs channel for notification
8. ✅ Seller: tap [Send Payment], run `/submit_tx`
9. ✅ Admin: tap [Verified] → Check logs channel
10. ✅ Buyer: tap [I've Sent Fiat] → Check logs channel
11. ✅ Seller: tap [Fiat Received] → Check logs channel
12. ✅ Admin: transfer USDT manually, tap [Release USDT]
13. ✅ Verify group is freed: `/list_groups`
14. ✅ Check logs channel for complete deal receipt

## Documentation

- 📖 `LOGS_SETUP.md` - Set up deal notifications channel
- 📖 `LOGS_FEATURE.md` - Complete logging system documentation
- 📖 `LOGS_QUICKREF.md` - Quick reference card
- 🚀 `QUICK_DEPLOY.md` - Fast deployment guide
- 📚 `DEPLOYMENT.md` - Complete deployment options
- 🧪 `test_logs.py` - Test your logs configuration

## Notes
- Admin manually transfers USDT (bot does not handle private keys).
- For automatic on-chain verification, integrate a blockchain explorer API (future enhancement).
- Use PostgreSQL for production and connection pooling.
- Keep `.env` secret; add to `.gitignore`.

---

## 👨‍💻 Developer

**Created by:** [@killerbesto](https://t.me/killerbesto)

For custom bot development, contact: [@killerbesto](https://t.me/killerbesto)

## 📄 License

Copyright © 2025 @killerbesto - All Rights Reserved

This bot is proprietary software developed by @killerbesto.  
Unauthorized copying, modification, distribution, or removal of copyright notices is strictly prohibited.

---

**⚠️ IMPORTANT:** This software includes built-in copyright protection. Any attempt to remove or modify copyright notices from the code or bot messages will violate the license agreement.
