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

    relationships = {table: [] for table in schema}

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

        # Useful semantic sample values only
        lines.append("\nSAMPLE VALUES:")

        has_samples = False

        for column in info["columns"]:

            name = column["name"]

            # Skip IDs
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

if __name__ == "__main__":

    documents = create_schema_documents()

    for doc in documents:

        print("\n")
        print("=" * 70)
        print(doc["content"])
        print("=" * 70)