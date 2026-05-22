# Deep Research Implementation Notes

Tujuan dokumen ini adalah menjadi acuan development ringkas dari
`docs/research/institutional_trading_engine_research.md`.

Catatan penting:

- Dokumen riset panjang tidak boleh dimuat ke backend runtime.
- Tahap awal tidak mengubah endpoint, UI, atau logic lama.
- Semua field baru yang nanti dibutuhkan sebaiknya optional dan backward-compatible.
- Prioritas awal adalah bar-based, lightweight, deterministic, dan mudah dites.

## Ringkasan Teknis

Target pengembangan adalah lightweight institutional trading layer, bukan menambah indikator retail biasa. Layer ini sebaiknya menghasilkan metadata keputusan yang menjelaskan:

- kondisi rezim market,
- kondisi volatilitas,
- kontribusi komponen sinyal,
- risiko berbasis ATR,
- gate risiko sebelum sinyal dipakai.

Untuk tahap awal, layer ini harus diperlakukan sebagai diagnostic layer. Jangan langsung mengganti `signal`, `confidence`, `risk_level`, atau endpoint lama.

## Model Yang Relevan

| Model | Kegunaan | Status implementasi yang disarankan |
|---|---|---|
| Market regime lite | Klasifikasi trend, range, volatile, transitional dari data OHLCV | Safe for now |
| Volatility regime | Klasifikasi calm, normal, high-vol dari ATR% atau realized volatility | Safe for now |
| Robust z-score | Standardisasi fitur agar indikator berbeda bisa dibandingkan | Safe for now |
| Signal contribution | Menjelaskan bobot kontribusi trend, momentum, volatility, risk plan | Safe for now |
| ATR risk sizing | Estimasi jarak stop, risk unit, dan risk-reward berbasis ATR | Safe for now |
| Risk gate | PASS, CAUTION, BLOCK berdasarkan volatility, RR, data quality, signal confidence | Safe for now |
| Time-series momentum | Momentum multi-horizon yang distandardisasi volatilitas | Later / Research Lab |
| Anchored VWAP / structure | AVWAP, swing levels, break of structure, distance-to-VWAP | Later / Research Lab |
| Dynamic covariance / shrinkage | Estimasi risiko portfolio lintas aset | Later / Research Lab |
| Risk parity / vol targeting | Alokasi portfolio berbasis kontribusi risiko | Later / Research Lab |
| CVaR / Expected Shortfall | Tail-risk metric dan stress testing | Later / Research Lab |
| Sentiment / event surprise | Event resmi, surprise makro, sentiment berbobot sumber | Later / Research Lab |
| HMM / Markov-switching regime | Probabilistic state engine | Not recommended for live dashboard yet |
| DCC-GARCH | Dynamic volatility/correlation model | Not recommended for live dashboard yet |
| Black-Litterman | Bayesian portfolio construction | Not recommended for live dashboard yet |
| Microstructure / OFI | Order-flow imbalance, depth, spread, impact | Not recommended for live dashboard yet |
| Execution algos | VWAP, POV, implementation shortfall, Almgren-Chriss | Not recommended for live dashboard yet |
| Full validation lab | CSCV/PBO, DSR, SPA, White Reality Check, bootstrap | Not recommended for live dashboard yet |

## Formula Penting

### Robust z-score

Gunakan untuk membuat fitur lebih tahan outlier.

```text
z_k,t = clip((x_k,t - median_window(x_k)) / MAD_window(x_k), -3, 3)
```

Fallback wajib:

- Jika `MAD == 0`, gunakan fallback denominator kecil atau kembalikan `0`.
- Jika data kurang panjang, gunakan window tersedia dan beri flag `low_sample`.

### Market regime probability target

Untuk versi riset penuh:

```text
pi_t = P(s_t | x_1:t)
```

Untuk tahap awal, jangan gunakan HMM dulu. Gunakan regime lite berbasis rule:

```text
if high_vol:
    regime = "VOLATILE"
elif trend_aligned:
    regime = "TRENDING"
elif low_vol_or_mixed:
    regime = "RANGING"
else:
    regime = "TRANSITIONAL"
```

### Time-series momentum

```text
s_i,t = sum(alpha_h * return_i,t-h:t-1 / sigma_i,t)
```

Tahap awal cukup ambil proxy ringan dari EMA alignment, MACD histogram, atau return rolling pendek.

### Signal contribution

```text
score_total = sum(component_score)
contribution_pct_i = component_score_i / max(abs(score_total), epsilon)
```

Komponen awal yang aman:

- trend,
- RSI/momentum,
- MACD,
- price location,
- volatility,
- risk plan.

### Regime-gated score

Untuk versi matang:

```text
alpha_t = sum(pi_r,t * (W_r' * z_t))
FinalScore_t = 100 * tanh(alpha_t) * LiquidityGate_t * RiskGate_t
```

