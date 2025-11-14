"""Interactive deal creation conversation handler."""
from __future__ import annotations

import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
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
ROLE, CURRENCY, AMOUNT, INR_RATE, PAYMENT_METHOD, COUNTERPARTY, CONFIRM = range(7)


async def deal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the deal creation flow - assign room and send invite link."""
    from . import bot, db
    
    msg = update.message
    initiator_id = msg.from_user.id
    
    # Check if user tagged someone in the message
    counterparty_id = None
    counterparty_username = None
    counterparty_name = None
    
    if msg.reply_to_message:
        # User replied to someone's message
        counterparty_id = msg.reply_to_message.from_user.id
        counterparty_username = msg.reply_to_message.from_user.username
        counterparty_name = f"@{msg.reply_to_message.from_user.username}" if msg.reply_to_message.from_user.username else msg.reply_to_message.from_user.full_name
    elif msg.entities:
        # Check for text mentions in /deal command
        for entity in msg.entities:
            if entity.type == MessageEntity.TEXT_MENTION:
                # User mentioned someone without username
                counterparty_id = entity.user.id
                counterparty_name = f"@{entity.user.username}" if entity.user.username else entity.user.full_name
                counterparty_username = None
                break
            elif entity.type == MessageEntity.MENTION:
                # User mentioned @username - need to extract from text
                username = msg.text[entity.offset:entity.offset + entity.length]
                counterparty_username = username
                # Try to resolve user ID
                try:
                    user_chat = await context.bot.get_chat(username)
                    counterparty_id = user_chat.id
                    counterparty_name = f"@{user_chat.username}" if user_chat.username else user_chat.full_name
                except:
                    pass
                break
    
    # Check if counterparty was mentioned
    if not counterparty_id:
        await msg.reply_text(
            "❌ Please tag your counterparty when creating a deal.\n\n"
            "Usage: `/deal @username` or reply to their message with `/deal`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Get free group
    free_group = await db.get_free_group()
    if not free_group:
        await msg.reply_text(
            "❌ No deal rooms available right now.\n"
            "Admin can check status with /list_groups"
        )
        return ConversationHandler.END
    
    group_chat_id = free_group["chat_id"]
    
    # Create invite link (no expiration, unlimited uses)
    try:
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=group_chat_id,
            name=f"Deal {initiator_id}-{counterparty_id}",
            # No member_limit or creates_join_request for maximum compatibility
        )
        invite_link = invite_link_obj.invite_link
    except Exception as e:
        logger.exception("Failed to create invite link: %s", e)
        await msg.reply_text("❌ Failed to create invite link. Contact admin.")
        return ConversationHandler.END
    
    # Create deal in pending state (will be confirmed when both join)
    deal_id = await db.create_deal(
        initiator_id=initiator_id,
        target_id=counterparty_id,
        initiator_role="pending",  # Will be selected in group
        amount="pending",  # Will be filled in group
        currency="pending",
        inr_rate=None,
        payment_method="pending",
        group_chat_id=group_chat_id,
        usdt_address=bot.USDT_ADDRESS,
        invite_link=invite_link,
    )
    
    # Format counterparty display name
    # Format initiator display name (prioritize username)
    initiator_display = f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.full_name
    
    # Format counterparty display name (prioritize username)
    counterparty_display = counterparty_name or counterparty_username or f"User {counterparty_id}"
    
    # ONLY send invite link to the main group (where /deal was typed)
    # NO DM sending - removed as per requirement
    
    reply_text = (
        f"✅ Deal #{deal_id} Created!\n\n"
        f"👤 Initiator: {initiator_display}\n"
        f"👤 Counterparty: {counterparty_display}\n\n"
        f"🔗 Private Deal Room:\n{invite_link}\n\n"
        f"⚠️ Click the link to join. Only authorized participants can join."
    )
    
    await msg.reply_text(reply_text)  # Removed parse_mode="Markdown"
    
    # Send notification to logs group
    await bot.send_log_notification(
        context,
        f"📝 <b>NEW DEAL CREATED</b>\n\n"
        f"Deal ID: #{deal_id}\n"
        f"Initiator: {initiator_display}\n"
        f"Counterparty: {counterparty_display}\n"
        f"Status: Pending (waiting to join room)\n\n"
        f"🔗 <a href='{invite_link}'>Deal Room</a>"
    )
    
    return ConversationHandler.END


async def role_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Deal creation cancelled.")
        return ConversationHandler.END
    
    role = query.data.split(":")[1]
    context.user_data["role"] = role
    
    # Ask for currency type
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Crypto (USDT)", callback_data="currency:crypto")],
        [InlineKeyboardButton("💰 INR", callback_data="currency:inr")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])
    
    role_emoji = "🛒" if role == "buyer" else "💰"
    await query.edit_message_text(
        f"{role_emoji} You're the {role.upper()}.\n\n"
        f"What currency are you dealing in?",
        reply_markup=keyboard
    )
    return CURRENCY


async def currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Deal creation cancelled.")
        return ConversationHandler.END
    
    currency = query.data.split(":")[1]
    context.user_data["currency"] = currency
    
    currency_symbol = "USDT" if currency == "crypto" else "INR"
    await query.edit_message_text(
        f"✅ Currency: {currency_symbol}\n\n"
        f"Now, enter the amount (just the number, e.g., 1000 or 50000):"
    )
    return AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input."""
    # Check if message is from the deal initiator
    if update.message.from_user.id != context.user_data.get("initiator_id"):
        # Ignore messages from other users
        return AMOUNT
    
    amount_text = update.message.text.strip()
    currency = context.user_data.get("currency", "crypto")
    currency_symbol = "USDT" if currency == "crypto" else "INR"
    
    # Store amount with currency
    context.user_data["amount"] = f"{amount_text} {currency_symbol}"
    
    # Get payment methods from environment
    from . import bot
    payment_methods = bot.PAYMENT_METHODS
    
    # Create keyboard with payment methods (2 per row)
    keyboard_buttons = []
    for i in range(0, len(payment_methods), 2):
        row = [InlineKeyboardButton(payment_methods[i], callback_data=f"payment:{payment_methods[i]}")]
        if i + 1 < len(payment_methods):
            row.append(InlineKeyboardButton(payment_methods[i + 1], callback_data=f"payment:{payment_methods[i + 1]}"))
        keyboard_buttons.append(row)
    
    keyboard_buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    amount = context.user_data["amount"]
    currency = context.user_data.get("currency", "Crypto")
    
    # If currency is INR, ask for INR rate
    if currency == "INR":
        await update.message.reply_text(
            f"✅ Amount: {amount} INR\n\n"
            f"Now, enter the INR to USDT rate (e.g., 90.5):"
        )
        return INR_RATE
    
    # For Crypto, go straight to payment method
    # Get payment methods from environment
    from . import bot
    payment_methods = bot.PAYMENT_METHODS
    
    # Create keyboard with payment methods (2 per row)
    keyboard_buttons = []
    for i in range(0, len(payment_methods), 2):
        row = [InlineKeyboardButton(payment_methods[i], callback_data=f"payment:{payment_methods[i]}")]
        if i + 1 < len(payment_methods):
            row.append(InlineKeyboardButton(payment_methods[i + 1], callback_data=f"payment:{payment_methods[i + 1]}"))
        keyboard_buttons.append(row)
    
    keyboard_buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await update.message.reply_text(
        f"✅ Amount: {amount}\n\n"
        f"Select payment method:",
        reply_markup=keyboard
    )
    return PAYMENT_METHOD


