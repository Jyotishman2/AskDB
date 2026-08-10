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

    if not sql or not sql.strip():
        raise SQLValidationError(
            "SQL query cannot be empty."
        )

    try:
        statements = sqlglot.parse(
            sql,
            read="sqlite"
        )

    except Exception as e:
        raise SQLValidationError(
            f"Invalid SQL syntax: {e}"
        )

    if len(statements) != 1:
        raise SQLValidationError(
            "Only one SQL statement is allowed."
        )

    statement = statements[0]

    if not isinstance(statement, exp.Select):
        raise SQLValidationError(
            "Only SELECT queries are allowed."
        )

    for forbidden in FORBIDDEN_EXPRESSIONS:

        if statement.find(forbidden):
            raise SQLValidationError(
                "Database modification is not allowed."
            )

    tables = {
        table.name.lower()
        for table in statement.find_all(exp.Table)
    }

    invalid_tables = tables - ALLOWED_TABLES

    if invalid_tables:
        raise SQLValidationError(
            f"Unknown tables: {sorted(invalid_tables)}"
        )

    return statement.sql(
        dialect="sqlite"
    )


if __name__ == "__main__":

    queries = [
        "SELECT * FROM customers LIMIT 10",

        "SELECT name FROM customers WHERE city = 'Guwahati'",

        """
        SELECT p.product_name, SUM(oi.quantity)
        FROM products p
        JOIN order_items oi
        ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name
        """,

        "DELETE FROM customers",

        "DROP TABLE customers",

        "UPDATE customers SET city = 'Delhi'",

        "INSERT INTO customers VALUES (1, 'Test', 'Delhi', 'Delhi', '2025-01-01')",

        "SELECT * FROM fake_table",

        "SELECT * FROM customers; DROP TABLE customers;",

        "PRAGMA database_list",

        "ATTACH DATABASE 'test.db' AS test"
    ]

    for query in queries:

        print("\nQuery:")
        print(query.strip())

        try:

            validated = validate_sql(query)

            print("SAFE")
            print(validated)

        except SQLValidationError as e:

            print("BLOCKED")
            print(e)