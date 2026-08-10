import os
import time
import random

import pandas as pd
from dotenv import load_dotenv
from google import genai


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def explain_result(
    question: str,
    sql: str,
    df: pd.DataFrame
):
    if df.empty:
        return "No results were found for your question."

    result_text = df.to_string(index=False)

    prompt = f"""
You are a data analyst assistant.

The user asked:

{question}

The following SQL query was executed:

{sql}

The query returned:

{result_text}

Explain the result clearly and concisely.

Rules:
- Answer the user's question directly.
- Base the answer only on the provided result.
- Do not invent information.
- Do not mention SQL unless necessary.
- Do not explain how the query works.
- Keep the response concise.
- Never assume a currency symbol or currency type unless it is explicitly provided in the user's question or result.
- Preserve numeric values and units exactly as supported by the data.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            if not response.text:
                return "The result was retrieved successfully, but no explanation was generated."

            return response.text.strip()

        except Exception as e:
            if attempt == 2:
                raise RuntimeError(
                    f"Failed to explain result: {e}"
                )

            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)


if __name__ == "__main__":

    data = {
        "name": [
            "Akash Roy",
            "Aarav Gupta",
            "Vikram Yadav"
        ],
        "total_spending": [
            2124817.30,
            1729762.13,
            1660224.90
        ]
    }

    df = pd.DataFrame(data)

    question = "Who are the top 3 customers by spending?"

    sql = """
    SELECT
        name,
        total_spending
    FROM customers
    ORDER BY total_spending DESC
    LIMIT 3;
    """

    try:
        answer = explain_result(
            question=question,
            sql=sql,
            df=df
        )

        print("\nQuestion:\n")
        print(question)

        print("\nData:\n")
        print(df.to_string(index=False))

        print("\nAnswer:\n")
        print(answer)

    except Exception as e:
        print(f"\nResult explanation failed: {e}")