"""
Test script to verify LOGS_GROUP_ID is configured correctly.
Run this to test if your bot can send messages to the logs channel/group.
"""
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
LOGS_GROUP_ID = int(os.environ.get("LOGS_GROUP_ID", "0")) if os.environ.get("LOGS_GROUP_ID") else None

async def test_logs_channel():
    """Test if bot can send to logs channel."""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file")
        return
    
    if not LOGS_GROUP_ID:
        print("❌ LOGS_GROUP_ID not configured in .env file")
        print("📖 See LOGS_SETUP.md for setup instructions")
        return
    
    print(f"🔍 Testing connection to logs group: {LOGS_GROUP_ID}")
    
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Try to send a test message
        message = await bot.send_message(
            chat_id=LOGS_GROUP_ID,
            text=(
                "🧪 <b>TEST MESSAGE</b>\n\n"
                "This is a test notification to verify the logs channel is working correctly.\n\n"
                "If you see this message, your LOGS_GROUP_ID is configured properly! ✅"
            ),
            parse_mode="HTML"
        )
        
        print("✅ Success! Test message sent to logs channel.")
        print(f"📨 Message ID: {message.message_id}")
        print(f"📍 Chat ID: {message.chat.id}")
        print(f"📝 Chat Title: {message.chat.title or 'Private Channel'}")
        print("\n✅ Your logs channel is working correctly!")
        
    except Exception as e:
        print(f"❌ Error sending message to logs channel:")
        print(f"   {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the bot is added to the channel/group")
        print("   2. Verify the bot is an administrator")
        print("   3. Check that LOGS_GROUP_ID is correct (includes negative sign)")
        print("   4. See LOGS_SETUP.md for detailed setup instructions")

if __name__ == "__main__":
    print("🚀 Testing Logs Channel Configuration...\n")
    asyncio.run(test_logs_channel())
