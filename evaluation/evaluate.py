import json
from pathlib import Path

import pandas as pd

from backend.text_to_sql import generate_sql
from backend.database_executor import execute_query


BASE_DIR = Path(__file__).resolve().parent

TEST_FILE = BASE_DIR / "test_queries.json"
CACHE_FILE = BASE_DIR / "sql_cache.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def is_api_limit_error(error):
    message = str(error).lower()

    indicators = [
        "429",
        "resource_exhausted",
        "quota",
        "rate limit",
        "too many requests"
    ]

    return any(
        indicator in message
        for indicator in indicators
    )


def normalize_dataframe(df):
    normalized = df.copy()

    normalized.columns = [
        f"col_{i}"
        for i in range(len(normalized.columns))
    ]

    normalized = normalized.reset_index(drop=True)

    return normalized


def results_match(actual_df, expected_df):
    if actual_df.shape != expected_df.shape:
        return False

    actual = normalize_dataframe(actual_df)
    expected = normalize_dataframe(expected_df)

    try:
        actual = actual.sort_values(
            by=list(actual.columns),
            kind="stable"
        ).reset_index(drop=True)

        expected = expected.sort_values(
            by=list(expected.columns),
            kind="stable"
        ).reset_index(drop=True)

        pd.testing.assert_frame_equal(
            actual,
            expected,
            check_dtype=False,
            check_names=False,
            rtol=1e-5,
            atol=1e-8
        )

        return True

    except (AssertionError, TypeError):
        return False


def get_generated_sql(test, cache):
    test_id = str(test["id"])

    if test_id in cache:

        print("CACHE HIT: Using previously generated SQL")

        return cache[test_id]["sql"], True

    print("CACHE MISS: Generating SQL with LLM")

    sql = generate_sql(
        test["question"]
    )

    cache[test_id] = {
        "question": test["question"],
        "sql": sql
    }

    save_json(
        CACHE_FILE,
        cache
    )

    print("SQL saved to cache")

    return sql, False


def evaluate():
    tests = load_json(TEST_FILE)

    if CACHE_FILE.exists():
        cache = load_json(CACHE_FILE)
    else:
        cache = {}

    total = len(tests)

    evaluated = 0

    execution_success = 0
    execution_failures = 0

    semantic_success = 0
    semantic_failures = 0

    skipped = 0

    cache_hits = 0
    cache_misses = 0

    results = []

    for test in tests:

        question = test["question"]
        gold_sql = test["gold_sql"]

        print("\n" + "=" * 70)

        print(
            f"Test {test['id']}: "
            f"{question}"
        )

        print("=" * 70)

        try:

            # ---------------------------------
            # GET GENERATED SQL
            # ---------------------------------

            generated_sql, from_cache = get_generated_sql(
                test,
                cache
            )

            if from_cache:
                cache_hits += 1
            else:
                cache_misses += 1

            print("\nGenerated SQL:\n")
            print(generated_sql)

            # ---------------------------------
            # EXECUTE GENERATED SQL
            # ---------------------------------

            try:

                actual_df = execute_query(
                    generated_sql
                )

                execution_success += 1

            except Exception as execution_error:

                execution_failures += 1
                evaluated += 1

                results.append({
                    "id": test["id"],
                    "question": question,
                    "category": test["category"],
                    "status": "execution_failed",
                    "generated_sql": generated_sql,
                    "error": str(execution_error),
                    "from_cache": from_cache
                })

                print(
                    "\nFAIL: Generated SQL "
                    "could not execute"
                )

                print(execution_error)

                continue

            # ---------------------------------
            # EXECUTE GOLD SQL
            # ---------------------------------

            try:

                expected_df = execute_query(
                    gold_sql
                )

            except Exception as gold_error:

                execution_failures += 1
                evaluated += 1

                results.append({
                    "id": test["id"],
                    "question": question,
                    "category": test["category"],
                    "status": "gold_query_failed",
                    "generated_sql": generated_sql,
                    "gold_sql": gold_sql,
                    "error": str(gold_error),
                    "from_cache": from_cache
                })

                print(
                    "\nFAIL: Gold SQL "
                    "could not execute"
                )

                print(gold_error)

                continue

            # ---------------------------------
            # SEMANTIC COMPARISON
            # ---------------------------------

            semantic_correct = results_match(
                actual_df,
                expected_df
            )

            evaluated += 1

            if semantic_correct:

                semantic_success += 1

                status = "passed"

                print(
                    "\nPASS: Result matches gold query"
                )

            else:

                semantic_failures += 1

                status = "incorrect"

                print(
                    "\nINCORRECT: Generated query "
                    "executed, but result differs "
                    "from gold query"
                )

                print("\nActual result:\n")

                print(
                    actual_df.to_string(
                        index=False
                    )
                )

                print("\nExpected result:\n")

                print(
                    expected_df.to_string(
                        index=False
                    )
                )

            results.append({
                "id": test["id"],
                "question": question,
                "category": test["category"],
                "status": status,
                "semantic_correct": semantic_correct,
                "generated_sql": generated_sql,
                "gold_sql": gold_sql,
                "from_cache": from_cache
            })

        except Exception as e:

            if is_api_limit_error(e):

                skipped += 1

                results.append({
                    "id": test["id"],
                    "question": question,
                    "category": test["category"],
                    "status": "skipped",
                    "reason": "LLM API quota/rate limit"
                })

                print(
                    "\nSKIPPED: "
                    "LLM API quota/rate limit"
                )

            else:

                execution_failures += 1
                evaluated += 1

                results.append({
                    "id": test["id"],
                    "question": question,
                    "category": test["category"],
                    "status": "failed",
                    "error": str(e)
                })

                print(
                    f"\nFAIL: {e}"
                )

    # ---------------------------------
    # METRICS
    # ---------------------------------

    execution_rate = (
        execution_success / evaluated * 100
        if evaluated
        else 0
    )

    semantic_rate = (
        semantic_success / execution_success * 100
        if execution_success
        else 0
    )

    overall_rate = (
        semantic_success / total * 100
        if total
        else 0
    )

    print("\n")
    print("=" * 70)
    print("ASKDB EVALUATION V4")
    print("=" * 70)

    print(
        f"Total questions:             {total}"
    )

    print(
        f"Successfully evaluated:      {evaluated}"
    )

    print(
        f"Skipped (API limits):        {skipped}"
    )

    print()

    print(
        f"Execution successes:         "
        f"{execution_success}"
    )

    print(
        f"Execution failures:          "
        f"{execution_failures}"
    )

    print(
        f"Execution success rate:      "
        f"{execution_rate:.1f}%"
    )

    print()

    print(
        f"Semantically correct:        "
        f"{semantic_success}"
    )

    print(
        f"Semantically incorrect:      "
        f"{semantic_failures}"
    )

    print(
        f"Semantic accuracy:           "
        f"{semantic_rate:.1f}%"
    )

    print()

    print(
        f"Overall success rate:        "
        f"{overall_rate:.1f}%"
    )

    print()

    print(
        f"Cache hits:                  "
        f"{cache_hits}"
    )

    print(
        f"Cache misses / LLM calls:    "
        f"{cache_misses}"
    )

    # ---------------------------------
    # SAVE DETAILED REPORT
    # ---------------------------------

    report_file = (
        BASE_DIR / "evaluation_results.json"
    )

    save_json(
        report_file,
        results
    )

    print(
        "\nDetailed results saved to:"
    )

    print(report_file)


if __name__ == "__main__":
    evaluate()