"""
Main Telegram bot for deal flow with group pool.

Copyright (c) 2025 @killerbesto
Bot Developer: @killerbesto
All Rights Reserved.
"""
from __future__ import annotations

import os
import logging
import asyncio
from typing import Optional

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    filters,
)
from telegram.error import TelegramError

from . import db

load_dotenv()

# Bot metadata - DO NOT REMOVE - PROTECTED BY LICENSE
__author__ = "@killerbesto"
__copyright__ = "Copyright (c) 2025 @killerbesto"
__version__ = "1.0.0"
__license__ = "Proprietary"
__developer__ = "https://t.me/killerbesto"

# Copyright validation - DO NOT MODIFY
_REQUIRED_CREDITS = {
    "developer": "@killerbesto",
    "telegram": "https://t.me/killerbesto",
    "year": "2025"
}

def _verify_integrity():
    """Verify copyright notices are intact - DO NOT REMOVE"""
    if __author__ != "@killerbesto":
        raise RuntimeError("Copyright violation detected")
    if "killerbesto" not in __copyright__.lower():
        raise RuntimeError("Copyright violation detected")
    return True

# Validate on import
_verify_integrity()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
USDT_ADDRESS = os.environ.get("USDT_ADDRESS", "")
MAIN_GROUP_ID = int(os.environ.get("MAIN_GROUP_ID", "0")) if os.environ.get("MAIN_GROUP_ID") else None
GROUP_CHAT_IDS = [int(x.strip()) for x in os.environ.get("GROUP_CHAT_IDS", "").split(",") if x.strip()]

# Message constants
MSG_DEAL_NOT_FOUND = "Deal not found."
MSG_THE_SELLER = "the seller"
MSG_THE_BUYER = "the buyer"
MSG_THE_INITIATOR = "the initiator"
MSG_THE_COUNTERPARTY = "the counterparty"
DEVELOPER_CREDIT = "@killerbesto"
BOT_SIGNATURE = f"🤖 Bot by {DEVELOPER_CREDIT}"
BOT_DEVELOPER_CREDIT = f"🤖 Bot developed by {DEVELOPER_CREDIT}"
LOGS_GROUP_ID = int(os.environ.get("LOGS_GROUP_ID", "0")) if os.environ.get("LOGS_GROUP_ID") else None
PAYMENT_METHODS = [x.strip() for x in os.environ.get("PAYMENT_METHODS", "UPI,Bank Transfer,CDM,Cash Deposit,PayPal").split(",") if x.strip()]


def get_user_display_name(chat):
    """Get user display name with username priority"""
    if chat.username:
        return f"@{chat.username}"
    return chat.full_name or chat.first_name or f"User {chat.id}"


# Network-specific addresses
ADMIN_USDT_BSC = os.environ.get("ADMIN_USDT_BSC", "")
ADMIN_USDT_TRON = os.environ.get("ADMIN_USDT_TRON", "")
ADMIN_USDT_BASE = os.environ.get("ADMIN_USDT_BASE", "")
ADMIN_USDT_SOL = os.environ.get("ADMIN_USDT_SOL", "")

ADMIN_USDC_BSC = os.environ.get("ADMIN_USDC_BSC", "")
ADMIN_USDC_TRON = os.environ.get("ADMIN_USDC_TRON", "")
ADMIN_USDC_BASE = os.environ.get("ADMIN_USDC_BASE", "")
ADMIN_USDC_SOL = os.environ.get("ADMIN_USDC_SOL", "")

