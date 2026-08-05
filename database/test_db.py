import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce.db"

conn = sqlite3.connect(DB_PATH)

# 1. Check table sizes
tables = ["customers", "products", "orders", "order_items"]

print("\n=== TABLE COUNTS ===")

for table in tables:
    count = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count:,}")


# 2. Test a multi-table JOIN
query = """
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_spent
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_items oi
    ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.name
ORDER BY total_spent DESC
LIMIT 10;
"""

print("\n=== TOP 10 CUSTOMERS BY SPENDING ===")

df = pd.read_sql_query(query, conn)

print(df.to_string(index=False))


# 3. Check broken foreign-key relationships
checks = {
    "orders -> customers": """
        SELECT COUNT(*)
        FROM orders o
        LEFT JOIN customers c
            ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """,

    "order_items -> orders": """
        SELECT COUNT(*)
        FROM order_items oi
        LEFT JOIN orders o
            ON oi.order_id = o.order_id
        WHERE o.order_id IS NULL
    """,

    "order_items -> products": """
        SELECT COUNT(*)
        FROM order_items oi
        LEFT JOIN products p
            ON oi.product_id = p.product_id
        WHERE p.product_id IS NULL
    """
}

print("\n=== FOREIGN KEY CHECKS ===")

for name, sql in checks.items():
    count = conn.execute(sql).fetchone()[0]
    print(f"{name}: {count} broken references")

conn.close()