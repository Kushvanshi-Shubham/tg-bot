# Testing Guide

Quick steps to test the new interactive /deal flow.

## Prerequisites
✅ Bot running (`python -m src.bot`)
✅ At least 1 group in pool (check with `/list_groups`)
✅ Two test accounts (or ask someone to help)

## Test 1: Interactive Deal Creation

### Steps:
1. **Start conversation**: Send `/deal` to the bot in DM
2. **Select role**: Click either "🛒 I'm Buying" or "💰 I'm Selling"
3. **Enter amount**: Type something like `1000 USD` or `50000 INR`
4. **Choose payment**: Click one of the payment method buttons (UPI, Bank Transfer, etc.)
5. **Enter username**: Type counterparty username (e.g., `@testuser` or `testuser`)
6. **Confirm**: Review the summary and click "✅ Confirm & Create Deal"

### Expected Results:
- ✅ Bot sends invite link to both users
- ✅ Deal created with correct role, amount, payment method
- ✅ Both users can join the group

## Test 2: Cancel Flow

### Steps:
1. Send `/deal`
2. Click "❌ Cancel" at any step OR send `/cancel`

### Expected Results:
- ✅ Bot cancels conversation
- ✅ Can start new `/deal` immediately

## Test 3: Error Handling

### Steps:
1. `/deal` → Select role → Enter amount → Choose payment
2. Enter invalid username: `@nonexistentuser123456789`
3. Click "✅ Confirm"

### Expected Results:
- ❌ Bot shows error: "Couldn't find user 'nonexistentuser123456789'"
- ✅ Deal not created
- ✅ No group wasted

## Test 4: Full Deal Flow

After deal creation, test the complete flow:

1. Both users join group via invite link
2. Seller clicks [✅ Accept]
3. Seller clicks [💰 Send Payment]
4. Seller runs `/submit_tx <deal_id> abc123 100 TRC20`
5. Admin clicks [✅ Verified]
6. Buyer clicks [✅ I've Sent Fiat]
7. Seller clicks [✅ Fiat Received]
8. Admin clicks [🔓 Release USDT]

### Expected Results:
- ✅ All buttons work in sequence
- ✅ Deal transitions through states: pending → accepted → paid → fiat_sent → fiat_received → released → closed
- ✅ Group is freed after completion

## Test 5: Payment Methods

### Steps:
1. Check `.env` has `PAYMENT_METHODS=UPI,Bank Transfer,CDM,Cash Deposit,PayPal`
2. Start `/deal` flow
3. Check payment method buttons

### Expected Results:
- ✅ All 5 methods appear as buttons (2 per row)
- ✅ Selected method appears in confirmation summary
- ✅ Method stored in database

## Admin Commands

Test these while deals are active:

- `/list_groups` — Shows all groups with Free/Occupied status
- `/deal_status` — Shows list of recent deals
- `/release_group -5004801923` — Manually frees a stuck group
- `/reset_groups` — Resets all groups to Free (⚠️ use carefully)

## Common Issues

### "No deal rooms available"
- Check: `/list_groups` to see if any groups are Free
- Fix: `/reset_groups` or `/release_group <chat_id>`

### "Couldn't find user"
- Make sure the user has:
  - Started the bot (`/start`)
  - Public @username OR you're using their numeric ID

### Invite link doesn't work
- Check bot permissions in group:
  - Bot must be admin
  - Must have "Can invite users via link" permission

### Conversation stuck
- Send `/cancel` to reset
- Or wait for timeout (if implemented)

## Payment Methods Configuration

Add custom payment methods in `.env`:
```
PAYMENT_METHODS=UPI,NEFT,RTGS,PhonePe,Paytm,Cash,CDM
```

Restart bot after changing `.env`.
