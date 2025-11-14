# Workflow Updates - Main Group Integration

## New Workflow

### 1. **Main TG Group** (Your Community Group)
Users initiate deals by typing:
```
/deal @username
```
or by replying to someone's message:
```
/deal
```

### 2. **Bot Behavior**
- Bot sends deal creation form to user's **DM** (private message)
- User fills out all details in DM (role, currency, amount, INR rate, payment method)
- Upon confirmation, bot:
  - Assigns a **free room** from the pool
  - Creates **join request link** (not auto-join)
  - Sends invite link to:
    - ✅ Deal initiator (DM)
    - ✅ Tagged counterparty (DM)
    - ✅ Main group (public announcement)

### 3. **Join Request Auto-Approval**
Bot automatically **approves** join requests ONLY for:
- ✅ User who typed `/deal`
- ✅ Tagged counterparty
- ✅ Admin (from ADMIN_IDS in .env)

❌ All other users are **declined**

### 4. **Private Deal Room Flow**
Once both users join the private room:
1. Both click "Confirm" to start the deal
2. Seller selects network (BSC/TRON/BASE/SOL/OTHER)
3. Seller selects token (USDT/USDC)
4. Bot shows admin deposit address
5. Seller submits transaction with `/submit_tx`
6. Admin verifies payment (clicks "Verified ✅")
7. Buyer marks "I've Sent Fiat 💸"
8. Seller marks "Fiat Received ✅"
9. Both click their "Completed" buttons
10. Bot kicks both users and frees the room

## Technical Changes

### Files Modified:

1. **src/bot.py**
   - Added `ChatJoinRequestHandler` import
   - Added `handle_chat_join_request()` function
     - Auto-approves: initiator, target, admin
     - Auto-declines: everyone else
   - Registered handler in `main()`

2. **src/deal_conversation.py**
   - Updated `deal_start()`:
     - Requires counterparty to be tagged
     - Stores main group ID if command is from group
     - Sends deal form to user's DM
     - Confirms in group that DM was sent
   - Updated `deal_confirmed()`:
     - Sends invite link to main group (if applicable)
     - Shows public announcement with deal details

### Environment Variables:
No new variables needed. Existing config is used:
- `BOT_TOKEN`
- `ADMIN_IDS` (comma-separated list)
- `GROUP_CHAT_IDS` (deal room pool)
- Network addresses (ADMIN_USDT_*, ADMIN_USDC_*)

## Testing Checklist

### Setup:
- [ ] Database migrated (deleted old deals.db)
- [ ] Bot restarted
- [ ] Admin addresses configured in .env
- [ ] Bot is admin in main group
- [ ] Bot is admin in all deal rooms

### Test Flow:
1. [ ] In main group, type `/deal @counterparty`
2. [ ] Verify bot sends DM to you
3. [ ] Verify bot confirms in main group
4. [ ] Complete deal form in DM
5. [ ] Verify invite link sent to:
   - [ ] Your DM
   - [ ] Counterparty's DM
   - [ ] Main group (public announcement)
6. [ ] Both users click invite link
7. [ ] Verify bot auto-approves both join requests
8. [ ] Verify admin can also join (auto-approved)
9. [ ] Try random user joining → should be declined
10. [ ] Complete full deal flow in private room
11. [ ] Verify both users kicked after completion
12. [ ] Verify room freed for next deal

## User Experience

### Before (Old Flow):
❌ Users couldn't initiate deals from main group
❌ Anyone could join deal rooms
❌ No public tracking of deals

### After (New Flow):
✅ Users initiate from main group with `/deal @user`
✅ Deal details shown publicly in main group
✅ Only authorized users can join private rooms
✅ Admin can monitor all deal rooms
✅ Clean separation: public announcements + private execution

## Security Features

1. **Join Request Validation**: Only deal participants + admin can join
2. **Dual Confirmation**: Both parties must confirm before proceeding
3. **Admin Oversight**: Admin can join any deal room to monitor
4. **Auto-Kick**: Users removed after deal completion
5. **Room Recycling**: Freed rooms are cleaned and reused

## Commands

### User Commands:
- `/start` - Start the bot (in DM)
- `/deal @username` - Create new deal (in main group or DM)
- `/submit_tx` - Submit transaction proof (in deal room)
- `/deal_status <deal_id>` - Check deal status

### Admin Commands:
- `/list_groups` - Show all rooms and their status
- `/release_group <chat_id>` - Manually free a room
- `/reset_groups` - Reset all rooms to free status

## Notes

- All deal creation happens in **DM** for privacy
- Main group only shows **announcements** (deal created, invite link)
- Private rooms are used for **actual deal execution**
- Bot must be **admin** in all groups (main + deal rooms)
- Join request approval requires bot to have **"Invite users via link"** permission
