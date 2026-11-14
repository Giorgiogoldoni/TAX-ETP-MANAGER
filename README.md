# TAX & ETP MANAGER

Gestore autonomo per analisi fiscale e operativa di ETF, ETN, ETC e certificati per un investitore fiscalmente residente in Italia.

## Obiettivi

- Inventario degli strumenti con ISIN, emittente, forma giuridica e trattamento fiscale documentato.
- Distinzione tra redditi di capitale e redditi diversi.
- Monitoraggio di plusvalenze, minusvalenze e scadenze fiscali.
- Pianificazione delle vendite senza confondere rendimento economico e recupero fiscale.
- Analisi del portafoglio cedolare e degli strumenti in perdita (tra cui STHE e STHY, da censire con ISIN e documentazione aggiornata).

## Principi di progetto

1. **La classificazione fiscale non si deduce dal ticker o dal nome commerciale.** Si verifica tramite ISIN, prospetto, KID, documentazione dell'emittente e fonti fiscali ufficiali.
2. **ETF, ETN, ETC e certificati non sono categorie fiscalmente intercambiabili.** La forma giuridica e la documentazione del singolo strumento determinano il trattamento.
3. **Distribuzioni e risultati da cessione vanno registrati separatamente.** Non ogni provento o perdita è compensabile con ogni altra voce.
4. **Nessuna operazione viene suggerita solo per generare una minusvalenza.** Si valutano costi, rischio, liquidità, spread, orizzonte e coerenza con il portafoglio.
5. **Ogni classificazione deve avere fonte, data di verifica e livello di confidenza.** I casi non verificati restano "da verificare".

## Moduli previsti

- `data/`: portafoglio, strumenti e movimenti fiscali.
- `modules/`: motore di classificazione e analisi.
- `reports/`: report e controlli.
- `index.html`: dashboard web.
- `.github/workflows/`: controlli automatici e pubblicazione.

## Avvertenza

Il progetto è uno strumento di organizzazione e supporto all'analisi, non sostituisce il parere di un commercialista o di un intermediario fiscale. Le regole fiscali devono essere verificate sulle fonti ufficiali e aggiornate alla data dell'operazione. Non inserire credenziali, dati bancari o documenti fiscali personali nel repository pubblico.

## Avvio

Aprire `index.html` in un browser oppure pubblicare il repository con GitHub Pages dalle impostazioni del progetto.