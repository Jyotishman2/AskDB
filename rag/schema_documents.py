from rag.schema_extractor import get_schema


TABLE_DESCRIPTIONS = {
    "customers": "Stores information about customers who purchase products.",
    "products": "Stores information about products available for purchase.",
    "orders": "Stores orders placed by customers.",
    "order_items": "Stores individual products contained within each order."
}


COLUMN_DESCRIPTIONS = {
    "customers": {
        "customer_id": "Unique identifier for a customer.",
        "name": "Full name of the customer.",
        "city": "City where the customer is located.",
        "state": "State where the customer is located.",
        "signup_date": "Date when the customer registered."
    },

    "products": {
        "product_id": "Unique identifier for a product.",
        "product_name": "Name of the product.",
        "category": "Category the product belongs to.",
        "price": "Current listed price of the product."
    },

    "orders": {
        "order_id": "Unique identifier for an order.",
        "customer_id": "Customer who placed the order.",
        "order_date": "Date when the order was placed.",
        "status": "Current status of the order."
    },

    "order_items": {
        "order_item_id": "Unique identifier for an order item.",
        "order_id": "Order containing this item.",
        "product_id": "Product contained in the order.",
        "quantity": "Number of units purchased.",
        "unit_price": "Price of one unit at the time of purchase."
    }
}


def get_relationships(schema):
    relationships = {
        table: []
        for table in schema
    }

    for table, info in schema.items():

        for fk in info["foreign_keys"]:

            source_column = fk["constrained_columns"][0]
            target_table = fk["referred_table"]
            target_column = fk["referred_columns"][0]

            outgoing = (
                f"{table}.{source_column} → "
                f"{target_table}.{target_column}"
            )

            incoming = (
                f"{target_table}.{target_column} ← "
                f"{table}.{source_column}"
            )

            relationships[table].append(outgoing)
            relationships[target_table].append(incoming)

    return relationships


def create_schema_documents():
    schema = get_schema()

    relationships = get_relationships(schema)

    documents = []

    for table, info in schema.items():

        lines = []

        lines.append(f"TABLE: {table}")

        lines.append("\nDESCRIPTION:")
        lines.append(
            TABLE_DESCRIPTIONS.get(
                table,
                f"Database table named {table}."
            )
        )

        lines.append("\nCOLUMNS:")

        primary_keys = set(info["primary_key"])

        for column in info["columns"]:

            name = column["name"]
            data_type = column["type"]

            description = (
                COLUMN_DESCRIPTIONS
                .get(table, {})
                .get(name, "")
            )

            pk_text = ""

            if name in primary_keys:
                pk_text = " Primary key."

            lines.append(
                f"- {name} ({data_type}): "
                f"{description}{pk_text}"
            )

        lines.append("\nSAMPLE VALUES:")

        has_samples = False

        for column in info["columns"]:

            name = column["name"]

            if name.endswith("_id"):
                continue

            samples = column["sample_values"]

            if samples:

                values = ", ".join(
                    str(value)
                    for value in samples
                )

                lines.append(
                    f"- {name}: {values}"
                )

                has_samples = True

        if not has_samples:
            lines.append("None")

        lines.append("\nRELATIONSHIPS:")

        table_relationships = relationships[table]

        if table_relationships:

            for relationship in table_relationships:
                lines.append(
                    f"- {relationship}"
                )

        else:
            lines.append("None")

        document = "\n".join(lines)

        documents.append({
            "table": table,
            "content": document
        })

    return documents

def retrieve_relevant_schema(question):
    documents = create_schema_documents()

    question_words = set(
        question.lower()
        .replace("?", " ")
        .replace(",", " ")
        .replace(".", " ")
        .split()
    )

    table_keywords = {
        "customers": {
            "customer",
            "customers",
            "name",
            "city",
            "state",
            "signup",
            "registered"
        },

        "products": {
            "product",
            "products",
            "category",
            "categories",
            "price"
        },

        "orders": {
            "order",
            "orders",
            "status",
            "date",
            "placed"
        },

        "order_items": {
            "quantity",
            "sold",
            "revenue",
            "spending",
            "unit_price",
            "items"
        }
    }

    scores = {}

    for document in documents:

        table = document["table"]

        score = len(
            question_words &
            table_keywords.get(table, set())
        )

        scores[table] = score

    selected_tables = {
        table
        for table, score in scores.items()
        if score > 0
    }

    # Revenue/spending requires order_items.
    if question_words & {
        "revenue",
        "spending",
        "spent",
        "sales"
    }:
        selected_tables.add("order_items")

    # Product-related quantity questions need products.
    if question_words & {
        "product",
        "products",
        "category",
        "categories"
    }:
        selected_tables.add("products")

    # Customer-related questions need customers.
    if question_words & {
        "customer",
        "customers",
        "name",
        "city",
        "state",
        "signup"
    }:
        selected_tables.add("customers")

    # If order_items is needed for a customer-level metric,
    # orders are required to connect customers to order_items.
    if (
        "customers" in selected_tables
        and "order_items" in selected_tables
    ):
        selected_tables.add("orders")

    return [
        document
        for document in documents
        if document["table"] in selected_tables
    ]

if __name__ == "__main__":

    documents = create_schema_documents()

    for doc in documents:

        print("\n")
        print("=" * 70)
        print(doc["content"])
        print("=" * 70)