import sqlglot
from sqlglot import exp


class SQLValidationError(Exception):
    pass


ALLOWED_TABLES = {
    "customers",
    "products",
    "orders",
    "order_items"
}


FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
)


def validate_sql(sql: str) -> str:

    try:
        statements = sqlglot.parse(
            sql,
            read="sqlite"
        )
    except Exception as e:
        raise SQLValidationError(
            f"Invalid SQL syntax: {e}"
        )

    # Only one SQL statement
    if len(statements) != 1:
        raise SQLValidationError(
            "Only one SQL statement is allowed."
        )

    statement = statements[0]

    # Must be a SELECT query
    if not isinstance(statement, exp.Select):
        raise SQLValidationError(
            "Only SELECT queries are allowed."
        )

    # Block modification statements
    for forbidden in FORBIDDEN_EXPRESSIONS:

        if statement.find(forbidden):
            raise SQLValidationError(
                "Database modification is not allowed."
            )

    # Validate table names
    tables = {
        table.name
        for table in statement.find_all(exp.Table)
    }

    invalid_tables = tables - ALLOWED_TABLES

    if invalid_tables:
        raise SQLValidationError(
            f"Unknown tables: {invalid_tables}"
        )

    return statement.sql(
        dialect="sqlite"
    )
if __name__ == "__main__":

    queries = [
        "SELECT * FROM customers LIMIT 10",

        "DELETE FROM customers",

        "DROP TABLE customers",

        "SELECT * FROM fake_table",

        "SELECT * FROM customers; DROP TABLE customers;"
    ]

    for query in queries:

        print("\nQuery:")
        print(query)

        try:
            validated = validate_sql(query)

            print("✅ SAFE")
            print(validated)

        except SQLValidationError as e:

            print("❌ BLOCKED")
            print(e)