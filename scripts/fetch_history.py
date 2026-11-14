#!/usr/bin/env python3
"""Download daily closing prices from 2026-01-01 for portfolio instruments."""
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "data" / "portfolio.json"
OUT = ROOT / "data" / "history.json"
WATCHLIST = ROOT / "data" / "watchlist.json"
START = "2026-01-01"
END = (date.today() + timedelta(days=1)).isoformat()

# Prefer EUR trading lines. A candidate is accepted only when it returns
# a usable daily Close series; no prices are synthesized or interpolated.
CANDIDATES = {
    "DJLEV": ["DJLEV.MI", "DJLEV.PA"],
    "COPA": ["COPA.MI", "COPA.L"],
    "3BAL": ["3BAL.MI", "0LJI.DE", "3BAL.L"],
    "IWVL": ["IWVL.MI", "IWVL.L"],
    "IESZ": ["IESZ.MI", "IESZ.DE"],
    "IBZL": ["IBZL.MI", "IBZL.L"],
    "IMEU": ["IMEU.AS", "IMEU.MI", "IMEU.L"],
    "SPY4": ["SPY4.PA", "SPY4.MI", "SPY4.DE"],
    "LCFE": ["LCFE.MI", "LCFE.L"],
    "LCOC": ["LCOC.MI", "LCOC.L"],
    "BNK": ["BNK.MI", "BNK.PA"],
    "WSPX": ["WSPX.MI", "WSPX.DE"],
    "WS5X": ["WS5X.MI", "W5SX.MI", "W5SX.DE"],
    "WRTY": ["WRTY.MI", "WRTY.DE"],
    "WNAS": ["WNAS.MI", "WNAS.DE"],
    "WWRD": ["WWRD.MI", "WWRD.DE"],
    "IWMO": ["IWMO.MI", "IS3R.DE", "IWMO.L"],
    "4EML": ["4EML.MI", "4EML.L", "4EML.DE"],
    "LCCN": ["LCCN.MI", "LCCN.PA"],
    "HSTE": ["HSTE.MI", "HSTE.L"],
}

def clean_series(frame):
    if frame is None or frame.empty or "Close" not in frame:
        return []
    result = []
    for stamp, row in frame.dropna(subset=["Close"]).iterrows():
        close = float(row["Close"])
        if close <= 0:
            continue
        item = {"date": stamp.strftime("%Y-%m-%d"), "close": round(close, 8)}
        for key in ("Open", "High", "Low"):
            if key in row and row[key] is not None:
                item[key.lower()] = round(float(row[key]), 8)
        result.append(item)
    return result

def main():
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    watchlist = json.loads(WATCHLIST.read_text(encoding="utf-8")) if WATCHLIST.exists() else {"tickers": []}
    tickers = sorted({p.get("ticker") for p in portfolio.get("positions", []) if p.get("ticker")} | set(watchlist.get("tickers", [])))
    data, unresolved = {}, []
    for ticker in tickers:
        attempts = CANDIDATES.get(ticker, [ticker + ".MI"])
        selected, prices = None, []
        errors = []
        for symbol in attempts:
            try:
                frame = yf.Ticker(symbol).history(start=START, end=END, interval="1d",
                                                  auto_adjust=False, actions=False)
                series = clean_series(frame)
                if len(series) >= 5:
                    selected, prices = symbol, series
                    break
                errors.append(symbol + ": no usable observations")
            except Exception as exc:
                errors.append(symbol + ": " + str(exc)[:180])
        if selected:
            quote_currency = "EUR"
            conversion = "none"
            if ticker == "3BAL" and selected == "3BAL.L":
                # LSE quotes this same ISIN in GBX (pence), not EUR.
                # Convert each daily close to EUR using daily EUR/GBP.
                fx_frame = yf.Ticker("EURGBP=X").history(start=START, end=END,
                                                         interval="1d", auto_adjust=False)
                fx_prices = clean_series(fx_frame)
                fx_by_date = {x["date"]: x["close"] for x in fx_prices}
                fx_dates = sorted(fx_by_date)
                converted = []
                for item in prices:
                    rate = fx_by_date.get(item["date"])
                    if rate is None:
                        prior = [d for d in fx_dates if d <= item["date"]]
                        rate = fx_by_date[prior[-1]] if prior else None
                    if rate and rate > 0:
                        converted.append({
                            "date": item["date"],
                            "close": round((item["close"] / 100.0) / rate, 8),
                            "native_close": item["close"],
                            "native_currency": "GBX",
                            "eur_gbp": rate,
                            **{k: round((item[k] / 100.0) / rate, 8)
                               for k in ("open", "high", "low") if k in item},
                        })
                prices = converted
                quote_currency = "GBX"
                conversion = "GBX / 100 / daily EURGBP"
            if len(prices) >= 5:
                data[ticker] = {
                    "symbol": selected,
                    "source": "Yahoo Finance",
                    "price_basis": "unadjusted daily close",
                    "price_currency": "EUR",
                    "quote_currency": quote_currency,
                    "fx_conversion": conversion,
                    "prices": prices,
                    "first_date": prices[0]["date"],
                    "last_date": prices[-1]["date"],
                }
            else:
                unresolved.append({"ticker": ticker, "attempts": errors + ["insufficient FX data for EUR conversion"]})
        else:
            unresolved.append({"ticker": ticker, "attempts": errors})

    # Broad market risk gauges: implied volatility indices, not portfolio instruments.
    market_indices = {}
    market_symbols = {"VIX": "^VIX", "VSTOXX": "^V2TX"}
    for name, symbol in market_symbols.items():
        try:
            frame = yf.Ticker(symbol).history(start=START, end=END, interval="1d",
                                              auto_adjust=False, actions=False)
            series = clean_series(frame)
            if series:
                market_indices[name] = {
                    "symbol": symbol,
                    "name": "CBOE Volatility Index" if name == "VIX" else "EURO STOXX 50 Volatility (VSTOXX)",
                    "source": "Yahoo Finance",
                    "unit": "index points",
                    "prices": series,
                    "first_date": series[0]["date"],
                    "last_date": series[-1]["date"],
                }
            else:
                print(f"MARKET INDEX UNRESOLVED {name}: {symbol}")
        except Exception as exc:
            print(f"MARKET INDEX ERROR {name}: {str(exc)[:180]}")

    all_dates = [v["last_date"] for v in data.values()] + [v["last_date"] for v in market_indices.values()]
    payload = {
        "schema_version": 1,
        "period_start": START,
        "period_end_exclusive": END,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest_date": max(all_dates) if all_dates else None,
        "source": "Yahoo Finance chart history",
        "status": "ok" if data and not unresolved else ("partial" if data else "unavailable"),
        "message": (f"Scaricate {len(data)} serie; {len(unresolved)} simboli non risolti."
                    if unresolved else f"Scaricate {len(data)} serie storiche."),
        "instruments": data,
        "market_indices": market_indices,
        "unresolved": unresolved,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(payload["message"])
    for ticker, item in data.items():
        print(f"{ticker}: {item['symbol']} {len(item['prices'])} daily closes "
              f"({item['first_date']} — {item['last_date']})")
    for item in unresolved:
        print(f"UNRESOLVED {item['ticker']}: {'; '.join(item['attempts'])}")

if __name__ == "__main__":
    main()
