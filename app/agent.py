"""A transparent tool-driven QA agent workflow.

This intentionally uses explicit Python tools and state rather than opaque autonomy.
It is straightforward to explain and can later be migrated to LangGraph.
"""
import time
from .chatbot import answer_question
from .evaluator import evaluate

class QATestAgent:
    def __init__(self, db):
        self.db = db
        self.trace = []

    def _tool(self, name, detail):
        self.trace.append({"tool": name, "detail": detail})

    def run(self, selected_ids=None):
        started = time.perf_counter()
        # Tool 1: choose the golden test cases to execute.
        if selected_ids:
            placeholders = ",".join("?" for _ in selected_ids)
            cases = self.db.execute(
                f"SELECT * FROM test_cases WHERE id IN ({placeholders}) ORDER BY id",
                selected_ids
            ).fetchall()
        else:
            cases = self.db.execute("SELECT * FROM test_cases ORDER BY id").fetchall()
        self._tool("select_test_cases", f"Selected {len(cases)} test case(s)")

        evaluated = []
        for case in cases:
            case_started = time.perf_counter()
            # Tool 2: call the chatbot under test.
            response = answer_question(case["question"])
            self._tool("query_chatbot", f"Executed test case #{case['id']}")
            # Tool 3: evaluate response against expected answer and trusted context.
            metrics = evaluate(
                case["question"], case["expected_answer"],
                case["reference_context"], response["answer"]
            )
            self._tool("evaluate_response", f"Scored test case #{case['id']}")
            latency = max(1, int((time.perf_counter() - case_started) * 1000))
            evaluated.append({
                "test_case_id": case["id"],
                "title": case["title"],
                "question": case["question"],
                "answer": response["answer"],
                "latency_ms": latency,
                **metrics
            })

        duration = max(1, int((time.perf_counter() - started) * 1000))
        total = len(evaluated)
        passed = sum(1 for item in evaluated if item["status"] == "PASS")
        failed = total - passed
        average = round(sum(x["overall_score"] for x in evaluated) / total, 1) if total else 0.0

        cursor = self.db.execute(
            "INSERT INTO runs (total, passed, failed, average_score, duration_ms) VALUES (?, ?, ?, ?, ?)",
            (total, passed, failed, average, duration)
        )
        run_id = cursor.lastrowid

        for item in evaluated:
            self.db.execute("""
                INSERT INTO results
                (run_id, test_case_id, status, answer, answer_match, relevance,
                 groundedness, safety_status, reason, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, item["test_case_id"], item["status"], item["answer"],
                item["answer_match"], item["relevance"], item["groundedness"],
                item["safety_status"], item["reason"], item["latency_ms"]
            ))
            if item["status"] == "FAIL":
                self._tool("record_regression_candidate", f"Saved failed case #{item['test_case_id']}")

        self._tool("save_run", f"Stored run #{run_id}")
        return {
            "run_id": run_id, "total": total, "passed": passed, "failed": failed,
            "average_score": average, "duration_ms": duration,
            "results": evaluated, "trace": self.trace
        }
