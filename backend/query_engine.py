from backend.text_to_sql import generate_sql
from backend.database_executor import execute_query
from backend.sql_repair import repair_sql
from backend.result_explainer import explain_result


MAX_REPAIR_ATTEMPTS = 2


def process_question(
    question: str,
    conversation_context: str = "",
    explain: bool = True
):

    # Step 1: Generate SQL
    sql = generate_sql(
    question,
    conversation_context
)

    print("\nGenerated SQL:\n")
    print(sql)

    df = None
    repair_attempts = 0

    # Step 2: Execute SQL
    # Repair only if SQL execution fails
    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):

        try:
            df = execute_query(sql)
            repair_attempts = attempt
            break

        except Exception as e:

            if attempt == MAX_REPAIR_ATTEMPTS:
                raise RuntimeError(
                    f"Query failed after "
                    f"{MAX_REPAIR_ATTEMPTS} repair attempts.\n"
                    f"Last SQL:\n{sql}\n"
                    f"Error: {e}"
                )

            print(f"\nSQL execution failed: {e}")
            print("\nAttempting SQL repair...")

            sql = repair_sql(
                question=question,
                sql=sql,
                error=str(e)
            )

            print("\nRepaired SQL:\n")
            print(sql)

    # Step 3: Explain result separately
    if explain:
       try:
        answer = explain_result(
            question=question,
            sql=sql,
            df=df
        )

       except Exception as e:
        print(f"\nResult explanation failed: {e}")

        answer = (
            "The query executed successfully, "
            "but I couldn't generate a natural-language explanation."
        )

    else:
      answer = None

    # Step 4: Return complete response
    return {
        "question": question,
        "sql": sql,
        "result": df,
        "answer": answer,
        "repair_attempts": repair_attempts
    }


if __name__ == "__main__":

    question = input("\nAsk a question: ")

    try:
        response = process_question(question)

        print("\nFinal SQL:\n")
        print(response["sql"])

        print("\nResult:\n")
        print(
            response["result"].to_string(index=False)
        )

        print("\nAnswer:\n")
        print(response["answer"])

        print(
            f"\nRepair attempts: "
            f"{response['repair_attempts']}"
        )

    except Exception as e:
        print(f"\nFailed: {e}")