import sqlite3

db_path = "stories.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(user)")
existing_cols = [row[1] for row in cur.fetchall()]

new_cols = {
    "last_visited_bots": "DATETIME",
    "last_visited_comments": "DATETIME",
    "last_visited_activity": "DATETIME"
}

for col, coltype in new_cols.items():
    if col not in existing_cols:
        cur.execute(f"ALTER TABLE user ADD COLUMN {col} {coltype}")
        print(f"[+] Added column: {col}")
    else:
        print(f"[skip] Column already exists: {col}")

conn.commit()
conn.close()
print("[+] Migration complete!")
