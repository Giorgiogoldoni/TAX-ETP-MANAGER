#!/usr/bin/env python3
"""Fetch a separate EUR-based history for the accumulating ETF verification basket."""
import json
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "observatory.json"
OUT = ROOT / "data" / "observatory_etf_history.json"
START = "2024-01-01"
END = (date.today() + timedelta(days=1)).isoformat()


def clean_close(frame):
    if frame is None or frame.empty or "Close" not in frame:
        return []
    rows = []
    for stamp, row in frame.dropna(subset=["Close"]).iterrows():
        value = float(row["Close"])
        if value > 0:
            rows.append({"date": stamp.strftime("%Y-%m-%d"), "close": value})
    return rows


def fx_history(symbol):
    frame = yf.Ticker(symbol).history(
        start=START, end=END, interval="1d",
        auto_adjust=False, actions=False
    )
    return {x["date"]: x["close"] for x in clean_close(frame)}


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    etfs = config.get("verification_etfs", [])
    try:\n        fx = {"USD": fx_history("EURUSD=X")}\n    except Exception as exc:\n        print(f"FX USD/EUR non disponibile: {str(exc)[:160]}")\n        fx = {"USD": {}}
    instruments, unresolved = {}, []

    for etf in etfs:
        key = etf["id"]
        quote_currency = etf.get("quote_currency", "EUR")
        selected, raw_prices, errors = None, [], []
        for symbol in etf.get("yahoo_symbols", []):
            try:
                frame = yf.Ticker(symbol).history(
                    start=START, end=END, interval="1d",
                    auto_adjust=False, actions=False
                )
                prices = clean_close(frame)
                if len(prices) >= 5:
                    selected, raw_prices = symbol, prices
                    break
                errors.append(f"{symbol}: meno di 5 prezzi validi")
            except Exception as exc:
                errors.append(f"{symbol}: {str(exc)[:160]}")

        if not selected:
            unresolved.append({"id": key, "ticker": etf.get("ticker"), "attempts": errors})
            continue

        converted, missing_fx = [], 0
        for point in raw_prices:
            close = point["close"]
            rate = None
            if quote_currency == "USD":
                rate = fx["USD"].get(point["date"])
                if rate is None:
                    prior = [d for d in fx["USD"] if d <= point["date"]]
                    rate = fx["USD"][prior[-1]] if prior else None
                if not rate or rate <= 0:
                    missing_fx += 1
                    continue
                close = close / rate
            converted.append({
                "date": point["date"],
                "close": round(close, 8),
                "quote_close": round(point["close"], 8),
                "quote_currency": quote_currency,
                **({"eurusd": round(rate, 8)} if rate else {})
            })

        if len(converted) < 5:
            unresolved.append({"id": key, "ticker": etf.get("ticker"),
                               "attempts": errors + ["serie insufficiente dopo conversione FX"]})
            continue

        instruments[key] = {
            "ticker": etf.get("ticker"),
            "isin": etf.get("isin"),
            "symbol": selected,
            "source": "Yahoo Finance",
            "price_currency": "EUR",
            "quote_currency": quote_currency,
            "fx_conversion": "USD / EURUSD giornaliero" if quote_currency == "USD" else "nessuna",
            "price_basis": "Close giornaliero; classe ad accumulazione",
            "prices": converted,
            "first_date": converted[0]["date"],
            "last_date": converted[-1]["date"],
            "fx_missing_rows": missing_fx
        }
        print(f"{key} {selected}: {len(converted)} chiusure EUR "
              f"({converted[0]['date']} — {converted[-1]['date']})")

    dates = [x["last_date"] for x in instruments.values()]
    payload = {
        "schema_version": 1,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": START,
        "latest_date": min(dates) if dates else None,
        "status": "ok" if instruments and not unresolved else ("partial" if instruments else "unavailable"),
        "instruments": instruments,
        "unresolved": unresolved,
        "method": "Close giornalieri delle classi Acc; prezzi in EUR. Le quotazioni USD sono convertite con EURUSD giornaliero."
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ETF verification history: {len(instruments)}/{len(etfs)} serie; "
          f"{len(unresolved)} non risolte; ultimo giorno comune {payload['latest_date']}")


if __name__ == "__main__":
    main()
