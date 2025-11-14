"""
Transaction submission conversation handler.

Copyright (c) 2025 @killerbesto
All Rights Reserved.
"""
from __future__ import annotations

import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)

# Conversation states
TX_HASH, TX_LINK, TX_AMOUNT, TX_CURRENCY = range(4)


async def submit_tx_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the transaction submission flow."""
    msg = update.message
    args = context.args
    
    if not args:
        await msg.reply_text(
            "❌ Please provide deal ID.\n\n"
            "Usage: /submit_tx <deal_id>"
        )
        return ConversationHandler.END
    
    try:
        deal_id = int(args[0])
    except ValueError:
        await msg.reply_text("❌ Invalid deal ID. Must be a number.")
        return ConversationHandler.END
    
    # Import db here to avoid circular imports
    from . import db
    
    # Verify deal exists
    deal = await db.get_deal(deal_id)
    if not deal:
        await msg.reply_text(f"❌ Deal #{deal_id} not found.")
        return ConversationHandler.END
    
    # Determine who is the seller based on role
    initiator_role = deal.get("initiator_role", "")
    if initiator_role == "seller":
        seller_id = deal["initiator_id"]
    elif initiator_role == "buyer":
        seller_id = deal.get("target_id")
    else:
        await msg.reply_text("❌ Deal roles not properly set.")
        return ConversationHandler.END
    
    # Verify caller is the seller
    if msg.from_user.id != seller_id:
        await msg.reply_text("❌ Only the crypto SELLER can submit transaction details.")
        return ConversationHandler.END
    
    # Verify deal is in correct state (must be confirmed)
    if deal.get("status") != "confirmed":
        await msg.reply_text(f"❌ Deal must be confirmed first. Current status: {deal.get('status', 'unknown')}")
        return ConversationHandler.END
    
    # Store deal_id in context
    context.user_data["tx_deal_id"] = deal_id
    context.user_data["tx_deal"] = deal
    
    await msg.reply_text(
        f"💳 **Transaction Submission - Deal #{deal_id}**\n\n"
        "Step 1/4: Enter the transaction hash (TX Hash):",
        parse_mode="Markdown"
    )
    return TX_HASH


async def tx_hash_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction hash input."""
    tx_hash = update.message.text.strip()
    context.user_data["tx_hash"] = tx_hash
    
    await update.message.reply_text(
        f"✅ TX Hash: `{tx_hash}`\n\n"
        "Step 2/4: Enter the blockchain explorer link (optional - send 'skip' to skip):",
        parse_mode="Markdown"
    )
    return TX_LINK


async def tx_link_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle transaction link input."""
    tx_link = update.message.text.strip()
    
    if tx_link.lower() == 'skip':
        context.user_data["tx_link"] = None
    else:
        context.user_data["tx_link"] = tx_link
    
    link_display = "Skipped" if tx_link.lower() == 'skip' else tx_link
    
    await update.message.reply_text(
        f"✅ Explorer Link: {link_display}\n\n"
        "Step 3/4: Enter the amount sent (numbers only):",
        parse_mode="Markdown"
    )
    return TX_AMOUNT


async def tx_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input."""
    amount_text = update.message.text.strip()
    
    # Validate numeric
    try:
        float(amount_text.replace(',', ''))
    except ValueError:
        await update.message.reply_text(
            "❌ Amount must be a number. Please try again:"
        )
        return TX_AMOUNT
    
    context.user_data["tx_amount"] = amount_text
    
    # Create currency selection buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("USDT", callback_data="tx_currency:USDT"),
            InlineKeyboardButton("ETH", callback_data="tx_currency:ETH"),
        ],
        [
            InlineKeyboardButton("BTC", callback_data="tx_currency:BTC"),
            InlineKeyboardButton("TRC20", callback_data="tx_currency:TRC20"),
        ],
        [
            InlineKeyboardButton("ERC20", callback_data="tx_currency:ERC20"),
            InlineKeyboardButton("BEP20", callback_data="tx_currency:BEP20"),
        ],
        [InlineKeyboardButton("Other", callback_data="tx_currency:Other")],
    ])
    
    await update.message.reply_text(
        f"✅ Amount: {amount_text}\n\n"
        "Step 4/4: Select the currency/network:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return TX_CURRENCY


async def tx_currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection and submit transaction."""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.split(":")[1]
    context.user_data["tx_currency"] = currency
    
    # Get all collected data
    deal_id = context.user_data["tx_deal_id"]
    deal = context.user_data["tx_deal"]
    tx_hash = context.user_data["tx_hash"]
    tx_link = context.user_data.get("tx_link")
    tx_amount = context.user_data["tx_amount"]
    
    # Import db and bot
    from . import db, bot
    
    # Save to database (including tx_link)
    await db.update_deal(
        deal_id=deal_id,
        tx_hash=tx_hash,
        tx_link=tx_link,
        deposit_amount=tx_amount,
        deposit_network=currency
    )
    
    # Update status to paid (pending verification)
    await db.update_deal_status(deal_id, "paid")
    
    # Format confirmation message
    confirmation = (
        "✅ **Transaction Submitted!**\n"
        f"{'='*35}\n\n"
        f"📋 **Deal ID:** #{deal_id}\n"
        f"🔑 **TX Hash:** `{tx_hash}`\n"
    )
    
    if tx_link:
        confirmation += f"🔗 **Explorer:** {tx_link}\n"
    
    confirmation += (
        f"💰 **Amount:** {tx_amount}\n"
        f"💱 **Currency:** {currency}\n\n"
        f"{'='*35}\n"
        "⏳ Waiting for admin verification..."
    )
    
    await query.edit_message_text(confirmation, parse_mode="Markdown")
    
    # Notify in group with verification button
    if deal.get("group_chat_id"):
        group_msg = (
            f"💳 **Payment Submitted - Deal #{deal_id}**\n"
            f"{'='*35}\n\n"
            f"🔑 TX Hash: `{tx_hash}`\n"
        )
        
        if tx_link:
            group_msg += f"🔗 Explorer: {tx_link}\n"
        
        group_msg += (
            f"💰 Amount: {tx_amount} {currency}\n\n"
            f"{'='*35}\n"
            "⚠️ **Admin: Please verify this transaction**"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verified", callback_data=f"verified:{deal_id}")],
            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment:{deal_id}")],
        ])
        
        try:
            await context.bot.send_message(
                chat_id=deal["group_chat_id"],
                text=group_msg,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception("Failed to send to group: %s", e)
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_tx_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the transaction submission."""
    await update.message.reply_text("❌ Transaction submission cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


# Build the conversation handler
def get_tx_conversation_handler():
    """Returns the ConversationHandler for transaction submission."""
    return ConversationHandler(
        entry_points=[CommandHandler("submit_tx", submit_tx_start)],
        states={
            TX_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, tx_hash_entered)],
            TX_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, tx_link_entered)],
            TX_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tx_amount_entered)],
            TX_CURRENCY: [CallbackQueryHandler(tx_currency_selected, pattern="^tx_currency:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_tx_conversation)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )
