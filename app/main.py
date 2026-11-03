from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.services.chatbot import build_chatbot
from app.services.repository import ResultRepository
from app.agent.workflow import QATestWorkflow
from app.services.chatbot import GroqRAGChatbot
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
DATASET = BASE / "data" / "golden_dataset.json"
app = FastAPI(title="AI-TestMate", version="1.0.0",
              description="A beginner-friendly AI response quality and regression testing harness.")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
repository = ResultRepository()
chatbot = build_chatbot()
workflow = QATestWorkflow(chatbot, repository)

def load_cases():
    return json.loads(DATASET.read_text(encoding="utf-8"))

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
async def health():
    import os
    return {"status": "ok", "chat_provider": os.getenv("AI_TESTMATE_CHAT_PROVIDER", "demo"),
            "knowledge_chunks": len(getattr(getattr(chatbot, "knowledge_base", None), "chunks", [])),
            "deepeval_enabled": os.getenv("AI_TESTMATE_USE_DEEPEVAL", "false").lower() == "true",
            "langgraph_enabled": os.getenv("AI_TESTMATE_USE_LANGGRAPH", "false").lower() == "true"}

@app.get("/api/cases")
async def cases():
    return load_cases()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    answer, sources = await chatbot.answer(request.message, request.history)
    return {"answer": answer, "sources": sources}

@app.post("/api/run-tests")
async def run_tests():
    return await workflow.run(load_cases())

@app.get("/api/results")
async def results():
    return repository.list_runs()

@app.get("/api/results/{run_id}")
async def result_detail(run_id: int):
    result = repository.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result

@app.get("/api/regression/{run_id}")
async def regression(run_id: int):
    current = repository.get_run(run_id)
    if not current:
        raise HTTPException(status_code=404, detail="Run not found")
    previous = repository.previous_run(run_id)
    if not previous:
        return {"run_id": run_id, "previous_run_id": None, "message": "No earlier run to compare."}
    old = {r["case_id"]: r for r in previous["results"]}
    changes = []
    for item in current["results"]:
        before = old.get(item["case_id"])
        if before:
            changes.append({"case_id": item["case_id"], "previous_passed": before["passed"],
                "current_passed": item["passed"], "previous_score": before["score"],
                "current_score": item["score"], "regressed": before["passed"] and not item["passed"]})
    return {"run_id": run_id, "previous_run_id": previous["id"], "changes": changes,
            "regressions": [c for c in changes if c["regressed"]]}


@app.post("/api/knowledge/reload")
async def reload_knowledge():
    kb = getattr(chatbot, "knowledge_base", None)
    if kb is None:
        raise HTTPException(status_code=400, detail="Knowledge-base reload is available in Groq RAG mode only.")
    try:
        count = kb.reload()
        return {"status": "ok", "chunks_indexed": count}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    kb = getattr(chatbot, "knowledge_base", None)
    if kb is None:
        raise HTTPException(status_code=400, detail="Knowledge uploads are available in Groq RAG mode only.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and Markdown files are supported.")
    content = await file.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be non-empty and no larger than 10 MB.")
    safe_name = Path(file.filename).name.replace("..", "_")
    destination = KNOWLEDGE_DIR / safe_name
    destination.write_bytes(content)
    try:
        count = kb.reload()
    except Exception as exc:
        destination.unlink(missing_ok=True)
        kb.reload()
        raise HTTPException(status_code=400, detail=f"Could not index file: {exc}")
    return {"status": "indexed", "filename": safe_name, "chunks_indexed": count}
