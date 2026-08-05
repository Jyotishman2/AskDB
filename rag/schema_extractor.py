from pathlib import Path

from sqlalchemy import create_engine, inspect, text


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ecommerce.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

inspector = inspect(engine)


def get_sample_values(table_name, column_name, limit=3):
    query = text(
        f'''
        SELECT DISTINCT "{column_name}"
        FROM "{table_name}"
        WHERE "{column_name}" IS NOT NULL
        LIMIT :limit
        '''
    )

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"limit": limit}
        )

        return [row[0] for row in result.fetchall()]


def get_schema():
    schema = {}

    tables = inspector.get_table_names()

    for table in tables:
        columns = inspector.get_columns(table)
        primary_key = inspector.get_pk_constraint(table)
        foreign_keys = inspector.get_foreign_keys(table)

        column_info = []

        for column in columns:
            samples = get_sample_values(
                table,
                column["name"]
            )

            column_info.append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "sample_values": samples
            })

        schema[table] = {
            "columns": column_info,
            "primary_key": primary_key.get(
                "constrained_columns",
                []
            ),
            "foreign_keys": foreign_keys
        }

    return schema


if __name__ == "__main__":
    schema = get_schema()

    for table, info in schema.items():

        print(f"\n{'=' * 60}")
        print(f"TABLE: {table}")
        print("=" * 60)

        print("\nCOLUMNS:")

        for column in info["columns"]:

            print(
                f"- {column['name']} "
                f"{column['type']}"
            )

            print(
                f"  Samples: "
                f"{column['sample_values']}"
            )

        print("\nPRIMARY KEY:")
        print(info["primary_key"])

        print("\nFOREIGN KEYS:")

        if not info["foreign_keys"]:
            print("None")

        for fk in info["foreign_keys"]:

            source = ", ".join(
                fk["constrained_columns"]
            )

            target = ", ".join(
                fk["referred_columns"]
            )

            print(
                f"- {table}.{source} "
                f"→ "
                f"{fk['referred_table']}.{target}"
            )