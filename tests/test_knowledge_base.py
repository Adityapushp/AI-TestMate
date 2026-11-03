from pathlib import Path
from app.services.knowledge_base import KnowledgeBase

def test_retrieval_finds_noise_guidance():
    kb = KnowledgeBase(Path(__file__).resolve().parents[1] / "knowledge_base")
    results = kb.search("my ceiling fan is rattling and making strange sounds")
    assert results
    assert "smart_fan_support.md" in [item.source for item in results]

def test_retrieval_returns_no_match_for_unrelated_question():
    kb = KnowledgeBase(Path(__file__).resolve().parents[1] / "knowledge_base", min_score=0.12)
    assert kb.search("how do I bake chocolate cookies") == []
