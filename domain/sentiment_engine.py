from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketContextItem:
    title: str
    detail: str


@dataclass(frozen=True)
class SentimentScore:
    label: str
    score: int
    note: str


def build_market_context(pair_label: str, period: str, interval: str) -> tuple[MarketContextItem, ...]:
    asset_note = _asset_specific_note(pair_label)
    timeframe_note = (
        f"Analisis memakai {interval} dalam periode {period}. "
        "Semakin kecil timeframe, semakin besar noise dan kebutuhan konfirmasi candle."
    )
    return (
        MarketContextItem("Konteks Aset", asset_note),
        MarketContextItem("Konteks Timeframe", timeframe_note),
        MarketContextItem(
            "Checklist Sebelum Entry",
            "Cek kalender ekonomi, spread, sesi market, dan berita besar sebelum mengambil posisi.",
        ),
    )


def score_sentiment(pair_label: str, context_items: tuple[MarketContextItem, ...]) -> SentimentScore:
    base_score = 50
    if pair_label in {"BTC/USD", "ETH/USD", "SOL/USD"}:
        base_score = 55
    elif pair_label == "XAU/USD":
        base_score = 52
    elif pair_label in {"EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"}:
        base_score = 50

    context_bonus = 0
    for item in context_items:
        detail = item.detail.lower()
        if "risk-off" in detail or "intervensi" in detail:
            context_bonus -= 3
        if "likuiditas" in detail or "konfirmasi" in detail:
            context_bonus += 2

    score = max(0, min(100, base_score + context_bonus))
    if score >= 60:
        label = "Positive"
    elif score <= 40:
        label = "Negative"
    else:
        label = "Neutral"
    return SentimentScore(label=label, score=score, note="Rule-based sentiment scoring.")


def _asset_specific_note(pair_label: str) -> str:
    if pair_label in {"BTC/USD", "ETH/USD"}:
        return "Crypto sensitif terhadap risk appetite, likuidasi leverage, arus ETF, dan pergerakan USD."
    if pair_label == "SOL/USD":
        return "SOL sensitif terhadap sentimen altcoin, likuiditas market crypto, dan kekuatan USD."
    if pair_label == "XAU/USD":
        return "Gold sensitif terhadap USD, yield obligasi, ekspektasi suku bunga, dan risk-off global."
    if pair_label in {"EUR/USD", "GBP/USD"}:
        return "Pair mayor Eropa sensitif terhadap data inflasi, bank sentral, dan kekuatan dolar AS."
    if pair_label == "USD/JPY":
        return "USD/JPY sensitif terhadap yield AS, kebijakan BoJ, dan intervensi verbal Jepang."
    if pair_label in {"AUD/USD", "USD/CAD"}:
        return "AUD/USD dan USD/CAD sensitif terhadap komoditas, data ekonomi, dan dinamika kekuatan USD."
    return "Gunakan konfirmasi berita dan likuiditas sebelum entry."

