from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketContextItem:
    title: str
    detail: str


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


def _asset_specific_note(pair_label: str) -> str:
    if pair_label in {"BTC/USD", "ETH/USD"}:
        return "Crypto sensitif terhadap risk appetite, likuidasi leverage, arus ETF, dan pergerakan USD."
    if pair_label == "XAU/USD":
        return "Gold sensitif terhadap USD, yield obligasi, ekspektasi suku bunga, dan risk-off global."
    if pair_label in {"EUR/USD", "GBP/USD"}:
        return "Pair mayor Eropa sensitif terhadap data inflasi, bank sentral, dan kekuatan dolar AS."
    if pair_label == "USD/JPY":
        return "USD/JPY sensitif terhadap yield AS, kebijakan BoJ, dan intervensi verbal Jepang."
    return "Gunakan konfirmasi berita dan likuiditas sebelum entry."
