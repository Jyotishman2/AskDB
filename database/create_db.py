import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "ecommerce.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
DATA_DIR = BASE_DIR / "data"

conn = sqlite3.connect(DB_PATH)

try:
    conn.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn.executescript(schema)

    tables = [
        "customers",
        "products",
        "orders",
        "order_items"
    ]

    for table in tables:
        csv_path = DATA_DIR / f"{table}.csv"

        df = pd.read_csv(csv_path)

        df.to_sql(
            table,
            conn,
            if_exists="append",
            index=False
        )

        print(f"Loaded {len(df):,} rows → {table}")

    conn.commit()

    print("\nDatabase created successfully!")
    print(f"Location: {DB_PATH}")

finally:
    conn.close()