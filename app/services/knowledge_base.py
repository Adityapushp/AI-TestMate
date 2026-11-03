"""Local TF-IDF retrieval for a small, editable support knowledge base.

No external embedding API or vector database is required. This is a lightweight
retrieval layer for a portfolio demo; for larger corpora, replace it with a
persistent vector store and evaluated embedding model.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class RetrievedChunk:
    source: str
    text: str
    score: float

class KnowledgeBase:
    def __init__(self, directory: Path, min_score: float = 0.035, chunk_words: int = 180, overlap: int = 35):
        self.directory = Path(directory)
        self.min_score = min_score
        self.chunk_words = chunk_words
        self.overlap = overlap
        self.chunks: list[tuple[str, str]] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.reload()

    def _read_file(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {'.md', '.txt'}:
            return path.read_text(encoding='utf-8', errors='ignore')
        if suffix == '.pdf':
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RuntimeError('PDF support requires pypdf. Install requirements.txt again.') from exc
            reader = PdfReader(str(path))
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        return ''

    def reload(self) -> int:
        self.chunks = []
        self.directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.directory.rglob('*')):
            if not path.is_file() or path.name.startswith('.') or path.name.upper() == 'README.MD':
                continue
            if path.suffix.lower() not in {'.md', '.txt', '.pdf'}:
                continue
            text = self._read_file(path)
            words = re.findall(r'\S+', text)
            if not words:
                continue
            step = max(1, self.chunk_words - self.overlap)
            for start in range(0, len(words), step):
                chunk = ' '.join(words[start:start + self.chunk_words]).strip()
                if len(chunk) > 40:
                    self.chunks.append((path.name, chunk))
        if self.chunks:
            # Word and character n-grams help match paraphrases such as "rattling" and "unusual noise".
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer='word', stop_words='english', sublinear_tf=True)
            self.matrix = self.vectorizer.fit_transform([text for _, text in self.chunks])
        else:
            self.vectorizer, self.matrix = None, None
        return len(self.chunks)

    def search(self, question: str, top_k: int = 4) -> list[RetrievedChunk]:
        if not self.vectorizer or self.matrix is None or not question.strip():
            return []
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        ranked = scores.argsort()[::-1][:top_k]
        return [RetrievedChunk(self.chunks[i][0], self.chunks[i][1], float(scores[i]))
                for i in ranked if scores[i] >= self.min_score]
