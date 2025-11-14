# Quick Setup Guide

## Prerequisites
1. ✅ Database migrated (old deals.db deleted)
2. ✅ Python 3.12 installed
3. ✅ Dependencies installed (`pip install -r requirements.txt`)

## Bot Permissions Required

### Main Group (Your Community)
1. Add bot as **administrator**
2. Enable these admin permissions:
   - ✅ Delete messages
   - ✅ Invite users via link
   - ✅ Manage chat

### Deal Room Groups (Pool of Private Rooms)
1. Add bot as **administrator** in each room
2. Enable these admin permissions:
   - ✅ Delete messages
   - ✅ Ban users
   - ✅ Invite users via link
   - ✅ Manage chat
   - ✅ Pin messages

## Configuration

### 1. Environment Variables (.env)
```env
# Bot Configuration
BOT_TOKEN=
ADMIN_IDS=

# Main group + Deal room pools
GROUP_CHAT_IDS=

# Payment Methods (comma-separated)
PAYMENT_METHODS=UPI,Bank Transfer,CDM,Cash Deposit,PayPal

# Legacy (for backward compatibility)
USDT_ADDRESS=TYourOldAddressHere

# Network-Specific Addresses (REQUIRED)
ADMIN_USDT_BSC=0xYourBSCAddress
ADMIN_USDT_TRON=TYourTronAddress
ADMIN_USDT_BASE=0xYourBaseAddress
ADMIN_USDT_SOL=YourSolanaAddress

# Optional: USDC Addresses
ADMIN_USDC_BSC=0xYourBSCUSDCAddress
ADMIN_USDC_TRON=TYourTronUSDCAddress
ADMIN_USDC_BASE=0xYourBaseUSDCAddress
ADMIN_USDC_SOL=YourSolanaUSDCAddress
```

### 2. Get Chat IDs

#### Method 1: Using bot
1. Add bot to group
2. Send any message in the group
3. Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":-1001234567890,...}`

#### Method 2: Using third-party bots
1. Add @RawDataBot to your group
2. It will show the chat ID immediately

### 3. Update .env
Replace `GROUP_CHAT_IDS` with:
```env
GROUP_CHAT_IDS=-1001234567890,-1001234567891,-1001234567892
```
First ID = Main group (where users type /deal)
Rest IDs = Deal room pool (private execution rooms)

## Start the Bot

```powershell
# 1. Delete old database
Remove-Item -Force deals.db

# 2. Start the bot
python -m src.bot
```

You should see:
```
INFO:__main__:Bot started
```

## Testing

### Test 1: Main Group Integration
1. In main group, type: `/deal @someone`
2. Check your DM - should receive deal form
3. Check main group - should see confirmation message

### Test 2: Deal Creation
1. Fill out form in DM:
   - Select role (Buyer/Seller)
   - Select currency (Crypto/INR)
   - Enter amount
   - (If INR: Enter rate)
   - Select payment method
   - Confirm details
2. Check DMs for invite link
3. Check main group for public announcement

### Test 3: Join Request Approval
1. Click invite link as deal initiator ✅ Should be approved
2. Counterparty clicks link ✅ Should be approved
3. Random user clicks link ❌ Should be declined
4. Admin clicks link ✅ Should be approved

### Test 4: Full Deal Flow
1. Both users join private room
2. Both click "Confirm"
3. Seller selects network
4. Seller selects token
5. Verify correct admin address shown
6. Seller runs `/submit_tx` in room
7. Admin verifies payment
8. Buyer marks "I've Sent Fiat"
9. Seller marks "Fiat Received"
10. Both mark "Completed"
11. Verify both users kicked
12. Verify room freed

## Troubleshooting

### Issue: "Could not send you a DM"
**Solution**: User must start the bot first
- Send `/start` to bot in private message
- Then try `/deal` again

### Issue: Join request not auto-approved
**Solution**: Check bot permissions
- Bot must be admin in deal room
- Bot needs "Invite users via link" permission
- Check ADMIN_IDS in .env includes admin user ID

### Issue: "No deal rooms available"
**Solution**: Add more rooms or free existing ones
- Create new Telegram groups
- Add bot as admin
- Add chat IDs to GROUP_CHAT_IDS in .env
- Or use `/release_group <chat_id>` to free stuck rooms

### Issue: Wrong admin address shown
**Solution**: Check .env configuration
- Make sure ADMIN_USDT_BSC, ADMIN_USDT_TRON, etc. are set
- Restart bot after changing .env
- Verify network/token selection in deal flow

### Issue: Users not kicked after completion
**Solution**: Bot needs ban permissions
- Bot must be admin in deal room
- Bot needs "Ban users" permission
- Check logs for any errors

## Architecture

```
Main Group (Public)
    ↓
  /deal @user
    ↓
User DM ← → Bot (Deal Form)
    ↓
  Confirm
    ↓
Assign Free Room → Create Join Link
    ↓
Send to: User DM + Counterparty DM + Main Group
    ↓
Join Requests → Auto-Approve (Initiator, Target, Admin)
    ↓
Private Room (Deal Execution)
    ↓
Both Confirm → Network → Token → TX → Verify → Fiat → Complete
    ↓
Kick Users → Free Room
```

## Admin Panel

### Monitor Rooms
```
/list_groups
```
Shows:
- Room chat ID
- Status (free/occupied)
- Current deal ID (if occupied)

### Free a Stuck Room
```
/release_group -1001234567890
```

### Reset All Rooms
```
/reset_groups
```
⚠️ Use carefully - frees ALL rooms

## Next Steps

1. ✅ Configure network addresses in .env
2. ✅ Test main group integration
3. ✅ Test join request approval
4. ✅ Test full deal flow
5. ✅ Monitor and adjust as needed

## Support

If you encounter issues:
1. Check bot logs for errors
2. Verify bot permissions in all groups
3. Verify .env configuration
4. Test with `/deal_status <deal_id>` to debug deal state
