import sqlite3
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print("Tables:", [row[0] for row in cursor.fetchall()])
cursor.execute('PRAGMA table_info(group_pool)')
print("\ngroup_pool columns:", [row[1] for row in cursor.fetchall()])
conn.close()
