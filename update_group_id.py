#!/usr/bin/env python3
"""Update old group ID to new supergroup ID in database"""
import sqlite3

DB_PATH = "bot.db"
OLD_ID = -5004801923
NEW_ID = -1003453691011

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Update groups table
cursor.execute("UPDATE groups SET chat_id = ? WHERE chat_id = ?", (NEW_ID, OLD_ID))
print(f"✅ Updated groups table: {cursor.rowcount} rows")

# Update deals table
cursor.execute("UPDATE deals SET group_chat_id = ? WHERE group_chat_id = ?", (NEW_ID, OLD_ID))
print(f"✅ Updated deals table: {cursor.rowcount} rows")

conn.commit()
conn.close()

print(f"\n🎉 Successfully updated group ID from {OLD_ID} to {NEW_ID}")
print("Restart the bot now!")