Tahap awal jangan mengganti final signal lama. Simpan output ini sebagai optional diagnostic field saja.

### ATR risk sizing

```text
Units_ATR = (Equity * risk_per_trade) / (k * ATR_t * point_value)
```

Untuk dashboard awal, cukup output:

- `atr`,
- `atr_percent`,
- `stop_distance_atr`,
- `risk_reward`,
- `risk_unit_label`,
- `risk_gate`.

### Kelly dan fractional Kelly

```text
f* = (b * p - q) / b
f* ~= mu / sigma^2
```

Jangan pakai untuk live dashboard tahap awal. Kelly sensitif terhadap estimation error dan butuh validasi statistik.

### Risk contribution

```text
RC_i = w_i * (Sigma * w)_i / sqrt(w' * Sigma * w)
```

Tunda sampai ada portfolio model dan covariance yang benar.

### Expected Shortfall / CVaR

```text
ES_alpha(L) = E[L | L >= VaR_alpha]
```

Tunda sampai ada scenario returns dan backtest/stress engine.

## Input Data Yang Dibutuhkan

### Safe for now

- OHLCV normalized.
- Timestamp yang sudah disortir.
- Existing indicators: EMA, MA, RSI, MACD, ATR.
- Existing trend analysis.
- Existing risk plan.
- Existing signal summary.
- Existing risk level.

### Later / Research Lab

- Return multi-horizon.
- Realized volatility multi-window.
- Rolling correlation lintas aset.
- Anchored VWAP dan volume profile.
- Funding, basis, open interest untuk crypto.
- COT positioning untuk futures/FX proxy.
- Macro/event calendar dengan timestamp resmi.
- Point-in-time data storage.
- Transaction cost dan slippage estimate.

### Not recommended for live dashboard yet

- L2/L3 order book.
- Tick reconstruction.
- Broker/exchange execution feed.
- Full portfolio holdings dan margin model.
- Vendor consensus estimates.
- NLP sentiment model inference.
- Revised/vintage macro database tanpa PIT controls.

## Output Yang Bisa Dipakai Dashboard

Tahap awal sebaiknya output optional, misalnya sebagai nested metadata:

```text
institutional_summary:
  market_regime_lite:
    label
    confidence
    reasons
  volatility_regime:
    label
    atr_percent
    realized_vol_proxy
  robust_z_score:
    trend_z
    momentum_z
    volatility_z
  signal_contribution:
    components
    total_score
  atr_risk:
    atr
    atr_percent
    stop_distance
    risk_reward
  risk_gate:
    status
    reasons
```

Dashboard tidak perlu berubah pada fase awal. Field ini bisa disimpan sebagai payload tambahan untuk fase UI berikutnya.

## Klasifikasi Fitur

### 1. Safe for now

Fitur yang bisa dibangun ringan, deterministic, tanpa dependency baru, dan tanpa mengubah behavior lama:

- `market_regime_lite`
  - Input: trend direction, EMA alignment, ATR%.
  - Output: `TRENDING`, `RANGING`, `VOLATILE`, `TRANSITIONAL`, `UNKNOWN`.

- `volatility_regime`
  - Input: ATR%, rolling return volatility jika tersedia.
  - Output: `Calm`, `Normal`, `High Volatility`, `Unknown`.

- `robust_z_score`
  - Input: close returns, RSI, MACD histogram, ATR%.
  - Output: clipped z-score per fitur.

- `signal_contribution`
  - Input: existing signal factors atau existing components.
  - Output: daftar kontribusi komponen yang menjelaskan confidence.

- `ATR risk`
  - Input: ATR, entry, stop loss, take profit, risk reward.
  - Output: risk distance, stop distance in ATR, risk note.

- `risk_gate`
  - Input: confidence, risk level, ATR%, RR, data availability.
  - Output: `PASS`, `CAUTION`, `BLOCK`.

Aturan tahap awal:

- Jangan override signal lama.
- Jangan menurunkan confidence lama.
- Jangan mengubah endpoint lama.
- Jangan tampilkan UI baru dulu.
- Gunakan optional field jika nanti di-wire ke response.

### 2. Later / Research Lab

Fitur yang berguna tetapi perlu data/model/test lebih matang:

- Time-series momentum multi-horizon.
- Anchored VWAP.
- Swing high/low berbasis n-bar.
- Break of structure dengan ATR buffer.
- Distance-to-VWAP z-score.
- Basic transaction cost estimate.
- Slippage proxy dari spread/volume jika data tersedia.
- Cross-asset factor scoring.
- Vol targeting.
- Risk parity ringan.
- CVaR approximation berbasis historical returns.
- Event/sentiment berbasis sumber resmi.
- Walk-forward backtest.
- Stationary bootstrap sederhana.
- Deflated Sharpe / PBO reporting.

