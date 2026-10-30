import asyncio
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from evals.graders.graders import (
    grade_access_control,
    grade_keyword_coverage,
    grade_refusal,
    grade_source_recall,
)
from packages.harness.agent import ask_docs

DATASET_PATH = "evals/datasets/golden.jsonl"
REPORTS_DIR = "evals/reports"
MIN_PASS_RATE = 0.80


async def run_evaluation():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    results = []
    print("\n" + "=" * 60)
    print("STARTING EVALUATION HARNESS RUN")
    print("=" * 60)

    for c in cases:
        user_id = c.get("user_id", "alice")
        res = await ask_docs(
            question=c["question"],
            workspace_id=c["workspace_id"],
            user_id=user_id,
        )

        grades = [
            grade_source_recall(c.get("expected_sources", []), res.get("citations", [])),
            grade_keyword_coverage(c.get("expected_keywords", []), res.get("answer", "")),
            grade_refusal(c.get("must_refuse", False), res.get("status")),
            grade_access_control(c.get("expect_denied", False), res.get("status")),
        ]

        passed = all(g.passed for g in grades)
        results.append({"case_id": c["id"], "passed": passed, "grades": grades, "result": res})
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {c['id']:<10} - Status: {res.get('status'):<8} | Question: {c['question'][:40]}")

    pass_rate = sum(1 for r in results if r["passed"]) / len(results)
    report_path = os.path.join(REPORTS_DIR, "latest.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"pass_rate": pass_rate, "total": len(results)}, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Overall Pass Rate: {pass_rate * 100:.1f}%")
    print("=" * 60)

    if pass_rate < MIN_PASS_RATE:
        print(f"EVALUATION GATE FAILED: Pass rate below {MIN_PASS_RATE * 100}% threshold.")
        sys.exit(1)
    print("EVALUATION GATE PASSED.")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
