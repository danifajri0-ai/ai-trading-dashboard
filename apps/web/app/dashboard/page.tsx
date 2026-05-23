import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { IndicatorPanel } from "@/components/IndicatorPanel";
import { MarketContextPanel } from "@/components/MarketContextPanel";
import { MarketHeader } from "@/components/MarketHeader";
import { RiskPlanCard } from "@/components/RiskPlanCard";
import { SentimentPanel } from "@/components/SentimentPanel";
import { SetupStrategyCard } from "@/components/SetupStrategyCard";
import { SignalCard } from "@/components/SignalCard";
import { getAnalysis } from "@/lib/api";

export default async function DashboardPage() {
  const analysis = await getAnalysis("BTCUSD", "H1");
  const explanation = (analysis.signal_explanation_lite as { explanation_summary?: string } | null)?.explanation_summary;

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
        <ConfidenceMeter confidence={analysis.confidence} qualityScore={analysis.trade_quality_score} />
        <IndicatorPanel
          trend={analysis.technical_summary?.trend}
          emaFast={analysis.technical_summary?.ema_fast}
          emaSlow={analysis.technical_summary?.ema_slow}
          rsi={analysis.technical_summary?.rsi}
          atr={analysis.technical_summary?.atr}
          support={analysis.technical_summary?.support}
          resistance={analysis.technical_summary?.resistance}
        />
      </div>
      <div className="grid grid-2">
        <SentimentPanel
          label={analysis.sentiment_summary?.sentiment_label}
          score={analysis.sentiment_summary?.sentiment_score}
          source={analysis.sentiment_summary?.source}
          context={analysis.sentiment_summary?.context}
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
      <div className="grid grid-2">
        <MarketContextPanel context={analysis.market_context_lite} />
        <SetupStrategyCard
          signal={analysis.signal}
          explanation={explanation}
          reasons={analysis.reasons}
          warnings={analysis.warnings}
        />
      </div>
    </main>
  );
}
