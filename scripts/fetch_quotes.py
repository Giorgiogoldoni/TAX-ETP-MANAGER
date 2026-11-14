#!/usr/bin/env python3
"""Fetch the latest available intraday quote for every instrument in history.json."""
import json
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "data" / "history.json"


def main():
    payload = json.loads(HISTORY.read_text(encoding="utf-8"))
    instruments = payload.get("instruments", {})
    quotes = {}
    unresolved = []

    for ticker, instrument in instruments.items():
        symbol = instrument.get("symbol")
        if not symbol:
            unresolved.append(ticker)
            continue
        try:
            frame = yf.Ticker(symbol).history(
                period="1d", interval="1m", auto_adjust=False,
                actions=False, prepost=False
            )
            if frame is None or frame.empty or "Close" not in frame:
                unresolved.append(ticker)
                continue
            valid = frame.dropna(subset=["Close"])
            if valid.empty:
                unresolved.append(ticker)
                continue
            stamp = valid.index[-1]
            row = valid.iloc[-1]
            price = float(row["Close"])
            if price <= 0:
                unresolved.append(ticker)
                continue
            quotes[ticker] = {
                "symbol": symbol,
                "price": round(price, 8),
                "currency": instrument.get("price_currency", "EUR"),
                "timestamp": stamp.isoformat(),
                "source": "Yahoo Finance intraday (1m)",
            }
        except Exception as exc:
            print(f"QUOTE ERROR {ticker} ({symbol}): {str(exc)[:180]}")
            unresolved.append(ticker)

    payload["latest_quotes"] = quotes
    payload["quotes_fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["quotes_status"] = "ok" if quotes and not unresolved else ("partial" if quotes else "unavailable")
    payload["quotes_unresolved"] = unresolved
    HISTORY.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Intraday quotes: {len(quotes)} updated; {len(unresolved)} unresolved.")
    for ticker, quote in quotes.items():
        print(f"{ticker}: {quote['price']} {quote['currency']} at {quote['timestamp']}")


if __name__ == "__main__":
    main()
