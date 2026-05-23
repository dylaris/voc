import json
import sqlite3
import os
import sys

def convert_json_to_sqlite(json_path="dict.json", db_path="dict.db"):
    """
    Convert JSON dictionary file to SQLite database
    JSON format: {"word": {"sw": "...", "translation": "..."}}
    """
    # Connect to SQLite database (creates if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table with word, sw, translation, freq fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT PRIMARY KEY,
            sw TEXT,
            translation TEXT NOT NULL,
            freq INTEGER DEFAULT 0
        )
    ''')

    # Create index for faster lookup
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sw ON dictionary(sw)')

    # Load JSON
    print(f"Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Inserting {len(data)} entries...")

    # Insert in batches for better performance
    batch = []
    batch_size = 10000

    for i, (word, info) in enumerate(data.items(), 1):
        sw = info.get("sw", "")
        translation = info.get("translation", "")
        batch.append((word, sw, translation, 0))

        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT OR REPLACE INTO dictionary (word, sw, translation, freq) VALUES (?, ?, ?, ?)",
                batch
            )
            conn.commit()
            print(f"Inserted {i} entries...")
            batch = []

    # Insert remaining
    if batch:
        cursor.executemany(
            "INSERT OR REPLACE INTO dictionary (word, sw, translation, freq) VALUES (?, ?, ?, ?)",
            batch
        )
        conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM dictionary")
    count = cursor.fetchone()[0]
    print(f"Done! Inserted {count} entries into {db_path}")

    # Close connection
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        # Only JSON file provided, generate DB name by changing extension
        json_name = sys.argv[1]
        db_name = os.path.splitext(json_name)[0] + ".db"
        convert_json_to_sqlite(json_name, db_name)
    elif len(sys.argv) >= 3:
        # Both JSON and DB name provided
        convert_json_to_sqlite(sys.argv[1], sys.argv[2])
    else:
        print("usage: python convert.py <JSON> <DB>")
