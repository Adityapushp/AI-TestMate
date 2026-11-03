"""A deterministic demo support bot. Replace this adapter with a real chatbot API later."""
import re

KNOWLEDGE = [
    {
        "topic": "reset",
        "keywords": ["reset", "restart", "factory"],
        "answer": "To reset the smart fan, press and hold the Wi-Fi button for five seconds until the indicator light blinks.",
        "context": "To reset the smart fan, press and hold the Wi-Fi button for five seconds until the indicator light blinks."
    },
    {
        "topic": "wifi",
        "keywords": ["wifi", "wi-fi", "connect", "pair", "network"],
        "answer": "Open the companion app, select Add Device, and follow the pairing instructions on a 2.4 GHz Wi-Fi network.",
        "context": "Use the companion app and choose Add Device. The fan requires a 2.4 GHz Wi-Fi network for initial pairing."
    },
    {
        "topic": "warranty",
        "keywords": ["warranty", "guarantee", "coverage"],
        "answer": "The demo product has a two-year warranty. Check your invoice for the exact coverage dates.",
        "context": "This demo product includes a two-year warranty. Warranty coverage starts from the invoice date and is subject to the product terms."
    },
    {
        "topic": "noise",
        "keywords": ["noise", "sound", "rattle", "vibration"],
        "answer": "Turn the fan off, check for loose external fittings, and contact support if the noise continues. Do not open electrical components.",
        "context": "If unusual noise occurs, switch the fan off and check for loose external fittings. Do not open electrical components. Contact authorized support if the noise continues."
    },
]

def answer_question(question: str) -> dict:
    q = question.lower()
    # Safety behaviour is deliberately explicit and easy to inspect.
    if any(term in q for term in ["admin password", "other customers", "phone numbers", "private data"]):
        return {
            "answer": "I cannot provide passwords or other customers' personal information. Please contact authorized support for account-specific help.",
            "context": "Customer personal information and administrator credentials are confidential and must never be disclosed.",
            "topic": "safety"
        }

    scored = []
    for item in KNOWLEDGE:
        score = sum(1 for word in item["keywords"] if word in q)
        scored.append((score, item))
    score, best = max(scored, key=lambda pair: pair[0])
    if score == 0:
        return {
            "answer": "I don't have enough information to answer that confidently. Please share the product model or contact customer support.",
            "context": "The support knowledge base does not contain a verified answer for this question.",
            "topic": "unknown"
        }
    return {"answer": best["answer"], "context": best["context"], "topic": best["topic"]}
