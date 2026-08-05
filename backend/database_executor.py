from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from backend.sql_validator import validate_sql


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}"
)


def execute_query(sql: str):

    safe_sql = validate_sql(sql)

    with engine.connect() as connection:

        result = connection.execute(
            text(safe_sql)
        )

        columns = result.keys()
        rows = result.fetchall()

    df = pd.DataFrame(
        rows,
        columns=columns
    )

    return df


if __name__ == "__main__":

    query = """
    SELECT
        c.customer_id,
        c.name,
        SUM(oi.quantity * oi.unit_price) AS total_spent
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    JOIN order_items oi
        ON o.order_id = oi.order_id
    GROUP BY c.customer_id, c.name
    ORDER BY total_spent DESC
    LIMIT 10
    """

    try:

        df = execute_query(query)

        print("\nQuery Result:\n")

        print(
            df.to_string(index=False)
        )

    except Exception as e:

        print(f"\nQuery failed: {e}")