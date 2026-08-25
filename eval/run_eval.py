import os
import time
from datetime import datetime, timezone

import duckdb
import matplotlib.pyplot as plt

from agent.graph import run_agent
from eval.judge import judge_answer
from eval.tasks import TASKS

DB_PATH = os.path.join(os.path.dirname(__file__), "results.duckdb")
CHART_PATH = os.path.join(os.path.dirname(__file__), "results.png")

SCHEMA = """
CREATE TABLE IF NOT EXISTS eval_runs (
    run_id TIMESTAMP,
    task_id VARCHAR,
    category VARCHAR,
    question VARCHAR,
    answer VARCHAR,
    passed BOOLEAN,
    steps INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_seconds DOUBLE
)
"""


def grade(task: dict, answer: str) -> bool:
    if "expected" in task:
        return task["expected"] in answer
    return judge_answer(task["question"], task["reference"], answer)


def run_task(task: dict) -> dict:
    start = time.perf_counter()
    result = run_agent(task["question"])
    latency = time.perf_counter() - start

    answer = result["messages"][-1]["content"]
    passed = grade(task, answer)

    return {
        "task_id": task["id"],
        "category": task["category"],
        "question": task["question"],
        "answer": answer,
        "passed": passed,
        "steps": result["steps"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
        "latency_seconds": latency,
    }


def save_results(con: duckdb.DuckDBPyConnection, run_id: datetime, rows: list[dict]) -> None:
    con.execute(SCHEMA)
    con.executemany(
        """
        INSERT INTO eval_runs
        (run_id, task_id, category, question, answer, passed, steps,
         prompt_tokens, completion_tokens, latency_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                run_id,
                r["task_id"],
                r["category"],
                r["question"],
                r["answer"],
                r["passed"],
                r["steps"],
                r["prompt_tokens"],
                r["completion_tokens"],
                r["latency_seconds"],
            )
            for r in rows
        ],
    )


def print_summary(rows: list[dict]) -> None:
    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    print(f"\n{passed}/{total} passed ({passed / total:.0%})")

    categories = sorted({r["category"] for r in rows})
    for category in categories:
        cat_rows = [r for r in rows if r["category"] == category]
        cat_passed = sum(1 for r in cat_rows if r["passed"])
        avg_steps = sum(r["steps"] for r in cat_rows) / len(cat_rows)
        avg_tokens = sum(r["prompt_tokens"] + r["completion_tokens"] for r in cat_rows) / len(cat_rows)
        avg_latency = sum(r["latency_seconds"] for r in cat_rows) / len(cat_rows)
        print(
            f"  {category:12s} {cat_passed}/{len(cat_rows)} passed | "
            f"avg steps {avg_steps:.1f} | avg tokens {avg_tokens:.0f} | avg latency {avg_latency:.2f}s"
        )


def plot_results(con: duckdb.DuckDBPyConnection) -> None:
    data = con.execute(
        """
        SELECT category,
               avg(passed::INT) AS pass_rate,
               avg(latency_seconds) AS avg_latency
        FROM eval_runs
        WHERE run_id = (SELECT max(run_id) FROM eval_runs)
        GROUP BY category
        ORDER BY category
        """
    ).fetchall()

    categories = [row[0] for row in data]
    pass_rates = [row[1] * 100 for row in data]
    latencies = [row[2] for row in data]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    ax1.bar(categories, pass_rates, color="#4C72B0")
    ax1.set_title("Pass rate by category")
    ax1.set_ylabel("% passed")
    ax1.set_ylim(0, 100)

    ax2.bar(categories, latencies, color="#DD8452")
    ax2.set_title("Average latency by category")
    ax2.set_ylabel("seconds")

    fig.tight_layout()
    fig.savefig(CHART_PATH, dpi=150)
    print(f"Chart saved to {CHART_PATH}")


def main() -> None:
    run_id = datetime.now(timezone.utc)
    rows = [run_task(task) for task in TASKS]

    con = duckdb.connect(DB_PATH)
    save_results(con, run_id, rows)
    print_summary(rows)
    plot_results(con)
    con.close()


if __name__ == "__main__":
    main()
