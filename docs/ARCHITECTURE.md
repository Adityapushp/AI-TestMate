# Architecture

1. FastAPI receives a support question.
2. `KnowledgeBase` indexes local Markdown/TXT/PDF files with scikit-learn TF-IDF.
3. The top matching chunks are inserted into a constrained prompt.
4. Groq Chat Completions generates a concise answer grounded in those chunks.
5. The response returns source filenames; if retrieval returns no suitable chunks, the assistant abstains.
6. The separate QA workflow runs golden cases, evaluates responses, stores them in SQLite, and supports regression comparison.

The retrieval implementation is deliberately lightweight TF-IDF, not neural semantic embeddings. Replace it with an evaluated embedding/vector database when the corpus or recall requirements justify that complexity.
