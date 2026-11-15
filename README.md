# TAX & ETP MANAGER

Sistema autonomo di **gestione dinamica di mercato** per ETF, ETN, ETC e certificati, con modulo fiscale italiano separato.

## Priorità strategica

La priorità è la qualità delle decisioni di investimento: selezione, mantenimento, riduzione e sostituzione degli strumenti in base a trend, momentum, forza relativa e rischio. La fiscalità è un livello successivo di ottimizzazione del risultato netto; non deve alterare un segnale di mercato valido.

## Portafogli modello

La dashboard presenta tre portafogli autonomi. I Portafogli 1 e 2 sono mantenuti invariati; il Portafoglio 3 è una proposta basata sulle view dei gestori, con esposizione esplicita al Giappone. I pesi sono obiettivi teorici e non rappresentano posizioni reali. Il modello 3 è definito in `data/targets.json`; gli strumenti e gli ISIN sono registrati in `data/instruments.json`.

## Architettura

- `index.html`: dashboard operativa.
- `data/portfolio.json`: posizioni e prezzi di carico.
- `data/instruments.json`: anagrafica strumenti, ISIN e caratteristiche.
- `data/market_snapshot.json`: osservazioni di mercato importate o aggiornate.
- `data/strategy.json`: parametri e pesi del modello.
- `modules/market-engine.js`: calcolo trasparente dei segnali.
- `data/tax_ledger.json`: registro fiscale separato.

## Modello di mercato iniziale

Il modello è predisposto per integrare gli strumenti già utilizzati nel progetto dell'investitore:

- ROC 38 e medie mobili 38/200: momentum e filtro di regime.
- AO ed EMA: conferma della direzione.
- Forza relativa e breadth: selezione e ampiezza del mercato.
- Volatilità e drawdown: controllo del rischio.

Il motore non inventa dati: se un indicatore o un prezzo manca, il relativo contributo è marcato come non disponibile e il segnale resta incompleto. Pesi e soglie sono configurabili in `data/strategy.json`.

## Regole decisionali

1. Il segnale di mercato è calcolato senza usare la posizione fiscale.
2. Il punteggio è una sintesi informativa, non una previsione né un ordine automatico.
3. Un dato mancante non viene trattato come neutrale o positivo.
4. Nessuna operazione viene suggerita solo per generare una minusvalenza.
5. Prima di una vendita si valuta separatamente l'effetto fiscale, i costi, lo spread e la coerenza del reinvestimento.
6. Le classificazioni fiscali si verificano per ISIN, prospetto/KID, documentazione dell'emittente e fonti ufficiali.

## Aggiornamento dati

La dashboard legge file JSON versionati nel repository. In questa prima fase non esiste ancora un feed prezzi automatico: i dati devono essere importati o aggiornati da una fonte affidabile, indicando data, valuta e fonte. Non presentare mai la dashboard come quotazione in tempo reale.

## Prossimi sviluppi

1. Importazione del portafoglio reale e delle watchlist.
2. Collegamento ai dati storici e calcolo degli indicatori.
3. Backtest e calibrazione del modello senza overfitting.
4. Ranking dinamico e proposte di rotazione.
5. Simulatore fiscale delle operazioni candidate.

## Avvertenza

Strumento di supporto informativo, non consulenza finanziaria o fiscale personalizzata. Le regole fiscali vanno verificate con l'intermediario o un professionista. Non inserire credenziali, dati bancari o documenti personali nel repository pubblico.