SURCHARGE_NON_BSC = 0.70  # $0.70 surcharge for non-BSC networks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_log_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send notification to logs/admin group."""
    if LOGS_GROUP_ID:
        try:
            await context.bot.send_message(chat_id=LOGS_GROUP_ID, text=message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send log notification: {e}")


# Helper function to get admin address by network and token
def get_admin_address(network: str, token: str) -> str:
    """Get admin receiving address based on network and token."""
    token = token or "USDT"
    if token == "USDT":
        if network == "BSC": return ADMIN_USDT_BSC
        if network == "TRON": return ADMIN_USDT_TRON
        if network == "BASE": return ADMIN_USDT_BASE
        if network == "SOL": return ADMIN_USDT_SOL
    elif token == "USDC":
        if network == "BSC": return ADMIN_USDC_BSC
        if network == "TRON": return ADMIN_USDC_TRON
        if network == "BASE": return ADMIN_USDC_BASE
        if network == "SOL": return ADMIN_USDC_SOL
    return "(configure address in .env)"


async def _show_deal_summary_for_acceptance(context: ContextTypes.DEFAULT_TYPE, deal_id: int, deal: dict) -> None:
    """Show deal summary to counterparty for acceptance/rejection."""
    try:
        initiator_chat = await context.bot.get_chat(deal["initiator_id"])
        target_chat = await context.bot.get_chat(deal["target_id"])
        initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else (initiator_chat.full_name or f"User {deal['initiator_id']}")
        target_name = f"@{target_chat.username}" if target_chat.username else (target_chat.full_name or f"User {deal['target_id']}")
    except Exception:
        initiator_name = f"User {deal['initiator_id']}"
        target_name = f"User {deal['target_id']}"
    
    role = deal.get("initiator_role", "Unknown")
    amount = deal.get("amount", "Unknown")
    network = deal.get("network")
    surcharge = deal.get("surcharge_usdt", 0.0)
    
    # Build summary based on who is initiator (seller or buyer)
    summary = (
        "📋 **Deal Summary - Please Review**\n"
        f"{'='*40}\n\n"
    )
    
    if role == "seller":
        # SELLER initiated - showing to BUYER
        amount_num = amount.split()[0] if isinstance(amount, str) else str(amount)
        summary += (
            f"👤 **{initiator_name}** (SELLER)\n"
            f"� **{target_name}** (BUYER - You)\n\n"
            f"{'─'*40}\n\n"
            f"�💰 **USDT Amount:** {amount_num} USDT\n"
        )
        if network:
            surcharge_text = "" if surcharge == 0 else f" (+${surcharge} surcharge)"
            summary += f"🌐 **Network:** {network}{surcharge_text}\n"
        summary += "\n**After accepting, you will propose your INR rate.**\n\n"
    else:
        # BUYER initiated - showing to SELLER
        inr_rate = deal.get("inr_rate")
        payment_method = deal.get("payment_method")
        amount_num = amount.split()[0] if isinstance(amount, str) else str(amount)
        
        summary += (
            f"👤 **{initiator_name}** (BUYER)\n"
            f"� **{target_name}** (SELLER - You)\n\n"
            f"{'─'*40}\n\n"
            f"�💰 **INR Amount:** ₹{amount_num}\n"
        )
        if inr_rate:
            summary += f"📊 **Rate:** ₹{inr_rate}/USDT\n"
            try:
                inr_val = float(amount_num.replace(',', ''))
                rate_val = float(str(inr_rate).replace(',', ''))
                usdt_equiv = inr_val / rate_val
                summary += f"💵 **You will send:** ~{usdt_equiv:.2f} USDT\n"
            except Exception:
                pass
        if payment_method:
            summary += f"💳 **Payment Method:** {payment_method}\n"
    
    summary += f"\n{'='*40}\n\n"
    summary += f"**{target_name}, please review and accept or reject:**"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept Deal", callback_data=f"accept_deal:{deal_id}")],
        [InlineKeyboardButton("❌ Reject Deal", callback_data=f"reject_deal:{deal_id}")],
    ])
    
    await context.bot.send_message(
        chat_id=deal["group_chat_id"],
        text=summary,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Welcome to the P2P Deal Bot.\n\n"
        "Use /deal to create a new deal with step-by-step guidance.\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"{BOT_DEVELOPER_CREDIT}\n"
        "© 2025 All Rights Reserved"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the current deal for the user."""
    msg = update.message
    user_id = msg.from_user.id
    
    # Check if message is in a group
    if msg.chat.type in ["group", "supergroup"]:
        # Get deal for this group
        deal = await db.get_deal_by_group(msg.chat_id)
        if not deal:
            await msg.reply_text("❌ No active deal found in this group.")
            return
        
        # Check if user is part of this deal
        if user_id != deal["initiator_id"] and user_id != deal.get("target_id"):
            await msg.reply_text("❌ You are not part of this deal.")
            return
        
        # Check if deal is already completed or cancelled
        if deal.get("status") in ["completed", "cancelled", "closed"]:
            await msg.reply_text(f"❌ This deal is already {deal.get('status')}.")
            return
        
        # Cancel the deal
        await db.update_deal_status(deal["id"], "cancelled")
        await msg.reply_text("✅ Deal cancelled successfully.")
        
        # Release group and notify users to leave manually
        if deal.get("group_chat_id"):
            await db.release_group(deal["group_chat_id"])
            try:
                await context.bot.send_message(
                    chat_id=deal["group_chat_id"],
                    text="❌ Deal cancelled! Please leave the room manually. Thank you!"
                )
            except Exception as e:
                logger.exception("Failed to send leave message: %s", e)
    else:
        # In DM, just show info
        await msg.reply_text(
            "❌ Cancel command only works in deal groups.\n\n"
            "Use the 'Cancel Deal' button during deal setup."
        )


# Old /deal command - now replaced by conversation handler in deal_conversation.py
# Keeping this for reference, but it's no longer used
    """
    /deal @username
    - Get free group from pool
    - Create deal record
    - Create invite link with member_limit=2
    - Send invite link to both users
    """
    msg = update.message
    args = context.args
    if not args:
        await msg.reply_text("Usage: /deal @username")
        return

    target = args[0].strip()
    
    # auto-add @ if missing and not a numeric ID
    if not target.startswith("@") and not target.isdigit():
        target = f"@{target}"

    # try to resolve username using get_chat
    target_chat = None
    try:
        target_chat = await context.bot.get_chat(target)
    except Exception as e:
        logger.info("get_chat failed for %s: %s", target, e)

    if not target_chat:
        await msg.reply_text(
            f"❌ Couldn't find user '{target}'.\n\n"
            "Make sure:\n"
            "• They have a public @username, OR\n"
            "• They've sent /start to the bot first\n\n"
            "You can also use their numeric user ID instead of username."
        )
        return

    initiator_id = msg.from_user.id
    target_id = target_chat.id

    # get a free group from pool
    free_group = await db.get_free_group()
    if not free_group:
        # check if any groups exist at all
        total_groups = len(GROUP_CHAT_IDS)
        await msg.reply_text(
            "❌ No deal rooms available right now.\n"
            f"Total groups in pool: {total_groups}\n\n"
            "Admin can check status with /list_groups and free stuck groups with /release_group <chat_id>"
        )
        return

    group_chat_id = free_group["chat_id"]

    # create invite link with member_limit=2 (buyer + seller)
    try:
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=group_chat_id,
            member_limit=2,
            name=f"Deal {initiator_id}-{target_id}",
        )
        invite_link = invite_link_obj.invite_link
    except TelegramError as e:
        logger.exception("Failed to create invite link: %s", e)
        await msg.reply_text("Failed to create invite link. Make sure the bot is admin in the group.")
        return

    # create deal record
    deal_id = await db.create_deal(
        initiator_id=initiator_id,
        target_id=target_id,
        group_chat_id=group_chat_id,
        usdt_address=USDT_ADDRESS,
        invite_link=invite_link,
    )

    # DON'T occupy the group yet - wait for both users to join
    # It will be occupied in handle_new_chat_members when both are present

    # send invite link to both users
    instructions = (
        f"Deal request created (ID {deal_id}).\n"
        f"Click the link below to join the private deal room:\n{invite_link}\n\n"
        "Once both of you join, the seller will be asked to accept the deal."
    )
    
    # send to initiator
    initiator_sent = False
    target_sent = False
    
    try:
        await context.bot.send_message(chat_id=initiator_id, text=instructions)
        initiator_sent = True
    except Exception as e:
        logger.exception("Failed to send to initiator: %s", e)
    
    # send to target
    try:
        await context.bot.send_message(chat_id=target_id, text=instructions)
        target_sent = True
    except Exception as e:
        logger.exception("Failed to send to target: %s", e)
    
    # give feedback
    if initiator_sent and target_sent:
        await msg.reply_text(f"Deal request sent (ID {deal_id}). Invite links sent to both users.")
    elif initiator_sent and not target_sent:
        await msg.reply_text(
            f"Deal request created (ID {deal_id}).\n"
            "✅ Invite link sent to you.\n"
            f"❌ Could not send to {target}. They must send /start to the bot first.\n\n"
            f"Share this link with them manually:\n{invite_link}"
        )
    elif not initiator_sent and target_sent:
        await msg.reply_text(f"Deal request created (ID {deal_id}). Link sent to {target}. Check your DMs for the link.")
    else:
        await msg.reply_text(
            f"Deal request created (ID {deal_id}).\n"
            f"Could not send DMs to either user. Here's the invite link:\n{invite_link}"
        )


async def handle_chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-approve join requests for deal participants and admin only."""
    join_request = update.chat_join_request
    if not join_request:
        return

    group_chat_id = join_request.chat.id
    user_id = join_request.from_user.id

    # Get deal for this group
    deal = await db.get_deal_by_group(group_chat_id)
    if not deal:
        # No deal found for this group, decline
        try:
            await context.bot.decline_chat_join_request(chat_id=group_chat_id, user_id=user_id)
            logger.info(f"Declined join request from {user_id} - no active deal in group {group_chat_id}")
        except Exception as e:
            logger.exception(f"Failed to decline join request: {e}")
        return

    # Check if user is authorized (initiator, target, or admin)
    is_authorized = (
        user_id == deal["initiator_id"] or
        user_id == deal.get("target_id") or
        user_id in ADMIN_IDS
    )

    if is_authorized:
        # Approve the join request
        try:
            await context.bot.approve_chat_join_request(chat_id=group_chat_id, user_id=user_id)
            logger.info(f"Approved join request for user {user_id} in deal #{deal['id']}")
        except Exception as e:
            logger.exception(f"Failed to approve join request: {e}")
    else:
        # Decline unauthorized users
        try:
            await context.bot.decline_chat_join_request(chat_id=group_chat_id, user_id=user_id)
            logger.info(f"Declined join request from unauthorized user {user_id} in deal #{deal['id']}")
        except Exception as e:
            logger.exception(f"Failed to decline join request: {e}")


async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detect when users join the group and start the deal flow."""
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    group_chat_id = msg.chat_id

    # get deal for this group
    deal = await db.get_deal_by_group(group_chat_id)
    if not deal:
        return

    # check if both participants have joined
    try:
        initiator_member = await context.bot.get_chat_member(chat_id=group_chat_id, user_id=deal["initiator_id"])
        target_member = await context.bot.get_chat_member(chat_id=group_chat_id, user_id=deal["target_id"])
    except Exception as e:
        logger.exception("Failed to check members: %s", e)
        return

    initiator_joined = initiator_member.status in ["member", "administrator", "creator"]
    target_joined = target_member.status in ["member", "administrator", "creator"]

    # Show member count when someone joins
    member_count = (1 if initiator_joined else 0) + (1 if target_joined else 0)
    
    # Show who just joined
    for new_member in msg.new_chat_members:
        username = f"@{new_member.username}" if new_member.username else (new_member.full_name or new_member.first_name)
        await context.bot.send_message(
            chat_id=group_chat_id,
            text=f"👋 {username} joined the deal room ({member_count}/2 members)"
        )

    if not (initiator_joined and target_joined):
        # not both joined yet, wait
        return

    # Both joined! Now occupy the group and start the deal flow
    await db.occupy_group(group_chat_id, deal["id"])
    
    # Send "Deal in Progress" message to MAIN GROUP
    if MAIN_GROUP_ID:
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            target_chat = await context.bot.get_chat(deal["target_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else (initiator_chat.full_name or f"User {deal['initiator_id']}")
            target_name = f"@{target_chat.username}" if target_chat.username else (target_chat.full_name or f"User {deal['target_id']}")
            
            await context.bot.send_message(
                chat_id=MAIN_GROUP_ID,
                text=f"🔄 Deal #{deal['id']} in Progress\n\n👤 {initiator_name}\n👤 {target_name}"
            )
        except Exception as e:
            logger.exception("Failed to send deal in progress message to main group: %s", e)
    
    # If deal role is still "pending", ask initiator to select role
    if deal.get("initiator_role") == "pending" and deal["status"] == "pending":
        # Get user details
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            target_chat = await context.bot.get_chat(deal["target_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else (initiator_chat.full_name or f"User {deal['initiator_id']}")
            target_name = f"@{target_chat.username}" if target_chat.username else (target_chat.full_name or f"User {deal['target_id']}")
        except Exception:
            initiator_name = f"User {deal['initiator_id']}"
            target_name = f"User {deal['target_id']}"
        
        # Welcome message
        welcome_msg = (
            f"👋 Welcome to Deal #{deal['id']}!\n\n"
            f"👤 Initiator: {initiator_name}\n"
            f"👤 Counterparty: {target_name}\n\n"
            "Let's start the deal process!\n"
            f"{initiator_name}, please select your role:"
        )
        
        # Role selection for initiator - simplified (only "I'm Selling" button)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("� I am the Seller", callback_data=f"start_role:{deal['id']}:seller")],
            [InlineKeyboardButton("� I am the Buyer", callback_data=f"start_role:{deal['id']}:buyer")],
            [InlineKeyboardButton("❌ Cancel Deal", callback_data=f"start_cancel:{deal['id']}")],
        ])
        
        await context.bot.send_message(
            chat_id=group_chat_id,
            text=welcome_msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages in deal groups for amount, INR rate, payment method input."""
    msg = update.message
    if not msg or not msg.text:
        return

    # Only process in groups
    if msg.chat.type not in ["group", "supergroup"]:
        return

    # Get deal for this group
    deal = await db.get_deal_by_group(msg.chat_id)
    if not deal:
        return

    text = msg.text.strip()
    
    # Handle buyer proposing rate AFTER accepting deal
    if deal.get("status") == "awaiting_buyer_rate":
        # Only buyer can propose rate
        role = deal.get("initiator_role")
        seller_is_initiator = (role == "seller")
        buyer_id = deal["target_id"] if seller_is_initiator else deal["initiator_id"]
        
        if msg.from_user.id != buyer_id:
            return  # Only buyer can input rate at this stage
        
        try:
            rate_val = float(text.replace(',', ''))
            if rate_val <= 0:
                raise ValueError
        except ValueError:
            await msg.reply_text("❌ Please enter a valid rate (e.g., 92):")
            return
        
        # Save the rate
        await db.update_deal(deal["id"], inr_rate=text)
        
        # Calculate total with fee
        amount_str = deal.get("amount", "0")
        amount_num = float(amount_str.split()[0]) if isinstance(amount_str, str) else 0
        network = deal.get("network", "BSC")
        surcharge = 0.0 if network == "BSC" else SURCHARGE_NON_BSC
        total_usdt = amount_num + surcharge
        total_inr = total_usdt * rate_val
        
        # Get seller info
        seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
        try:
            seller_chat = await context.bot.get_chat(seller_id)
            seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or f"User {seller_id}")
            buyer_chat = await context.bot.get_chat(buyer_id)
            buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else (buyer_chat.full_name or f"User {buyer_id}")
        except Exception:
            seller_name = f"User {seller_id}"
            buyer_name = f"User {buyer_id}"
        
        # Show detailed calculation to seller for approval
        summary = (
            "📊 **Rate Proposal from Buyer**\n"
            f"{'='*40}\n\n"
            f"💱 **Proposed Rate:** ₹{rate_val}/USDT\n\n"
            "📝 **Calculation:**\n"
            f"• USDT Amount: {amount_num} USDT\n"
            f"• Network: {network}\n"
        )
        
        if surcharge > 0:
            summary += f"• Network Fee: +${surcharge} USDT\n"
        
        summary += (
            f"• **Total USDT:** {total_usdt} USDT\n\n"
            f"💰 **Seller will receive:** ₹{total_inr:.2f}\n\n"
            f"{'='*40}\n\n"
            f"**{seller_name}, do you accept this rate?**"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept Rate", callback_data=f"accept_rate:{deal['id']}")],
            [InlineKeyboardButton("❌ Reject Rate", callback_data=f"reject_rate:{deal['id']}")],
        ])
        
        await msg.reply_text(summary, reply_markup=keyboard, parse_mode="Markdown")
        return

    # Handle seller submitting TX link
    if deal.get("status") == "awaiting_tx_link":
        # Only seller can submit TX link
        role = deal.get("initiator_role")
        seller_is_initiator = (role == "seller")
        seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
        
        if msg.from_user.id != seller_id:
            return  # Only seller can submit TX link
        
        # Validate it's a URL
        if not (text.startswith("http://") or text.startswith("https://")):
            await msg.reply_text("❌ Please send a valid transaction explorer link (must start with http:// or https://)")
            return
        
        # Save TX link
        await db.update_deal(deal["id"], tx_link=text)
        await db.update_deal_status(deal["id"], "verified")  # Move to verified status
        
        await msg.reply_text("✅ Transaction link submitted successfully!")
        
        # Notify admin to verify
        admin_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verify TX", callback_data=f"verified:{deal['id']}")],
            [InlineKeyboardButton("❌ Reject TX", callback_data=f"reject_tx:{deal['id']}")],
        ])
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text=(
                "🔍 **Transaction Submitted - Admin Review Required**\n\n"
                f"🔗 TX Link: {text}\n\n"
                "Admin: Please verify the transaction and click below."
            ),
            reply_markup=admin_buttons
        )
        return

    # Only process setup messages from initiator during pending status
    # Allow free chat during other statuses
    if deal.get("status") not in ["pending"]:
        # Deal in progress - allow free chat between users
        return
    
    if msg.from_user.id != deal["initiator_id"]:
        # Not the initiator during setup - ignore
        return

    # Check what we're waiting for based on deal state
    # Waiting for amount (currency is set, amount is still "pending")
    if deal.get("currency") and deal.get("currency") != "pending" and deal.get("amount") == "pending":
        try:
            amount_val = float(text.replace(',', ''))
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            await msg.reply_text("❌ Please enter a valid number for amount.")
            return

        role = deal.get("initiator_role", "")
        # Both seller and buyer enter USDT amount
        amount_text = f"{text} USDT"
        await db.update_deal(deal["id"], amount=amount_text)
        await msg.reply_text(f"✅ Amount: {amount_text}")

        currency = deal.get("currency", "")

        # NEW LOGIC: Seller=USDT, Buyer=INR
        if role == "seller":
            # Seller is selling USDT - ask for network
            await msg.reply_text(
                "🌐 Select the blockchain network for this deal:\n"
                "⚠️ BSC has NO surcharge, other networks add +$0.70"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("BSC (BEP20) - No Fee", callback_data=f"start_network:{deal['id']}:BSC")],
                [InlineKeyboardButton("TRON (TRC20) +$0.70", callback_data=f"start_network:{deal['id']}:TRON")],
                [InlineKeyboardButton("BASE +$0.70", callback_data=f"start_network:{deal['id']}:BASE")],
                [InlineKeyboardButton("Solana +$0.70", callback_data=f"start_network:{deal['id']}:SOL")],
            ])
            await msg.reply_text("Select network:", reply_markup=keyboard)
        else:
            # Buyer is paying INR - ask for rate they're willing to pay
            await msg.reply_text("💱 Please type the INR to USDT rate you're willing to pay (e.g., 92):")

    # Waiting for INR rate (from buyer)
    elif deal.get("amount") != "pending" and not deal.get("inr_rate"):
        try:
            rate_val = float(text.replace(',', ''))
            if rate_val <= 0:
                raise ValueError
        except ValueError:
            await msg.reply_text("❌ Please enter a valid rate (e.g., 92):")
            return

        await db.update_deal(deal["id"], inr_rate=text)
        await msg.reply_text(f"✅ INR Rate: ₹{text}/USDT")

        # After buyer enters rate, ask for payment method
        keyboard_buttons = []
        for i in range(0, len(PAYMENT_METHODS), 2):
            row = [InlineKeyboardButton(PAYMENT_METHODS[i], callback_data=f"start_payment:{deal['id']}:{PAYMENT_METHODS[i]}")]
            if i + 1 < len(PAYMENT_METHODS):
                row.append(InlineKeyboardButton(PAYMENT_METHODS[i + 1], callback_data=f"start_payment:{deal['id']}:{PAYMENT_METHODS[i + 1]}"))
            keyboard_buttons.append(row)
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        await msg.reply_text("💳 Select payment method (for INR transfer):", reply_markup=keyboard)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    # ✅ DON'T call q.answer() here - call it after validation in each handler
    data = q.data

    # Handle role selection at deal start
    if data.startswith("start_role:"):
        _, deal_id_str, role = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.answer(MSG_DEAL_NOT_FOUND, show_alert=True)
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the initiator
        if q.from_user.id != deal["initiator_id"]:
            try:
                initiator_chat = await context.bot.get_chat(deal["initiator_id"])
                initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            except Exception:
                initiator_name = MSG_THE_INITIATOR
            await q.answer(f"⚠️ This is the INITIATOR's action. Wait for {initiator_name} to select role.", show_alert=True)
            return
        
        await q.answer()  # Acknowledge the callback query

        # Update role
        await db.update_deal(deal_id, initiator_role=role)
        
        # Set currency based on role:
        # SELLER = selling USDT (crypto)
        # BUYER = paying INR
        if role == "seller":
            # Seller sells USDT
            await db.update_deal(deal_id, currency="crypto")
            await q.edit_message_text(
                "💰 Role selected: SELLER\n"
                "💵 You are selling: USDT\n\n"
                "Please type the USDT amount you want to sell (e.g., 100):"
            )
        else:
            # Buyer pays INR, receives USDT
            await db.update_deal(deal_id, currency="inr")
            await q.edit_message_text(
                "🛒 Role selected: BUYER\n"
                "💵 You are paying with: INR\n"
                "🪙 You will receive: USDT\n\n"
                "Please type the USDT amount you want to buy (e.g., 100):"
            )

    # DEPRECATED: Currency selection removed - USDT only now
    # elif data.startswith("start_currency:"):

    elif data.startswith("start_network:"):
        _, deal_id_str, network = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the initiator
        if q.from_user.id != deal["initiator_id"]:
            try:
                initiator_chat = await context.bot.get_chat(deal["initiator_id"])
                initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            except Exception:
                initiator_name = MSG_THE_INITIATOR
            await q.answer(f"⚠️ This is the INITIATOR's action. Wait for {initiator_name} to select the network.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        # Calculate surcharge
        surcharge = 0.0 if network == "BSC" else SURCHARGE_NON_BSC
        
        # Update network and surcharge
        await db.update_deal(deal_id, network=network, surcharge_usdt=surcharge)
        
        surcharge_text = "" if network == "BSC" else f" (+${surcharge} surcharge)"
        await q.edit_message_text(f"✅ Network: {network}{surcharge_text}")
        
        # Update token to USDT (always USDT only)
        await db.update_deal(deal_id, token_symbol="USDT")
        
        # Show summary to counterparty (buyer) for acceptance
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text="� Preparing deal summary for buyer..."
        )
        await _show_deal_summary_for_acceptance(context, deal_id, deal)

    elif data.startswith("start_payment:"):
        _, deal_id_str, payment = data.split(":", 2)
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the initiator
        if q.from_user.id != deal["initiator_id"]:
            try:
                initiator_chat = await context.bot.get_chat(deal["initiator_id"])
                initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            except Exception:
                initiator_name = MSG_THE_INITIATOR
            await q.answer(f"⚠️ This is the INITIATOR's action. Wait for {initiator_name} to select payment method.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        # Update payment method
        await db.update_deal(deal_id, payment_method=payment)
        await q.edit_message_text(f"✅ Payment Method: {payment}")
        
        # Get user names
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            target_chat = await context.bot.get_chat(deal["target_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else (initiator_chat.full_name or f"User {deal['initiator_id']}")
            target_name = f"@{target_chat.username}" if target_chat.username else (target_chat.full_name or f"User {deal['target_id']}")
        except Exception:
            initiator_name = f"User {deal['initiator_id']}"
            target_name = f"User {deal['target_id']}"
        
        # Determine who is buyer/seller
        role = deal.get("initiator_role", "Unknown")
        amount = deal.get("amount", "Unknown")
        inr_rate = deal.get("inr_rate")
        
        # Build comprehensive summary for BUYER (INR) initiator
        summary = (
            "📋 **Deal Summary - Please Review**\n"
            f"{'='*40}\n\n"
            f"👤 **{initiator_name}** (Initiator - BUYER)\n"
            f"👤 **{target_name}** (Counterparty - SELLER)\n\n"
            f"{'─'*40}\n\n"
        )
        
        # Buyer is paying INR
        summary += f"💰 **INR Amount:** {amount}\n"
        if inr_rate:
            summary += f"📊 **Rate:** ₹{inr_rate}/USDT\n"
            try:
                # Calculate USDT equivalent
                inr_val = float(amount.split()[0].replace(',', ''))
                rate_val = float(str(inr_rate).replace(',', ''))
                usdt_equiv = inr_val / rate_val
                summary += f"💵 **You will receive:** ~{usdt_equiv:.2f} USDT\n"
            except Exception:
                pass
        
        summary += f"💳 **Payment Method:** {payment}\n\n"
        summary += f"{'='*40}\n\n"
        summary += f"**{target_name}, please review and accept or reject this deal:**"
        
        # Only counterparty needs to confirm/reject
        keyboard_target = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept Deal", callback_data=f"accept_deal:{deal_id}")],
            [InlineKeyboardButton("❌ Reject Deal", callback_data=f"reject_deal:{deal_id}")],
        ])
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text=summary,
            reply_markup=keyboard_target,
            parse_mode="Markdown"
        )

    elif data.startswith("accept_deal:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the counterparty (target)
        if q.from_user.id != deal["target_id"]:
            try:
                target_chat = await context.bot.get_chat(deal["target_id"])
                target_name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
            except Exception:
                target_name = MSG_THE_COUNTERPARTY
            await q.answer(f"⚠️ This is the COUNTERPARTY's action. Wait for {target_name} to accept the deal.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await q.edit_message_text("✅ Deal accepted by counterparty!")
        
        # Send notification to logs group
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            target_chat = await context.bot.get_chat(deal["target_id"])
            target_name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
            
            await send_log_notification(
                context,
                "✅ <b>DEAL ACCEPTED</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Initiator: {initiator_name}\n"
                f"Counterparty: {target_name}\n"
                f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}\n"
                "Status: Awaiting rate confirmation"
            )
        except Exception as e:
            logger.error(f"Failed to send acceptance log: {e}")
        
        # Determine who is buyer/seller
        role = deal.get("initiator_role")
        currency = deal.get("currency")
        seller_is_initiator = (role == "seller")
        buyer_id = deal["target_id"] if seller_is_initiator else deal["initiator_id"]
        
        # For crypto deals: Ask ANYONE to propose INR rate (seller or buyer)
        if currency == "crypto":
            await context.bot.send_message(
                chat_id=deal["group_chat_id"],
                text=(
                    "💱 Please type your proposed INR rate per USDT.\n\n"
                    "Example: Type '92' for ₹92/USDT\n\n"
                    "Either party can propose the rate."
                )
            )
            # Set a flag so we know we're waiting for rate
            await db.update_deal(deal_id, status="awaiting_buyer_rate")
        else:
            # INR deal - already has rate, just confirm
            await db.update_deal_status(deal_id, "confirmed")
            
            seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or f"User {seller_id}")
            except Exception:
                seller_name = f"User {seller_id}"
            
            # Add button for seller to submit transaction
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Submit Transaction", callback_data=f"submit_tx_button:{deal_id}")],
            ])
            
            await context.bot.send_message(
                chat_id=deal["group_chat_id"],
                text=(
                    "✅ Deal Confirmed!\n\n"
                    "Next Step:\n"
                    f"Seller ({seller_name}): Click the button below to submit your transaction details.\n"
                    "After admin verification, buyer will send fiat payment proof."
                ),
                reply_markup=keyboard
            )

    elif data.startswith("reject_deal:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the counterparty
        if q.from_user.id != deal["target_id"]:
            try:
                target_chat = await context.bot.get_chat(deal["target_id"])
                target_name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
            except Exception:
                target_name = MSG_THE_COUNTERPARTY
            await q.answer(f"⚠️ This is the COUNTERPARTY's action. Wait for {target_name} to reject or accept.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await q.edit_message_text("❌ Deal rejected by counterparty")
        await db.update_deal_status(deal_id, "cancelled")
        
        # Send notification to logs group
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            target_chat = await context.bot.get_chat(deal["target_id"])
            target_name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
            
            await send_log_notification(
                context,
                "❌ <b>DEAL REJECTED</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Initiator: {initiator_name}\n"
                f"Counterparty: {target_name}\n"
                f"Rejected by: {target_name}\n"
                f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}"
            )
        except Exception as e:
            logger.error(f"Failed to send rejection log: {e}")
        
        # Release group and notify users to leave manually
        if deal.get("group_chat_id"):
            await db.release_group(deal["group_chat_id"])
            try:
                await context.bot.send_message(
                    chat_id=deal["group_chat_id"],
                    text="❌ Deal rejected! Please leave the room manually. Thank you!"
                )
            except Exception as e:
                logger.exception("Failed to send leave message: %s", e)

    elif data.startswith("accept_rate:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the seller
        role = deal.get("initiator_role")
        seller_is_initiator = (role == "seller")
        seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
        
        if q.from_user.id != seller_id:
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or "Seller")
            except Exception:
                seller_name = "Seller"
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to accept/reject the rate.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await q.edit_message_text("✅ Seller accepted the rate!")
        
        # Update status to confirmed
        await db.update_deal_status(deal_id, "confirmed")
        
        # Show deposit address
        network = deal.get("network", "BSC")
        admin_addr = get_admin_address(network, "USDT")
        amount_str = deal.get("amount", "0")
        amount_num = float(amount_str.split()[0]) if isinstance(amount_str, str) else 0
        surcharge = 0.0 if network == "BSC" else SURCHARGE_NON_BSC
        total_usdt = amount_num + surcharge
        
        # Get seller info for button restriction
        try:
            seller_chat = await context.bot.get_chat(seller_id)
            seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or f"User {seller_id}")
        except Exception:
            seller_name = f"User {seller_id}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Submit Transaction", callback_data=f"submit_tx_button:{deal_id}")],
        ])
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text=(
                "📍 **Deposit Address**\n"
                f"{'='*35}\n\n"
                f"💰 **Send exactly:** {total_usdt} USDT\n"
                f"🌐 **Network:** {network}\n"
                "📍 **Address:**\n"
                f"`{admin_addr}`\n\n"
                f"{'='*35}\n\n"
                f"**{seller_name}, after sending, click the button below:**"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    elif data.startswith("reject_rate:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the seller
        role = deal.get("initiator_role")
        seller_is_initiator = (role == "seller")
        seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
        buyer_id = deal["target_id"] if seller_is_initiator else deal["initiator_id"]
        
        if q.from_user.id != seller_id:
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or "Seller")
            except Exception:
                seller_name = "Seller"
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to accept/reject the rate.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await q.edit_message_text("❌ Seller rejected the rate")
        
        # Ask buyer to propose new rate
        try:
            buyer_chat = await context.bot.get_chat(buyer_id)
            buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else (buyer_chat.full_name or f"User {buyer_id}")
        except Exception:
            buyer_name = f"User {buyer_id}"
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text=(
                f"{buyer_name}, please propose a new INR rate.\n\n"
                "Example: Type '92' for ₹92/USDT"
            )
        )

    elif data.startswith("submit_tx_button:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify it's the seller
        role = deal.get("initiator_role")
        seller_is_initiator = (role == "seller")
        seller_id = deal["initiator_id"] if seller_is_initiator else deal["target_id"]
        buyer_id = deal["target_id"] if seller_is_initiator else deal["initiator_id"]
        
        if q.from_user.id != seller_id:
            # Get seller name
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_name = f"@{seller_chat.username}" if seller_chat.username else (seller_chat.full_name or "Seller")
            except Exception:
                seller_name = "Seller"
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to submit the transaction.", show_alert=True)
            return
        
        # Check deal status
        if deal.get("status") != "confirmed":
            await q.answer(f"Deal must be confirmed first. Current status: {deal.get('status')}", show_alert=True)
            return
        
        await q.answer("Please send the transaction explorer link...")
        
        # Set status to awaiting_tx_link so we know we're waiting for seller's TX link
        await db.update_deal(deal_id, status="awaiting_tx_link")
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text=(
                "🔗 Please send the transaction explorer link.\n\n"
                "Example:\n"
                "• BSCScan: https://bscscan.com/tx/0x...\n"
                "• Tronscan: https://tronscan.org/#/transaction/...\n"
                "• Basescan: https://basescan.org/tx/0x...\n"
                "• Solscan: https://solscan.io/tx/..."
            )
        )

    elif data.startswith("start_cancel:"):
        _, deal_id_str = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.answer(MSG_DEAL_NOT_FOUND, show_alert=True)
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await q.edit_message_text("❌ Deal cancelled")
        await db.update_deal_status(deal_id, "cancelled")
        
        # Send notification to logs group
        try:
            initiator_chat = await context.bot.get_chat(deal["initiator_id"])
            initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else initiator_chat.full_name
            target_chat = await context.bot.get_chat(deal["target_id"])
            target_name = f"@{target_chat.username}" if target_chat.username else target_chat.full_name
            
            await send_log_notification(
                context,
                "❌ <b>DEAL CANCELLED</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Initiator: {initiator_name}\n"
                f"Counterparty: {target_name}\n"
                f"Cancelled by: {get_user_display_name(q.from_user)}\n"
                "Status: CANCELLED"
            )
        except Exception as e:
            logger.error(f"Failed to send cancellation log: {e}")
        
        # Release group and notify users to leave manually
        if deal.get("group_chat_id"):
            await db.release_group(deal["group_chat_id"])
            try:
                await context.bot.send_message(
                    chat_id=deal["group_chat_id"],
                    text="❌ Deal cancelled! Please leave the room manually. Thank you!"
                )
            except Exception as e:
                logger.exception("Failed to send leave message: %s", e)

    # OLD network/token handlers - DEPRECATED
    # Network and token are now selected DURING deal setup (start_network/start_token)
    # NOT after acceptance. Keeping for reference only.
    # elif data.startswith("network:"):
    # elif data.startswith("token:"):

    # Old accept/reject handlers - keeping for backward compatibility
    elif data.startswith("accept:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # verify caller is target (seller)
        if q.from_user.id != deal["target_id"]:
            try:
                seller_chat = await context.bot.get_chat(deal["target_id"])
                seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
            except Exception:
                seller_name = MSG_THE_SELLER
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to accept.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        await db.update_deal_status(deal_id, "accepted")
        
        # Get timestamp
        from datetime import datetime
        accepted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced acceptance message with deal summary
        acceptance_msg = (
            f"✅ **Deal #{deal_id} Accepted!**\n"
            f"{'='*35}\n\n"
            f"💰 Amount: {deal.get('amount', 'N/A')}\n"
            f"💱 Currency: {deal.get('currency', 'N/A')}\n"
            f"💳 Payment: {deal.get('payment_method', 'N/A')}\n"
            f"✅ Accepted at: {accepted_time}\n\n"
            "**Next Step:** Seller, click below to submit payment details."
        )
        
        # send instructions and "Send Payment" button
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💰 Send Payment", callback_data=f"send_payment:{deal_id}")]])
        await q.edit_message_text(acceptance_msg, reply_markup=keyboard, parse_mode="Markdown")

    elif data.startswith("reject:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id != deal["target_id"]:
            try:
                seller_chat = await context.bot.get_chat(deal["target_id"])
                seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
            except Exception:
                seller_name = MSG_THE_SELLER
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to reject or accept.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        await db.update_deal_status(deal_id, "rejected")
        await q.edit_message_text(f"❌ Deal {deal_id} rejected by seller.")
        
        # release group immediately
        if deal["group_chat_id"]:
            await db.release_group(deal["group_chat_id"])
            try:
                await context.bot.send_message(
                    chat_id=deal["group_chat_id"],
                    text="Deal rejected. This room is now free for the next deal."
                )
            except Exception as e:
                logger.exception("Failed to send message: %s", e)

    elif data.startswith("send_payment:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id != deal["target_id"]:
            try:
                seller_chat = await context.bot.get_chat(deal["target_id"])
                seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
            except Exception:
                seller_name = MSG_THE_SELLER
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to submit payment.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        # Show enhanced payment instructions with step-by-step guide
        payment_msg = (
            f"💰 **Payment Instructions - Deal #{deal_id}**\n"
            f"{'='*35}\n\n"
            "📋 **Deal Summary:**\n"
            f"• Amount: {deal.get('amount', 'N/A')}\n"
            f"• Currency: {deal.get('currency', 'N/A')}\n"
            f"• Payment: {deal.get('payment_method', 'N/A')}\n\n"
            "💳 **Send USDT to:**\n"
            f"`{USDT_ADDRESS}`\n\n"
            f"{'='*35}\n"
            "**After sending, click the button above to submit transaction details.**"
        )
        
        await q.edit_message_text(payment_msg, parse_mode="Markdown")

    elif data.startswith("verified:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id not in ADMIN_IDS:
            await q.answer("⚠️ This is an ADMIN action. Only admins can verify transactions.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await db.update_deal_status(deal_id, "verified")
        
        # Send notification to logs group
        try:
            await send_log_notification(
                context,
                "✅ <b>TX VERIFIED BY ADMIN</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Admin: {get_user_display_name(q.from_user)}\n"
                f"TX Hash: {deal.get('tx_hash', 'N/A')}\n"
                f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}\n"
                f"Network: {deal.get('network', 'N/A')}\n"
                "Status: Verified - Awaiting fiat payment"
            )
        except Exception as e:
            logger.error(f"Failed to send verification log: {e}")
        
        # Determine buyer
        buyer_id = deal["initiator_id"] if deal.get("initiator_role") == "buyer" else deal.get("target_id")
        
        try:
            buyer_chat = await context.bot.get_chat(buyer_id)
            buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else (buyer_chat.full_name or f"User {buyer_id}")
        except Exception:
            buyer_name = f"User {buyer_id}"
        
        # Notify about USDT verification and ask buyer to send fiat + proof
        await q.edit_message_text(
            "✅ **USDT Payment Verified by Admin!**\n\n"
            f"{buyer_name} (Buyer):\n"
            "1. Send INR/fiat payment to seller\n"
            "2. Upload payment screenshot/proof as image\n"
            "3. Click 'Sent Fiat' button below\n\n"
            "⚠️ Make sure to send proof before clicking!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ I've Sent Fiat + Proo", callback_data=f"fiat_sent:{deal_id}")
            ]]),
            parse_mode="Markdown"
        )

    elif data.startswith("fiat_sent:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify caller is buyer
        buyer_id = deal["initiator_id"] if deal.get("initiator_role") == "buyer" else deal.get("target_id")
        if q.from_user.id != buyer_id:
            try:
                buyer_chat = await context.bot.get_chat(buyer_id)
                buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else buyer_chat.full_name
            except Exception:
                buyer_name = MSG_THE_BUYER
            await q.answer(f"⚠️ This is the BUYER's action. Wait for {buyer_name} to confirm fiat sent.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await db.update_deal_status(deal_id, "fiat_sent")
        
        # Send notification to logs group
        try:
            buyer_chat = await context.bot.get_chat(buyer_id)
            buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else buyer_chat.full_name
            
            await send_log_notification(
                context,
                "💰 <b>FIAT SENT BY BUYER</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Buyer: {buyer_name}\n"
                f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}\n"
                f"Payment Method: {deal.get('payment_method', 'N/A')}\n"
                "Status: Awaiting seller confirmation"
            )
        except Exception as e:
            logger.error(f"Failed to send fiat sent log: {e}")
        
        # Ask seller to confirm
        await q.edit_message_text(
            "✅ **Buyer sent fiat**\n\n"
            "Seller, click below when you receive the fiat payment.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Fiat Received", callback_data=f"fiat_received:{deal_id}")
            ]]),
            parse_mode="Markdown"
        )

    elif data.startswith("fiat_received:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Verify caller is seller
        seller_id = deal["target_id"] if deal.get("initiator_role") == "buyer" else deal.get("initiator_id")
        if q.from_user.id != seller_id:
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
            except Exception:
                seller_name = MSG_THE_SELLER
            await q.answer(f"⚠️ This is the SELLER's action. Wait for {seller_name} to confirm fiat received.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await db.update_deal_status(deal_id, "fiat_received")
        
        # Send notification to logs group
        try:
            seller_chat = await context.bot.get_chat(seller_id)
            seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
            
            await send_log_notification(
                context,
                "💵 <b>FIAT RECEIVED BY SELLER</b>\n\n"
                f"Deal ID: #{deal_id}\n"
                f"Seller: {seller_name}\n"
                f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}\n"
                f"Payment Method: {deal.get('payment_method', 'N/A')}\n"
                "Status: Awaiting both parties to mark complete"
            )
        except Exception as e:
            logger.error(f"Failed to send fiat received log: {e}")
        
        # Now show completion buttons for BOTH parties
        await q.edit_message_text(
            "✅ **Seller confirmed fiat received!**\n\n"
            "📌 Admin will release USDT soon.\n"
            "Both parties click below when satisfied:",
            parse_mode="Markdown"
        )
        
        # Send completion buttons
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text="Buyer, mark completion:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Mark Completed", callback_data=f"complete:{deal_id}:buyer")
            ]])
        )
        
        await context.bot.send_message(
            chat_id=deal["group_chat_id"],
            text="Seller, mark completion:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Mark Completed", callback_data=f"complete:{deal_id}:seller")
            ]])
        )

    elif data.startswith("complete:"):
        _, deal_id_str, who = data.split(":")
        deal_id = int(deal_id_str)
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        # Determine who is buyer and seller
        buyer_id = deal["initiator_id"] if deal.get("initiator_role") == "buyer" else deal.get("target_id")
        seller_id = deal["target_id"] if deal.get("initiator_role") == "buyer" else deal.get("initiator_id")

        # Verify caller
        if who == "buyer":
            if q.from_user.id != buyer_id:
                try:
                    buyer_chat = await context.bot.get_chat(buyer_id)
                    buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else buyer_chat.full_name
                except Exception:
                    buyer_name = MSG_THE_BUYER
                await q.answer(f"⚠️ This is the BUYER's button. Wait for {buyer_name} to complete.", show_alert=True)
                return
            # ✅ Acknowledge callback query
            await q.answer()
            # Mark buyer as completed (use initiator or target field based on role)
            if deal.get("initiator_role") == "buyer":
                await db.update_deal(deal_id, completed_initiator=1)
            else:
                await db.update_deal(deal_id, completed_target=1)
        else:  # seller
            if q.from_user.id != seller_id:
                try:
                    seller_chat = await context.bot.get_chat(seller_id)
                    seller_name = f"@{seller_chat.username}" if seller_chat.username else seller_chat.full_name
                except Exception:
                    seller_name = MSG_THE_SELLER
                await q.answer(f"⚠️ This is the SELLER's button. Wait for {seller_name} to complete.", show_alert=True)
                return
            # ✅ Acknowledge callback query
            await q.answer()
            # Mark seller as completed
            if deal.get("initiator_role") == "seller":
                await db.update_deal(deal_id, completed_initiator=1)
            else:
                await db.update_deal(deal_id, completed_target=1)
        
        await q.edit_message_text(f"✅ {who.capitalize()} marked completed!")
        
        # Check if both completed
        deal = await db.get_deal(deal_id)
        if deal.get("completed_initiator") and deal.get("completed_target"):
            # Both completed! Close deal and kick users
            await db.update_deal_status(deal_id, "closed")
            
            # Get user names for notification
            try:
                initiator_chat = await context.bot.get_chat(deal["initiator_id"])
                target_chat = await context.bot.get_chat(deal["target_id"])
                initiator_name = f"@{initiator_chat.username}" if initiator_chat.username else (initiator_chat.full_name or f"User {deal['initiator_id']}")
                target_name = f"@{target_chat.username}" if target_chat.username else (target_chat.full_name or f"User {deal['target_id']}")
            except Exception:
                initiator_name = f"User {deal['initiator_id']}"
                target_name = f"User {deal['target_id']}"
            
            # Send completion message to deal room
            await context.bot.send_message(
                chat_id=deal["group_chat_id"],
                text=(
                    f"🎉 **Deal #{deal_id} Completed!**\n\n"
                    "Both parties confirmed completion.\n"
                    "Thank you for using our service!\n\n"
                    "━━━━━━━━━━━━━━━━━\n"
                    f"{BOT_SIGNATURE}"
                ),
                parse_mode="Markdown"
            )
            
            # Send "Deal Completed" message to MAIN GROUP
            if MAIN_GROUP_ID:
                try:
                    await context.bot.send_message(
                        chat_id=MAIN_GROUP_ID,
                        text=f"✅ Deal #{deal_id} Completed!\n\n👤 {initiator_name}\n👤 {target_name}\n\n🎉 Transaction successful!"
                    )
                except Exception as e:
                    logger.exception("Failed to send deal completed message to main group: %s", e)
            
            # Send comprehensive receipt to logs group
            try:
                await send_log_notification(
                    context,
                    "🎉 <b>DEAL COMPLETED</b>\n\n"
                    f"Deal ID: #{deal_id}\n"
                    f"Initiator: {initiator_name}\n"
                    f"Counterparty: {target_name}\n"
                    f"Amount: {deal.get('amount')} {deal.get('currency', 'USDT')}\n"
                    f"Payment Method: {deal.get('payment_method', 'N/A')}\n"
                    f"Network: {deal.get('network', 'N/A')}\n"
                    f"INR Rate: ₹{deal.get('inr_rate', 'N/A')}/USDT\n"
                    "Status: ✅ COMPLETED\n\n"
                    "Both parties confirmed completion."
                )
            except Exception as e:
                logger.error(f"Failed to send completion log: {e}")
            
            # Ask users to leave manually (regular groups can't kick)
            if deal.get("group_chat_id"):
                try:
                    await context.bot.send_message(
                        chat_id=deal["group_chat_id"],
                        text="✅ Deal completed! Please leave the room manually. Thank you!"
                    )
                except Exception:
                    pass
                
                await db.release_group(deal["group_chat_id"])

    elif data.startswith("release:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id not in ADMIN_IDS:
            await q.answer("⚠️ This is an ADMIN action. Only admins can release payment.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        await db.update_deal_status(deal_id, "paid")
        
        # ask buyer to send fiat
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ I've Sent Fiat", callback_data=f"fiat_sent:{deal_id}")]])
        await q.edit_message_text(f"Deal {deal_id} — Payment verified by admin.\nBuyer, send fiat to seller and click below when done.", reply_markup=keyboard)

    elif data.startswith("fiat_sent:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id != deal["initiator_id"]:
            try:
                buyer_chat = await context.bot.get_chat(deal["initiator_id"])
                buyer_name = f"@{buyer_chat.username}" if buyer_chat.username else buyer_chat.full_name
            except Exception:
                buyer_name = MSG_THE_BUYER
            await q.answer(f"⚠️ This is the BUYER's action. Wait for {buyer_name} to send fiat.", show_alert=True)
            return
        
        # ✅ Acknowledge callback query
        await q.answer()
        
        await db.update_deal_status(deal_id, "fiat_sent")
        
        # ask seller to confirm fiat received
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Fiat Received", callback_data=f"fiat_received:{deal_id}")]])
        await q.edit_message_text(f"Deal {deal_id} — Buyer marked fiat as sent.\nSeller, click below when you receive fiat.", reply_markup=keyboard)

    elif data.startswith("fiat_received:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id != deal["target_id"]:
            await q.answer("Only the seller can confirm fiat received.", show_alert=True)
            return

        # ✅ Acknowledge callback query
        await q.answer()

        await db.update_deal_status(deal_id, "fiat_received")
        
        # notify admin to release USDT
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Release USDT", callback_data=f"release:{deal_id}")]])
        await q.edit_message_text(f"Deal {deal_id} — Seller confirmed fiat received.\nAdmin, click below to release USDT.", reply_markup=keyboard)

    elif data.startswith("release:"):
        deal_id = int(data.split(":", 1)[1])
        deal = await db.get_deal(deal_id)
        if not deal:
            await q.edit_message_text(MSG_DEAL_NOT_FOUND)
            return

        if q.from_user.id not in ADMIN_IDS:
            await q.answer("Only admin can release.", show_alert=True)
            return

        # ✅ Acknowledge callback query
        await q.answer()

        await db.update_deal_status(deal_id, "released")
        await db.update_deal_status(deal_id, "closed")
        
        await q.edit_message_text(f"Deal {deal_id} — USDT released by admin.\nDeal complete! 🎉")
        
        # release group
        if deal["group_chat_id"]:
            await db.release_group(deal["group_chat_id"])
            # optionally kick members or leave a closing message
            try:
                await context.bot.send_message(chat_id=deal["group_chat_id"], text="Deal completed. This room is now free for the next deal.")
            except Exception as e:
                logger.exception("Failed to send closing message: %s", e)


# Old submit_tx command - replaced by interactive flow in tx_conversation.py
# Keeping for reference
# async def submit_tx_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """
#     /submit_tx <deal_id> <tx_hash> <amount> <network>
#     Seller submits payment proof
#     """
#     ...


async def deal_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /deal_status <deal_id> or /my_deals
    """
    msg = update.message
    if context.args:
        deal_id = int(context.args[0])
        deal = await db.get_deal(deal_id)
        if not deal:
            await msg.reply_text(MSG_DEAL_NOT_FOUND)
            return
        await msg.reply_text(str(deal))
        return

    # list my deals
    deals = await db.list_deals_for_user(msg.from_user.id)
    if not deals:
        await msg.reply_text("You have no deals.")
        return
    lines = [f"ID {d['id']} — {d['status']} — with {d['target_id'] if d['initiator_id']==msg.from_user.id else d['initiator_id']}" for d in deals]
    await msg.reply_text("\n".join(lines))


async def admin_list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list groups in pool."""
    msg = update.message
    if msg.from_user.id not in ADMIN_IDS:
        await msg.reply_text("You are not an admin.")
        return

    # list groups from DB
    async with db.aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = db.aiosqlite.Row
        cur = await conn.execute("SELECT * FROM groups")
        rows = await cur.fetchall()
        groups = [dict(r) for r in rows]

    if not groups:
        await msg.reply_text("No groups in pool.")
        return

    lines = [f"Chat ID: {g['chat_id']} — {g['name']} — {'Occupied' if g['is_occupied'] else 'Free'} — Deal: {g['current_deal_id']}" for g in groups]
    await msg.reply_text("\n".join(lines))


async def admin_release_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to manually release a group."""
    msg = update.message
    if msg.from_user.id not in ADMIN_IDS:
        await msg.reply_text("You are not an admin.")
        return

    if not context.args:
        await msg.reply_text("Usage: /release_group <chat_id>")
        return

    chat_id = int(context.args[0])
    await db.release_group(chat_id)
    await msg.reply_text(f"Group {chat_id} released.")


async def admin_reset_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to reset all groups to free (useful for testing/recovery)."""
    msg = update.message
    if msg.from_user.id not in ADMIN_IDS:
        await msg.reply_text("You are not an admin.")
        return

    # reset all groups
    async with db.aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("UPDATE groups SET is_occupied = 0, current_deal_id = NULL")
        await conn.commit()
    
    await msg.reply_text("✅ All groups have been reset to FREE status.")


async def initialize_db_and_groups() -> None:
    """Initialize database and group pool."""
    await db.init_db()
    
    # add groups from env to pool
    for gid in GROUP_CHAT_IDS:
        await db.add_group_to_pool(gid, f"Deal room {gid}")
    
    logger.info(f"Loaded {len(GROUP_CHAT_IDS)} groups into pool")


async def setup_bot_commands(app) -> None:
    """Set up bot command menu (shows when user types /)."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("deal", "Create a new deal"),
        BotCommand("deal_status", "Check deal status"),
        BotCommand("cancel", "Cancel current operation"),
    ]
    
    # Admin-only commands
    admin_commands = commands + [
        BotCommand("list_groups", "List all group pools (Admin)"),
        BotCommand("release_group", "Free a stuck group (Admin)"),
        BotCommand("reset_groups", "Reset all groups (Admin)"),
    ]
    
    # Set commands for regular users
    await app.bot.set_my_commands(commands)
    
    # Set commands for admins
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(admin_id)
            )
        except Exception as e:
            logger.warning(f"Could not set admin commands for {admin_id}: {e}")


def main() -> None:
    """
    Main entry point for the Telegram bot.
    
    Bot Developer: @killerbesto
    Copyright (c) 2025
    """
    if not BOT_TOKEN:
        print("Please set BOT_TOKEN in environment (.env) and restart.")
        return
    
    # Print copyright notice
    print("=" * 50)
    print("  Telegram P2P Deal Bot")
    print("  Developer: @killerbesto")
    print("  Copyright (c) 2025 - All Rights Reserved")
    print("=" * 50)

    # initialize DB and load groups (single asyncio.run call)
    asyncio.run(initialize_db_and_groups())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Import conversation handlers
    # Import the deal command handler directly
    from .deal_conversation import deal_start
    
    # No longer using tx_conversation - now using button-based TX submission
    # from .tx_conversation import get_tx_conversation_handler
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("deal", deal_start))  # Simple command handler, not conversation
    # app.add_handler(get_tx_conversation_handler())  # REMOVED: Now using button-based flow
    app.add_handler(CommandHandler("deal_status", deal_status))
    app.add_handler(CommandHandler("list_groups", admin_list_groups))
    app.add_handler(CommandHandler("release_group", admin_release_group_cmd))
    app.add_handler(CommandHandler("reset_groups", admin_reset_all_groups))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(ChatJoinRequestHandler(handle_chat_join_request))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))  # Handle text input in groups

    # Set up bot command menu
    async def post_init(application):
        await setup_bot_commands(application)
    
    app.post_init = post_init

    logger.info("Bot started successfully - Developer: @killerbesto")
    app.run_polling()


if __name__ == "__main__":
    main()
