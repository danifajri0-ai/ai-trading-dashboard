from __future__ import annotations

import re
from typing import Any


POSITIVE_KEYWORDS = {
    "surge",
    "gain",
    "beats",
    "optimism",
    "rally",
    "strong",
    "growth",
    "upgrade",
    "breakout",
    "bullish",
}
NEGATIVE_KEYWORDS = {
    "drop",
    "fall",
    "misses",
    "risk",
    "fear",
    "weak",
    "decline",
    "volatility",
    "downgrade",
    "bearish",
    "selloff",
}
RISK_KEYWORDS = {
    "volatility",
    "uncertainty",
    "recession",
    "conflict",
    "inflation",
    "tightening",
    "liquidity",
    "sanction",
    "intervention",
}
TOPIC_KEYWORDS = {
    "macro": {"inflation", "cpi", "jobs", "gdp", "recession", "rate", "fed", "ecb", "boj"},
    "policy": {"policy", "central bank", "guidance", "hike", "cut"},
    "market_structure": {"liquidity", "spread", "session", "flow"},
    "crypto_narrative": {"etf", "on-chain", "exchange", "regulation", "mining"},
}


def score_sentiment_inputs(headlines: list[str], context: list[str] | None = None) -> dict[str, Any]:
    normalized_headlines = [headline.strip() for headline in headlines if isinstance(headline, str) and headline.strip()]
    normalized_context = [item.strip() for item in (context or []) if isinstance(item, str) and item.strip()]

    if not normalized_headlines and not normalized_context:
        return {
            "status": "not_available",
            "sentiment_score": None,
            "label": "Not Available",
            "key_topics": [],
            "risk_keywords": [],
            "caveat": "No headline or context input available for sentiment scoring.",
        }

    if not normalized_headlines and normalized_context:
        return {
            "status": "limited",
            "sentiment_score": 50.0,
            "label": "Neutral",
            "key_topics": _topics_from_text(normalized_context),
            "risk_keywords": _risk_keywords_from_text(normalized_context),
            "caveat": (
                "Sentiment score is context-only because no news headlines are available. "
                "Treat this as low-confidence evidence."
            ),
        }

    score = 50.0
    all_text = normalized_headlines + normalized_context
    tokens = _tokenize(" ".join(all_text))
    for token in tokens:
        if token in POSITIVE_KEYWORDS:
            score += 4.0
        if token in NEGATIVE_KEYWORDS:
            score -= 4.0
    score = max(0.0, min(100.0, score))

    label = "Neutral"
    if score >= 60.0:
        label = "Positive"
    elif score <= 40.0:
        label = "Negative"

    return {
        "status": "available",
        "sentiment_score": round(score, 2),
        "label": label,
        "key_topics": _topics_from_text(all_text),
        "risk_keywords": _risk_keywords_from_text(all_text),
        "caveat": (
            "Rule-based lightweight sentiment scoring from provided text only. "
            "It does not guarantee market direction."
        ),
    }


def _topics_from_text(texts: list[str]) -> list[str]:
    tokens = set(_tokenize(" ".join(texts)))
    topics: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if tokens.intersection(keywords):
            topics.append(topic)
    return topics


def _risk_keywords_from_text(texts: list[str]) -> list[str]:
    tokens = set(_tokenize(" ".join(texts)))
    return sorted(tokens.intersection(RISK_KEYWORDS))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())
