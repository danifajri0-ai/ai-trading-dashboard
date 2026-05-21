from __future__ import annotations

from dataclasses import dataclass

from technical_analysis import MarketLevels, RiskPlan, TrendAnalysis


@dataclass(frozen=True)
class SignalFactor:
    name: str
    score: int
    detail: str


@dataclass(frozen=True)
class SignalSummary:
    action: str
    confidence: int
    label: str
    summary: str
    factors: tuple[SignalFactor, ...]


def build_signal_summary(levels: MarketLevels, trend: TrendAnalysis, risk_plan: RiskPlan) -> SignalSummary:
    factors: list[SignalFactor] = []

    if trend.direction == "WAIT":
        factors.append(SignalFactor("Trend", 10, "EMA belum selaras, bias utama masih netral."))
    else:
        factors.append(SignalFactor("Trend", 30, f"Trend mendukung skenario {trend.direction}."))

    factors.append(_score_rsi(levels.rsi, trend.direction))
    factors.append(_score_price_location(levels, trend.direction))
    factors.append(_score_volatility(levels.atr_percent))
    factors.append(_score_risk_plan(risk_plan))

    raw_score = sum(factor.score for factor in factors)
    confidence = max(0, min(100, raw_score))

    if trend.direction == "WAIT" or confidence < 45:
        action = "WAIT"
    else:
        action = trend.direction

    label = _confidence_label(confidence)
    summary = _build_summary(action, label, confidence)

    return SignalSummary(
        action=action,
        confidence=confidence,
        label=label,
        summary=summary,
        factors=tuple(factors),
    )


def _score_rsi(rsi: float, direction: str) -> SignalFactor:
    if direction == "BUY":
        if 45 <= rsi <= 68:
            return SignalFactor("RSI", 20, "RSI mendukung momentum buy tanpa terlihat terlalu jenuh.")
        if rsi > 72:
            return SignalFactor("RSI", 6, "RSI sudah tinggi, risiko pullback meningkat.")
        return SignalFactor("RSI", 12, "RSI belum optimal tetapi masih bisa diterima.")

    if direction == "SELL":
        if 32 <= rsi <= 55:
            return SignalFactor("RSI", 20, "RSI mendukung momentum sell tanpa terlihat terlalu jenuh.")
        if rsi < 28:
            return SignalFactor("RSI", 6, "RSI sudah rendah, risiko rebound meningkat.")
        return SignalFactor("RSI", 12, "RSI belum optimal tetapi masih bisa diterima.")

    if 40 <= rsi <= 60:
        return SignalFactor("RSI", 10, "RSI netral dan belum memberi tekanan kuat.")
    return SignalFactor("RSI", 6, "RSI berada di area ekstrem, tunggu konfirmasi tambahan.")


def _score_price_location(levels: MarketLevels, direction: str) -> SignalFactor:
    total_range = max(levels.resistance - levels.support, 0.0)
    if total_range <= 0:
        return SignalFactor("Lokasi Harga", 5, "Range support-resistance terlalu sempit untuk dinilai.")

    support_ratio = levels.distance_to_support / total_range
    resistance_ratio = levels.distance_to_resistance / total_range

    if direction == "BUY":
        if support_ratio <= 0.35:
            return SignalFactor("Lokasi Harga", 20, "Harga relatif dekat area support.")
        if resistance_ratio <= 0.25:
            return SignalFactor("Lokasi Harga", 8, "Harga sudah dekat resistance, ruang naik lebih terbatas.")
        return SignalFactor("Lokasi Harga", 14, "Harga berada di tengah range.")

    if direction == "SELL":
        if resistance_ratio <= 0.35:
            return SignalFactor("Lokasi Harga", 20, "Harga relatif dekat area resistance.")
        if support_ratio <= 0.25:
            return SignalFactor("Lokasi Harga", 8, "Harga sudah dekat support, ruang turun lebih terbatas.")
        return SignalFactor("Lokasi Harga", 14, "Harga berada di tengah range.")

    return SignalFactor("Lokasi Harga", 8, "Harga belum berada di area keputusan yang kuat.")


def _score_volatility(atr_percent: float) -> SignalFactor:
    if atr_percent <= 0:
        return SignalFactor("Volatilitas", 5, "ATR belum valid.")
    if atr_percent <= 2.5:
        return SignalFactor("Volatilitas", 15, "Volatilitas masih terkendali.")
    if atr_percent <= 5:
        return SignalFactor("Volatilitas", 10, "Volatilitas cukup tinggi, gunakan ukuran posisi lebih kecil.")
    return SignalFactor("Volatilitas", 5, "Volatilitas sangat tinggi, risiko whipsaw meningkat.")


def _score_risk_plan(risk_plan: RiskPlan) -> SignalFactor:
    if risk_plan.risk_reward is None:
        return SignalFactor("Risk Plan", 5, "Risk plan belum tersedia.")
    if risk_plan.risk_reward >= 2:
        return SignalFactor("Risk Plan", 15, "Risk-reward minimal 1:2 terpenuhi.")
    if risk_plan.risk_reward >= 1.5:
        return SignalFactor("Risk Plan", 10, "Risk-reward cukup, tetapi belum ideal.")
    return SignalFactor("Risk Plan", 5, "Risk-reward kurang menarik.")


def _confidence_label(confidence: int) -> str:
    if confidence >= 80:
        return "High Confidence"
    if confidence >= 60:
        return "Medium Confidence"
    if confidence >= 45:
        return "Low Confidence"
    return "No Trade"


def _build_summary(action: str, label: str, confidence: int) -> str:
    if action == "WAIT":
        return f"{label} ({confidence}%). Lebih aman menunggu konfirmasi sebelum entry."
    return f"{label} ({confidence}%). Skenario {action} valid jika price action mendukung."
