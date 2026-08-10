from backend.text_to_sql import generate_sql
from backend.database_executor import execute_query
from backend.sql_validator import validate_sql, SQLValidationError
from backend.sql_repair import repair_sql


MAX_REPAIR_ATTEMPTS = 2


def run_query(
    question,
    conversation_context=""
):
    sql = generate_sql(
        question,
        conversation_context
    )

    try:

        validated_sql = validate_sql(sql)

        result = execute_query(
            validated_sql
        )

        return {
            "success": True,
            "question": question,
            "sql": validated_sql,
            "result": result,
            "repaired": False,
            "repair_attempts": 0
        }

    except Exception as first_error:

        last_error = first_error
        current_sql = sql

        for attempt in range(MAX_REPAIR_ATTEMPTS):

            try:

                repaired_sql = repair_sql(
                    question,
                    current_sql,
                    str(last_error)
                )

                validated_sql = validate_sql(
                    repaired_sql
                )

                result = execute_query(
                    validated_sql
                )

                return {
                    "success": True,
                    "question": question,
                    "sql": validated_sql,
                    "result": result,
                    "repaired": True,
                    "repair_attempts": attempt + 1
                }

            except Exception as repair_error:

                current_sql = repaired_sql if "repaired_sql" in locals() else current_sql
                last_error = repair_error

        return {
            "success": False,
            "question": question,
            "sql": current_sql,
            "result": None,
            "repaired": True,
            "repair_attempts": MAX_REPAIR_ATTEMPTS,
            "error": str(last_error)
        }


if __name__ == "__main__":

    question = input("AskDB > ")

    try:

        response = run_query(
            question
        )

        print("\n" + "=" * 70)
        print("ASKDB RESULT")
        print("=" * 70)

        print("\nGenerated SQL:\n")
        print(response["sql"])

        print(
            "\nRepaired:",
            response["repaired"]
        )

        print(
            "Repair attempts:",
            response["repair_attempts"]
        )

        if response["success"]:

            print("\nResult:\n")
            print(
                response["result"].to_string(
                    index=False
                )
            )

        else:

            print("\nQuery failed:")
            print(response["error"])

    except Exception as e:

        print("\nQuery pipeline failed:")
        print(e)