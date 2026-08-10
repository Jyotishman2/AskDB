from rag.schema_extractor import get_schema


TOPIC_DEFINITIONS = {
    "customers": [
        {
            "topic": "customer_identity",
            "description": "Unique customer records and personal identifiers.",
            "columns": ["customer_id", "name"],
        },
        {
            "topic": "customer_location",
            "description": "Customer geography and regional segmentation.",
            "columns": ["city", "state"],
        },
        {
            "topic": "customer_registration",
            "description": "Customer sign-up history and registration timing.",
            "columns": ["signup_date"],
        },
    ],
    "products": [
        {
            "topic": "product_identity",
            "description": "Core product inventory and naming information.",
            "columns": ["product_id", "product_name"],
        },
        {
            "topic": "product_category",
            "description": "Product classification and category-based grouping.",
            "columns": ["category"],
        },
        {
            "topic": "product_pricing",
            "description": "Product pricing and sales value context.",
            "columns": ["price"],
        },
    ],
    "orders": [
        {
            "topic": "order_identity",
            "description": "Order identity and order-level metadata.",
            "columns": ["order_id", "order_date"],
        },
        {
            "topic": "customer_relationship",
            "description": "Which customer placed each order and order ownership.",
            "columns": ["customer_id"],
        },
        {
            "topic": "order_status",
            "description": "Order lifecycle state such as pending, shipped, or cancelled.",
            "columns": ["status"],
        },
    ],
    "order_items": [
        {
            "topic": "order_item_identity",
            "description": "Each line item within an order and its item-level identifier.",
            "columns": ["order_item_id", "order_id"],
        },
        {
            "topic": "product_relationship",
            "description": "Product linkage between an order item and the product it contains.",
            "columns": ["product_id"],
        },
        {
            "topic": "quantity_and_revenue",
            "description": "Purchase quantity, unit prices, and revenue contribution for historical sales analysis.",
            "columns": ["quantity", "unit_price"],
        },
    ],
}


def _describe_column(column, table_name, primary_keys, foreign_key_map):
    name = column["name"]
    column_type = str(column["type"])
    details = [f"- {name} ({column_type})"]

    if name in primary_keys:
        details.append(" PRIMARY KEY")

    if name in foreign_key_map:
        details.append(f" FOREIGN KEY -> {foreign_key_map[name]}")

    details.append(f": {column.get('sample_values', [])}")
    return "".join(details)


def create_schema_chunks():
    schema = get_schema()
    chunks = []

    table_order = ["customers", "products", "orders", "order_items"]

    for table_name in table_order:
        table_info = schema.get(table_name, {})
        columns = table_info.get("columns", [])
        primary_keys = set(table_info.get("primary_key", []))
        foreign_key_map = {}

        for fk in table_info.get("foreign_keys", []):
            for source_column, target_column, target_table in zip(
                fk.get("constrained_columns", []),
                fk.get("referred_columns", []),
                [fk.get("referred_table")] * len(fk.get("constrained_columns", [])),
            ):
                foreign_key_map[source_column] = f"{target_table}.{target_column}"

        for definition in TOPIC_DEFINITIONS.get(table_name, []):
            topic = definition["topic"]
            selected_columns = []

            for column in columns:
                if column["name"] in definition["columns"]:
                    selected_columns.append(column)

            lines = [
                f"Table: {table_name}",
                f"Topic: {topic}",
                f"Purpose: {definition['description']}",
                "",
                "Relevant columns:",
            ]

            for column in selected_columns:
                lines.append(
                    _describe_column(
                        column,
                        table_name,
                        primary_keys,
                        foreign_key_map,
                    )
                )

            if not selected_columns:
                lines.append("- No columns matched this topic.")

            relationships = []
            for fk in table_info.get("foreign_keys", []):
                constrained = fk.get("constrained_columns", [])
                referenced = fk.get("referred_columns", [])
                if any(column_name in definition["columns"] for column_name in constrained):
                    relationship = (
                        f"{table_name}.{', '.join(constrained)} -> "
                        f"{fk.get('referred_table')}.{', '.join(referenced)}"
                    )
                    relationships.append(relationship)

            if relationships:
                lines.extend(["", "Relationships:"])
                lines.extend(f"- {relationship}" for relationship in relationships)

            sample_values = []
            for column in selected_columns:
                values = column.get("sample_values", [])
                if values:
                    sample_values.append(
                        f"{column['name']}: {', '.join(str(value) for value in values[:3])}"
                    )

            if sample_values:
                lines.extend(["", "Sample values:"])
                lines.extend(f"- {item}" for item in sample_values)

            chunk = {
                "id": f"{table_name}.{topic}",
                "table": table_name,
                "topic": topic,
                "content": "\n".join(lines),
            }
            chunks.append(chunk)

    return chunks