Aturan:

- Jalankan sebagai research module atau offline lab dulu.
- Jangan dipakai live decision sebelum ada validation report.
- Simpan parameter dan threshold secara eksplisit.

### 3. Not recommended for live dashboard yet

Fitur berat yang rawan salah jika dipasang langsung:

- HMM / Markov-switching live regime engine.
- DCC-GARCH dynamic covariance.
- Black-Litterman optimizer.
- Full ES/CVaR optimizer.
- Kelly sizing untuk live position.
- Microstructure OFI dari L2/L3.
- Order book reconstruction.
- VWAP/POV/IS execution engine.
- Live slippage model.
- NLP sentiment model inference.
- Auto-learning harian.
- Model yang mengubah parameter sendiri tanpa research cycle.

Alasan utama:

- Membutuhkan data point-in-time.
- Membutuhkan validasi statistik.
- Rawan look-ahead bias.
- Rawan overfitting.
- Bisa memberi rasa aman palsu di dashboard.
- Butuh observability dan kill-switch sebelum live.

## Risiko Implementasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Look-ahead bias | Sinyal terlihat bagus tetapi tidak bisa direplikasi live | Pastikan hanya memakai candle yang sudah tersedia saat analisis |
| Data revision leakage | Macro/fundamental/event memakai data revisi masa depan | Tunda fitur event/macro sampai ada PIT storage |
| Overfitting threshold | Gate terlihat presisi tapi rapuh | Threshold awal sederhana dan mudah diaudit |
| Feature duplication | Layer baru hanya mengulang indikator lama dengan nama baru | Output harus berupa context, contribution, dan gate, bukan indikator tambahan |
| Runtime bloat | Backend membawa riset panjang atau logic berat | Riset tetap di docs; runtime hanya fungsi kecil |
| Contract breakage | Frontend/API client gagal parse payload | Tambahkan field optional saja |
| False precision | Dashboard menampilkan probabilitas seolah model sudah HMM | Pakai label `lite` dan reasons eksplisit |
| Data pendek | MAD/volatility/ATR tidak stabil | Fallback aman dan flag `low_sample` |
| Signal override terlalu dini | Behavior lama berubah tanpa validasi | Institutional layer tahap awal hanya diagnostic |
| Dependency creep | Instal library berat untuk fitur yang belum matang | Tidak ada dependency baru di tahap awal |

## Prioritas Implementasi

### P0: Dokumentasi dan kontrak desain

- Simpan ringkasan teknikal ini sebagai acuan development.
- Model registry tahap awal sudah dibuat di `research/model_registry.yaml` sebagai artefak research-only, belum terhubung ke runtime app.
- Tentukan payload optional yang tidak mengubah response lama.
- Jangan implement runtime dulu.

### P1: Domain helper ringan

- Buat pure domain module untuk:
  - robust z-score,
  - volatility regime,
  - market regime lite,
  - signal contribution,
  - ATR risk,
  - risk gate.
- Semua fungsi harus deterministic dan unit-testable.
- Tidak boleh import Streamlit/FastAPI.

### P2: Optional DTO

- Tambahkan optional nested dataclass untuk institutional summary.
- Parser HTTP harus menerima payload lama tanpa field baru.
- Existing fields tetap sama.

### P3: Service wiring diagnostic only

- Wire layer baru di analysis service setelah logic lama selesai.
- Jika calculation gagal, fallback ke `None` atau safe unknown summary.
- Jangan ubah `signal`, `confidence`, `risk_level`, atau endpoint.

### P4: UI phase berikutnya

- Setelah payload stabil, baru rancang panel UI.
- Panel awal yang masuk akal:
  - regime lite,
  - volatility regime,
  - signal contribution,
  - ATR risk,
  - risk gate.
- Jangan tampilkan fitur probabilistic berat sebelum modelnya benar-benar ada.

## Development Guardrails

- Backend runtime tidak membaca dokumen riset panjang.
- Tidak ada dependency baru.
- Tidak ada refactor besar.
- Tidak ada penghapusan logic lama.
- Tidak ada perubahan endpoint lama.
- Tidak ada perubahan UI pada tahap dokumentasi ini.
- Semua tambahan runtime di fase berikutnya harus optional dan backward-compatible.
- Semua fungsi baru harus punya test untuk data normal, data pendek, dan data kosong.

## Kesimpulan

Tahap awal yang paling aman adalah membangun institutional layer sebagai metadata kecil di sekitar logic yang sudah ada. Fokusnya bukan mengganti mesin sinyal, tetapi menambahkan konteks keputusan: regime lite, volatility, contribution, ATR risk, dan risk gate. Fitur berat seperti HMM, DCC-GARCH, Black-Litterman, CVaR optimizer, microstructure, execution algo, dan NLP event engine harus tetap di Research Lab sampai data, validasi, dan observability siap.
