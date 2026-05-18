import json
import sqlite3
import os
import sys

def convert_json_to_sqlite(json_path="dict.json", db_path="dict.db"):
    """
    Convert JSON dictionary file to SQLite database
    """
    # Connect to SQLite database (creates if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT PRIMARY KEY,
            translation TEXT NOT NULL
        )
    ''')

    # Create index for faster lookup
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word)')

    # Load JSON
    print(f"Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Inserting {len(data)} entries...")

    # Insert in batches for better performance
    batch = []
    batch_size = 10000

    for i, (word, translation) in enumerate(data.items(), 1):
        batch.append((word, translation))

        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT OR REPLACE INTO dictionary (word, translation) VALUES (?, ?)",
                batch
            )
            conn.commit()
            print(f"Inserted {i} entries...")
            batch = []

    # Insert remaining
    if batch:
        cursor.executemany(
            "INSERT OR REPLACE INTO dictionary (word, translation) VALUES (?, ?)",
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
