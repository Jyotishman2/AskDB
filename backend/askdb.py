from backend.text_to_sql import generate_sql
from backend.database_executor import execute_query


def ask_database(question):

    sql = generate_sql(question)

    print("\nGenerated SQL:\n")
    print(sql)

    result = execute_query(sql)

    return {
        "question": question,
        "sql": sql,
        "result": result
    }


if __name__ == "__main__":

    question = input("\nAskDB > ")

    try:

        response = ask_database(question)

        print("\nResult:\n")

        print(
            response["result"].to_string(
                index=False
            )
        )

    except Exception as e:

        print(f"\nError: {e}")