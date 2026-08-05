import os
import time
import random

from dotenv import load_dotenv
from google import genai

from rag.schema_documents import create_schema_documents


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


def generate_sql(question):
    schema_context = build_schema_context()

    prompt = f"""
You are an expert SQLite SQL developer.

Your task is to convert a user's natural-language question
into a valid SQLite SELECT query.

DATABASE SCHEMA:

{schema_context}

BUSINESS RULES:

1. Revenue must be calculated using:
   order_items.quantity * order_items.unit_price

2. Do not use products.price to calculate historical sales revenue.

3. Use relationships defined in the database schema when joining tables.

4. Generate SQLite-compatible SQL.

5. Only generate SELECT queries.

6. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, REPLACE, or TRUNCATE statements.

7. Use clear table aliases when joining multiple tables.

8. Do not invent tables or columns that do not exist in the schema.

USER QUESTION:

{question}

Return ONLY the SQL query.
Do not include markdown.
Do not include ```sql.
Do not explain the query.
"""

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:
            error_message = str(e)

            retryable = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            )

            if not retryable:
                raise

            if attempt == max_retries - 1:
                raise

            wait_time = (2 ** attempt) + random.random()

            print(
                f"LLM temporarily unavailable. "
                f"Retrying in {wait_time:.1f}s..."
            )

            time.sleep(wait_time)


if __name__ == "__main__":
    question = input("AskDB > ")

    sql = generate_sql(question)

    print("\nGenerated SQL:\n")
    print(sql)