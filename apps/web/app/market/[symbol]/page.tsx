import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { IndicatorPanel } from "@/components/IndicatorPanel";
import { MarketHeader } from "@/components/MarketHeader";
import { RiskPlanCard } from "@/components/RiskPlanCard";
import { SignalCard } from "@/components/SignalCard";
import { getAnalysis } from "@/lib/api";

type MarketPageProps = {
  params: {
    symbol: string;
  };
};

export default async function MarketSymbolPage({ params }: MarketPageProps) {
  const symbol = params.symbol?.toUpperCase() || "BTCUSD";
  const analysis = await getAnalysis(symbol, "H1");

  return (
    <main className="grid" style={{ gap: 14 }}>
      <MarketHeader symbol={analysis.symbol} timeframe={analysis.timeframe} source={process.env.NEXT_PUBLIC_API_BASE_URL || "fallback"} />
      <SignalCard
        signal={analysis.signal}
        bias={analysis.bias}
        confidence={analysis.confidence}
        riskLevel={analysis.risk_level}
      />
      <div className="grid grid-2">
        <IndicatorPanel
          trend={analysis.technical_summary?.trend}
          emaFast={analysis.technical_summary?.ema_fast}
          emaSlow={analysis.technical_summary?.ema_slow}
          rsi={analysis.technical_summary?.rsi}
          atr={analysis.technical_summary?.atr}
          support={analysis.technical_summary?.support}
          resistance={analysis.technical_summary?.resistance}
        />
        <RiskPlanCard
          riskLevel={analysis.risk_summary?.risk_level}
          entryArea={analysis.risk_summary?.entry_area}
          stopLoss={analysis.risk_summary?.stop_loss}
          takeProfit={analysis.risk_summary?.take_profit}
          riskReward={analysis.risk_summary?.risk_reward}
          maxRiskPct={analysis.risk_summary?.max_risk_pct}
          notes={analysis.risk_summary?.notes}
        />
      </div>
      <ConfidenceMeter confidence={analysis.confidence} qualityScore={analysis.trade_quality_score} />
    </main>
  );
}
