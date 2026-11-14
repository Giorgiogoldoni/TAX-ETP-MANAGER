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
START = "2026-01-01"
END = (date.today() + timedelta(days=1)).isoformat()

# Prefer EUR trading lines. A candidate is accepted only when it returns
# a usable daily Close series; no prices are synthesized or interpolated.
CANDIDATES = {
    "DJLEV": ["DJLEV.MI", "DJLEV.PA"],
    "COPA": ["COPA.MI", "COPA.L"],
    "3BAL": ["3BAL.MI", "3BAL.L"],
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
}

def clean_series(frame):
    if frame is None or frame.empty or "Close" not in frame:
        return []
    close = frame["Close"]
    # yfinance may return a one-column DataFrame for some versions.
    if hasattr(close, "columns"):
        if len(close.columns) != 1:
            return []
        close = close.iloc[:, 0]
    result = []
    for stamp, value in close.dropna().items():
        price = float(value)
        if price <= 0:
            continue
        result.append({"date": stamp.strftime("%Y-%m-%d"), "close": round(price, 8)})
    return result

def main():
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    tickers = sorted({p.get("ticker") for p in portfolio.get("positions", []) if p.get("ticker")})
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
            data[ticker] = {
                "symbol": selected,
                "source": "Yahoo Finance",
                "price_basis": "unadjusted daily close",
                "price_currency": "EUR (EUR trading line selected by exchange suffix)",
                "prices": prices,
                "first_date": prices[0]["date"],
                "last_date": prices[-1]["date"],
            }
        else:
            unresolved.append({"ticker": ticker, "attempts": errors})

    all_dates = [v["last_date"] for v in data.values()]
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
