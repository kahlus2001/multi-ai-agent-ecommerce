import os
import json
import sqlite3
from pathlib import Path

def provision_database_from_json(json_path: str, db_path: str):
    # Ensure the output directory exists
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

    # Load the JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    data = raw["root"] if isinstance(raw, dict) and "root" in raw else raw
    print(f"🔍 Found {len(data)} records in dataset.")

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Drop old table if it exists
    cur.execute("DROP TABLE IF EXISTS products")

    # Create table
    cur.execute("""
    CREATE TABLE products (
        id TEXT PRIMARY KEY,
        actual_price REAL,
        average_rating REAL,
        brand TEXT,
        category TEXT,
        crawled_at TEXT,
        description TEXT,
        discount TEXT,
        images TEXT,
        out_of_stock BOOLEAN,
        pid TEXT,
        product_details TEXT,
        seller TEXT,
        selling_price REAL,
        sub_category TEXT,
        title TEXT,
        url TEXT
    )
    """)

    # Insert items
    for item in data:
        try:
            cur.execute("""
            INSERT INTO products (
                id, actual_price, average_rating, brand, category,
                crawled_at, description, discount, images, out_of_stock,
                pid, product_details, seller, selling_price, sub_category,
                title, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("_id"),
                float(item.get("actual_price", "0").replace(",", "").strip() or 0),
                float(item.get("average_rating", "0").strip() or 0),
                item.get("brand"),
                item.get("category"),
                item.get("crawled_at"),
                item.get("description"),
                item.get("discount"),
                json.dumps(item.get("images")) if isinstance(item.get("images"), list) else str(item.get("images")),
                int(bool(item.get("out_of_stock", False))),
                item.get("pid"),
                json.dumps(item.get("product_details")) if isinstance(item.get("product_details"), dict) else str(item.get("product_details")),
                item.get("seller"),
                float(item.get("selling_price", "0").replace(",", "").strip() or 0),
                item.get("sub_category"),
                item.get("title"),
                item.get("url")
            ))
        except Exception as e:
            print(f"⚠️ Skipping item due to error: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Database provisioned at: {db_path}")
