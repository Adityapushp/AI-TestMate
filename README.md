# AI-TestMate — RAG Chatbot Quality & Regression Testing

AI-TestMate is a beginner-friendly portfolio project for an AI Quality Engineer role. It combines a knowledge-grounded smart-fan support chatbot with a repeatable QA harness: golden test cases, response evaluation, SQLite run history, and regression comparison.

## What changed in this version

- **Groq API** is the generation provider. It uses Groq's OpenAI-compatible API endpoint.
- **Local retrieval** indexes Markdown, TXT, and PDF support documents on your machine. No paid embedding API is required.
- **RAG flow:** question → local TF-IDF retrieval → relevant source chunks → Groq-generated grounded response.
- **Document upload:** add PDF/TXT/MD files from the API and re-index them.
- **Abstention:** when no relevant source is found, the chatbot says it cannot verify the answer instead of inventing product-specific details.
- **Offline mode:** automated tests can run without a Groq key using `AI_TESTMATE_CHAT_PROVIDER=demo`.
- Existing golden dataset, evaluator, test runner, dashboard, SQLite history, and regression endpoint are retained.

> The included support article is generic demonstration content, not an official Atomberg manual. Add approved manuals/FAQs before relying on model-specific setup, reset, warranty, or repair instructions.

## 1. Setup on Windows PowerShell

```powershell
cd A:\AI-TestMate
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Get a Groq API key

1. Open [Groq Console](https://console.groq.com/keys) and create an API key.
2. In the project root, copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Replace `GROQ_API_KEY=replace_with_your_groq_api_key` with your key. Keep the key private and never upload `.env` to GitHub.
4. The default model is `openai/gpt-oss-20b`. If Groq changes free-plan availability, select a currently available model from [Groq's model/rate-limit documentation](https://console.groq.com/docs/rate-limits) and update `AI_TESTMATE_CHAT_MODEL` in `.env`.

## 3. Start the application

```powershell
uvicorn app.main:app --reload
```

Open:
- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health

The health endpoint shows the provider and number of indexed chunks. If you see a missing-key error at startup, check that `.env` is in the project root and contains a valid key.

## 4. Try the RAG chatbot

Ask natural questions such as:
- “My fan is rattling and making a strange noise. What should I check?”
- “The remote stopped responding. What can I safely try?”
- “The app cannot find my fan on Wi-Fi. What information should I check?”
- “There is a burning smell. What should I do?”

The answer includes the source filenames used. The chatbot is intentionally conservative: if the local documents do not cover a question, it directs the user to the exact product manual or authorised support.

## 5. Add your own product manuals / FAQs

Put `.pdf`, `.txt`, or `.md` files in the `knowledge_base` folder and call the reload endpoint:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/knowledge/reload
```

You can also upload one file using the interactive API docs at `/docs` → `POST /api/knowledge/upload`. Files are limited to 10 MB. The app indexes the uploaded file immediately. Use only documents you are allowed to use, and avoid uploading customer personal information.

## 6. Run QA and regression tests

Run the built-in golden test suite from the dashboard or:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/run-tests
```

Run automated code tests (no Groq API call is needed):

```powershell
pytest -q
```

If the test runner says async tests are unsupported, activate the project's `.venv` and reinstall dependencies with `pip install -r requirements.txt`.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | App/provider/index health |
| POST | `/api/chat` | Ask the RAG chatbot |
| POST | `/api/knowledge/upload` | Upload PDF/TXT/MD knowledge file |
| POST | `/api/knowledge/reload` | Re-index the knowledge folder |
| GET | `/api/cases` | Read golden test cases |
| POST | `/api/run-tests` | Execute QA cases and save results |
| GET | `/api/results` | List previous runs |
| GET | `/api/results/{run_id}` | Inspect a run |
| GET | `/api/regression/{run_id}` | Compare against the previous run |

## Architecture

```text
Browser dashboard
       │
       ▼
FastAPI ─────────────── SQLite (QA run history)
  │
  ├── /api/chat
  │      │
  │      ▼
  │   KnowledgeBase (local TF-IDF index)
  │      │ retrieves top matching chunks
  │      ▼
  │   Groq Chat Completions API
  │      │
  │      ▼
  │   Answer + source filenames
  │
  └── /api/run-tests
         │
         ▼
   Golden dataset → Chatbot → Local evaluator → SQLite
```

## Important limitations / interview honesty

1. Retrieval uses local TF-IDF word matching, not a neural embedding model. It is lightweight, explainable, and suitable for a small demo corpus; it may miss some paraphrases. Evaluate retrieval quality before expanding the corpus.
2. Groq free-plan access is rate-limited. Model IDs and limits can change; check the current Groq console/docs if a model becomes unavailable.
3. The included knowledge article is generic and is not official Atomberg documentation. Product-specific answers require approved source documents.
4. The local evaluator is a transparent heuristic, not a human-level semantic judge. Its scores are QA signals, not proof of correctness.
5. Prompt-injection defenses are starter safeguards, not a complete security guarantee.

## Interview explanation

“I built AI-TestMate as a small RAG-based support chatbot and AI quality-testing platform. It retrieves relevant passages from local product documents, passes those passages to a Groq-hosted language model, and returns a response with source filenames. I also built a golden test dataset, a local evaluator, run-history storage, and regression comparison so I can measure whether chatbot changes improve or break response quality. I kept retrieval local to avoid a paid embeddings dependency and added an abstention path for questions not covered by the documents.”
