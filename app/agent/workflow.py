"""QA workflow: select cases -> query chatbot -> evaluate -> persist."""
import os
from app.services.evaluator import LocalEvaluator, add_deepeval_metrics

class QATestWorkflow:
    def __init__(self, chatbot, repository, evaluator=None):
        self.chatbot = chatbot
        self.repository = repository
        self.evaluator = evaluator or LocalEvaluator()

    async def run(self, cases: list[dict]) -> dict:
        if os.getenv("AI_TESTMATE_USE_LANGGRAPH", "false").lower() == "true":
            try:
                return await self._run_langgraph(cases)
            except ImportError:
                # Keep the app usable if the optional dependency was not installed.
                pass
        results = []
        for case in cases:
            answer, sources = await self.chatbot.answer(case["question"], case.get("history", []))
            evaluation = self.evaluator.evaluate(case, answer, case.get("contexts", []))
            deepeval = add_deepeval_metrics(case, answer, case.get("contexts", []))
            item = {
                "case_id": case["id"], "question": case["question"], "answer": answer,
                "sources": sources, "passed": evaluation.passed, "score": evaluation.score,
                "relevance": evaluation.relevance, "groundedness_proxy": evaluation.groundedness_proxy,
                "safety_passed": evaluation.safety_passed, "feedback": evaluation.feedback,
                "deepeval": deepeval,
            }
            if deepeval and not deepeval.get("error"):
                item["deepeval_passed"] = (
                    deepeval.get("answer_relevancy", 0) >= 0.5 and deepeval.get("faithfulness", 0) >= 0.5
                )
            results.append(item)
        run_id = self.repository.save_run(results)
        return {"run_id": run_id, "total": len(results), "passed": sum(r["passed"] for r in results),
                "failed": sum(not r["passed"] for r in results), "results": results,
                "workflow": "python"}

    async def _run_langgraph(self, cases: list[dict]) -> dict:
        from langgraph.graph import StateGraph, END
        async def execute(state):
            results = []
            for case in state["cases"]:
                answer, sources = await self.chatbot.answer(case["question"], case.get("history", []))
                ev = self.evaluator.evaluate(case, answer, case.get("contexts", []))
                de = add_deepeval_metrics(case, answer, case.get("contexts", []))
                results.append({"case_id": case["id"], "question": case["question"], "answer": answer,
                    "sources": sources, "passed": ev.passed, "score": ev.score, "relevance": ev.relevance,
                    "groundedness_proxy": ev.groundedness_proxy, "safety_passed": ev.safety_passed,
                    "feedback": ev.feedback, "deepeval": de})
            return {"results": results}
        async def persist(state):
            run_id = self.repository.save_run(state["results"])
            return {"run_id": run_id}
        graph = StateGraph(dict)
        graph.add_node("execute_tests", execute)
        graph.add_node("save_results", persist)
        graph.set_entry_point("execute_tests")
        graph.add_edge("execute_tests", "save_results")
        graph.add_edge("save_results", END)
        compiled = graph.compile()
        output = await compiled.ainvoke({"cases": cases})
        results = output["results"]
        return {"run_id": output["run_id"], "total": len(results),
            "passed": sum(r["passed"] for r in results), "failed": sum(not r["passed"] for r in results),
            "results": results, "workflow": "langgraph"}
