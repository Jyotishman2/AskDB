import os
import time
import random

from dotenv import load_dotenv
from google import genai

from rag.schema_documents import create_schema_documents
from backend.sql_validator import validate_sql, SQLValidationError


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def build_schema_context():
    documents = create_schema_documents()

    return "\n\n".join(
        doc["content"]
        for doc in documents
    )


def repair_sql(question, sql, error):

    schema_context = build_schema_context()

    prompt = f"""
You are an expert SQLite SQL query repair system.

Your task is to fix an invalid SQL query while preserving
the user's original intent.

DATABASE SCHEMA:

{schema_context}

USER QUESTION:

{question}

GENERATED SQL:

{sql}

DATABASE / VALIDATION ERROR:

{error}

RULES:

1. Use only tables and columns present in the schema.
2. Preserve the original user's intent.
3. Generate SQLite-compatible SQL.
4. Return only one SQL statement.
5. Return only a SELECT query.
6. Do not use INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, REPLACE, TRUNCATE, PRAGMA, ATTACH, or DETACH.
7. Do not invent tables or columns.
8. Return ONLY the corrected SQL.
9. Do not include explanations.
10. Do not use markdown code blocks.
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            repaired_sql = response.text.strip()

            repaired_sql = (
                repaired_sql
                .replace("```sql", "")
                .replace("```", "")
                .strip()
            )

            validated_sql = validate_sql(
                repaired_sql
            )

            return validated_sql

        except SQLValidationError as e:

            if attempt == 2:
                raise SQLValidationError(
                    f"Repaired SQL is still invalid: {e}"
                )

            error = str(e)

            time.sleep(
                (2 ** attempt) +
                random.uniform(0, 1)
            )

        except Exception as e:

            if attempt == 2:
                raise

            time.sleep(
                (2 ** attempt) +
                random.uniform(0, 1)
            )

    raise SQLValidationError(
        "SQL repair failed."
    )


if __name__ == "__main__":

    question = (
        "Show the top 5 products by total quantity sold."
    )

    bad_sql = """
    SELECT p.product_name, SUM(oi.amount)
    FROM products p
    JOIN order_items oi
    ON p.product_id = oi.product_id
    GROUP BY p.product_name
    """

    error = (
        "no such column: oi.amount"
    )

    try:

        repaired = repair_sql(
            question,
            bad_sql,
            error
        )

        print("\nRepaired SQL:\n")
        print(repaired)

    except Exception as e:

        print("\nRepair failed:")
        print(e)