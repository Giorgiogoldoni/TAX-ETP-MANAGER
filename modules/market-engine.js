/**
 * Motore trasparente dei segnali di mercato.
 * I campi mancanti restano mancanti: non vengono trasformati in zero.
 */
export function evaluateInstrument(item, config = {}) {
  const p = config.parameters || {};
  const w = p.weights || { trend:30, momentum:25, ao_ema:15, relative_strength:20, breadth:10 };
  const t = p.thresholds || { strong:70, positive:55, neutral:45, weak:30 };
  const parts = [];
  const add = (name, value, weight, detail) => {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return;
    parts.push({ name, value: Math.max(0, Math.min(100, value)), weight, detail });
  };

  // Trend: prezzo sopra entrambe le medie = forte; sotto entrambe = debole.
  if (Number.isFinite(item.price) && Number.isFinite(item.ma38) && Number.isFinite(item.ma200)) {
    let score = item.price > item.ma38 && item.ma38 > item.ma200 ? 100 :
      item.price > item.ma200 ? 65 : item.price < item.ma38 && item.price < item.ma200 ? 0 : 35;
    add("Trend MA38/MA200", score, w.trend, score >= 65 ? "Trend favorevole" : "Trend da monitorare");
  }
  if (Number.isFinite(item.roc38)) {
    const score = Math.max(0, Math.min(100, 50 + item.roc38 * 2));
    add("Momentum ROC38", score, w.momentum, item.roc38.toFixed(2) + "%");
  }
  if (Number.isFinite(item.ao) && Number.isFinite(item.price) && Number.isFinite(item.ema20)) {
    const bullish = item.ao > 0 && item.price > item.ema20;
    const bearish = item.ao < 0 && item.price < item.ema20;
    add("AO + EMA20", bullish ? 100 : bearish ? 0 : 50, w.ao_ema, bullish ? "Conferma positiva" : bearish ? "Conferma negativa" : "Segnali misti");
  }
  if (Number.isFinite(item.relative_strength)) {
    add("Forza relativa", Math.max(0, Math.min(100, 50 + item.relative_strength * 5)), w.relative_strength, item.relative_strength.toFixed(2));
  }
  if (Number.isFinite(item.breadth)) {
    add("Breadth", Math.max(0, Math.min(100, item.breadth)), w.breadth, item.breadth.toFixed(1) + "/100");
  }

  const totalWeight = parts.reduce((s, x) => s + x.weight, 0);
  const score = totalWeight ? parts.reduce((s, x) => s + x.value * x.weight, 0) / totalWeight : null;
  const riskFlags = [];
  if (p.risk_flags?.below_ma200 && Number.isFinite(item.price) && Number.isFinite(item.ma200) && item.price < item.ma200) riskFlags.push("Prezzo sotto MA200");
  if (p.risk_flags?.negative_roc && Number.isFinite(item.roc38) && item.roc38 < 0) riskFlags.push("ROC38 negativo");
  if (p.risk_flags?.high_volatility && Number.isFinite(item.volatility_annualized) && item.volatility_annualized > 35) riskFlags.push("Volatilità annualizzata elevata");
  if (Number.isFinite(item.drawdown) && item.drawdown <= -20) riskFlags.push("Drawdown almeno -20%");

  let label = "Dati insufficienti";
  if (score !== null) label = score >= t.strong ? "Forte" : score >= t.positive ? "Positivo" : score >= t.neutral ? "Neutrale" : score >= t.weak ? "Debole" : "Molto debole";
  return { ticker: item.ticker || "—", score, label, coverage: parts.length, components: parts, riskFlags };
}

export function evaluateSnapshot(snapshot, config) {
  return (snapshot.instruments || []).map(item => ({ ...item, signal: evaluateInstrument(item, config) }))
    .sort((a,b) => (b.signal.score ?? -1) - (a.signal.score ?? -1));
}