async def inr_rate_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle INR rate input."""
    rate_text = update.message.text.strip()
    
    # Validate numeric
    try:
        rate = float(rate_text.replace(',', ''))
        if rate <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid rate (e.g., 90.5):"
        )
        return INR_RATE
    
    context.user_data["inr_rate"] = rate_text
    
    # Get payment methods from environment
    from . import bot
    payment_methods = bot.PAYMENT_METHODS
    
    # Create keyboard with payment methods (2 per row)
    keyboard_buttons = []
    for i in range(0, len(payment_methods), 2):
        row = [InlineKeyboardButton(payment_methods[i], callback_data=f"payment:{payment_methods[i]}")]
        if i + 1 < len(payment_methods):
            row.append(InlineKeyboardButton(payment_methods[i + 1], callback_data=f"payment:{payment_methods[i + 1]}"))
        keyboard_buttons.append(row)
    
    keyboard_buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    await update.message.reply_text(
        f"✅ INR Rate: {rate_text}\n\n"
        f"Select payment method:",
        reply_markup=keyboard
    )
    return PAYMENT_METHOD


async def payment_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment method selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Deal creation cancelled.")
        return ConversationHandler.END
    
    payment_method = query.data.split(":")[1]
    context.user_data["payment_method"] = payment_method
    
    # Check if counterparty was already provided
    if "counterparty_username" in context.user_data:
        # Skip to confirmation
        return await show_confirmation(update, context)
    
    await query.edit_message_text(
        f"✅ Payment method: {payment_method}\n\n"
        f"Now, enter the counterparty username (with or without @):"
    )
    return COUNTERPARTY


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show confirmation screen with deal summary."""
    role = context.user_data["role"]
    currency = context.user_data.get("currency", "Crypto")
    amount = context.user_data["amount"]
    inr_rate = context.user_data.get("inr_rate")
    payment_method = context.user_data["payment_method"]
    counterparty = context.user_data.get("counterparty_username", "Unknown")
    
    counterparty_role = "Seller" if role == "buyer" else "Buyer"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Create Deal", callback_data="confirm:yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm:no")],
    ])
    
    summary = (
        f"📋 **Deal Summary**\n\n"
        f"Your role: {role.upper()}\n"
        f"Currency: {currency}\n"
        f"Amount: {amount}\n"
    )
    
    if inr_rate:
        summary += f"INR Rate: {inr_rate}\n"
    
    summary += (
        f"Payment method: {payment_method}\n"
        f"{counterparty_role}: {counterparty}\n\n"
        f"Confirm to create the deal?"
    )
    
    # Check if this is from callback query or message
    if update.callback_query:
        await update.callback_query.edit_message_text(summary, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(summary, reply_markup=keyboard, parse_mode="Markdown")
    
    return CONFIRM


async def counterparty_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle counterparty username input."""
    # Check if message is from the deal initiator
    if update.message.from_user.id != context.user_data.get("initiator_id"):
        # Ignore messages from other users
        return COUNTERPARTY
    
    username = update.message.text.strip()
    
    # Auto-add @ if missing and not numeric
    if not username.startswith("@") and not username.isdigit():
        username = f"@{username}"
    
    context.user_data["counterparty_username"] = username
    
    # Show confirmation
    return await show_confirmation(update, context)


async def deal_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle deal confirmation and create the deal."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm:no":
        await query.edit_message_text("❌ Deal creation cancelled.")
        return ConversationHandler.END
    
    # Import bot functions
    from . import bot, db
    
    role = context.user_data["role"]
    currency = context.user_data.get("currency", "Crypto")
    amount = context.user_data["amount"]
    inr_rate = context.user_data.get("inr_rate")
    payment_method = context.user_data["payment_method"]
    counterparty = context.user_data.get("counterparty_username", context.user_data.get("counterparty"))
    
    # Resolve counterparty
    try:
        # If we already have counterparty_id, use it
        if "counterparty_id" in context.user_data:
            target_id = context.user_data["counterparty_id"]
        else:
            # Otherwise resolve from username
            target_chat = await context.bot.get_chat(counterparty)
            target_id = target_chat.id
    except Exception as e:
        logger.exception("Failed to resolve counterparty: %s", e)
        await query.edit_message_text(
            f"❌ Couldn't find user '{counterparty}'.\n\n"
            f"Make sure they have a public @username or have started the bot."
        )
        return ConversationHandler.END
    
    initiator_id = query.from_user.id
    
    # Get free group
    free_group = await db.get_free_group()
    if not free_group:
        await query.edit_message_text(
            f"❌ No deal rooms available right now.\n"
            f"Admin can check status with /list_groups"
        )
        return ConversationHandler.END
    
    group_chat_id = free_group["chat_id"]
    
    # Create invite link (no expiration, unlimited uses)
    try:
        invite_link_obj = await context.bot.create_chat_invite_link(
            chat_id=group_chat_id,
            name=f"Deal {initiator_id}-{target_id}",
            # No member_limit or creates_join_request for maximum compatibility
        )
        invite_link = invite_link_obj.invite_link
    except Exception as e:
        logger.exception("Failed to create invite link: %s", e)
        await query.edit_message_text("❌ Failed to create invite link. Contact admin.")
        return ConversationHandler.END
    
    # Create deal
    deal_id = await db.create_deal(
        initiator_id=initiator_id,
        target_id=target_id,
        initiator_role=role,
        amount=amount,
        currency=currency,
        inr_rate=inr_rate,
        payment_method=payment_method,
        group_chat_id=group_chat_id,
        usdt_address=bot.USDT_ADDRESS,
        invite_link=invite_link,
    )
    
    # Send invite links
    counterparty_role = "seller" if role == "buyer" else "buyer"
    
    instructions_initiator = (
        f"✅ Deal #{deal_id} created!\n\n"
        f"Your role: {role.upper()}\n"
        f"Amount: {amount}\n"
        f"Payment: {payment_method}\n"
        f"Counterparty: {counterparty}\n\n"
        f"Click the link to join the deal room:\n{invite_link}"
    )
    
    # Format initiator name with @ priority
    initiator_display = f"@{query.from_user.username}" if query.from_user.username else query.from_user.full_name
    
    instructions_target = (
        f"📢 New deal request from {initiator_display}!\n\n"
        f"Deal #{deal_id}\n"
        f"Your role: {counterparty_role.upper()}\n"
        f"Amount: {amount}\n"
        f"Payment: {payment_method}\n\n"
        f"Click the link to join the deal room:\n{invite_link}"
    )
    
    initiator_sent = False
    target_sent = False
    
    try:
        await context.bot.send_message(chat_id=initiator_id, text=instructions_initiator)
        initiator_sent = True
    except Exception as e:
        logger.exception("Failed to send to initiator: %s", e)
    
    try:
        await context.bot.send_message(chat_id=target_id, text=instructions_target)
        target_sent = True
    except Exception as e:
        logger.exception("Failed to send to target: %s", e)
    
    # If command was started in a group, send invite link there too
    main_group_id = context.user_data.get("main_group_id")
    if main_group_id:
        # Format initiator name with @ priority
        initiator_display_group = f"@{query.from_user.username}" if query.from_user.username else query.from_user.full_name
        
        try:
            await context.bot.send_message(
                chat_id=main_group_id,
                text=(
                    f"🎯 Deal #{deal_id} Created!\n\n"
                    f"👤 Initiator: {initiator_display_group}\n"
                    f"👤 Counterparty: {counterparty}\n"
                    f"💰 Amount: {amount}\n"
                    f"💳 Payment: {payment_method}\n\n"
                    f"🔗 Private Deal Room:\n{invite_link}\n\n"
                    f"⚠️ Only authorized participants can join."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception("Failed to send to main group: %s", e)
    
    # Feedback
    if initiator_sent and target_sent:
        await query.edit_message_text(f"✅ Deal #{deal_id} created! Invite links sent to both users.")
    elif initiator_sent and not target_sent:
        await query.edit_message_text(
            f"✅ Deal #{deal_id} created!\n"
            f"❌ Could not send to {counterparty}. They must /start the bot first.\n\n"
            f"Share this link manually:\n{invite_link}"
        )
    else:
        await query.edit_message_text(
            f"✅ Deal #{deal_id} created!\n"
            f"Here's the invite link:\n{invite_link}"
        )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("❌ Deal creation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


# Build the conversation handler
def get_deal_conversation_handler():
    """Returns the ConversationHandler for deal creation."""
    return ConversationHandler(
        entry_points=[CommandHandler("deal", deal_start)],
        states={
            ROLE: [CallbackQueryHandler(role_selected)],
            CURRENCY: [CallbackQueryHandler(currency_selected)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)],
            INR_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, inr_rate_entered)],
            PAYMENT_METHOD: [CallbackQueryHandler(payment_method_selected)],
            COUNTERPARTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, counterparty_entered)],
            CONFIRM: [CallbackQueryHandler(deal_confirmed)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )
