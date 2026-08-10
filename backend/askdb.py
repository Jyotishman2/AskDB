from backend.query_engine import process_question


def ask_database(question: str):
    return process_question(question)


if __name__ == "__main__":

    question = input("\nAskDB > ")

    try:
        response = ask_database(question)

        print("\nFinal SQL:\n")
        print(response["sql"])

        print("\nResult:\n")
        print(
            response["result"].to_string(
                index=False
            )
        )

        print("\nAnswer:\n")
        print(response["answer"])

        print(
            f"\nRepair attempts: "
            f"{response['repair_attempts']}"
        )

    except Exception as e:
        print(f"\nError: {e}")