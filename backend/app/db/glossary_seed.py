"""Fachbegriffe für Aktien, UCITS, Obligationen und den Schweizer Privathandel."""

GLOSSARY_SEED: list[dict] = [
    {
        "term": "Aktie",
        "slug": "aktie",
        "short_definition": "Anteilschein an einem Unternehmen. Du wirst Miteigentümerin oder Miteigentümer.",
        "long_explanation": (
            "Mit einer Aktie kaufst du einen Bruchteil der Firma, nicht nur eine Wette auf den Kurs. "
            "Du trägst das unternehmerische Risiko: Gewinn, Verlust, im Extremfall Totalausfall. "
            "Rechte hängen von der Aktiengattung ab — oft Stimmrecht an der GV und Anspruch auf Dividende, "
            "wenn der Verwaltungsrat eine Ausschüttung vorschlägt.\n\n"
            "In der Schweiz handelst du Titel an der SIX (z. B. NESN.SW) oder ausländische Aktien über deinen Broker. "
            "US-Einzelaktien sind für Privatkunden in der Regel kaufbar; es fallen Courtage, oft Stempelabgabe "
            "und bei US-Dividenden Quellensteuer an. Der Kurs allein sagt nichts über Qualität — "
            "Gewinn, Verschuldung und Bewertung gehören dazu."
        ),
        "related_terms": ["Dividende", "ISIN", "Market Cap", "Stempelabgabe"],
        "chart_hint": None,
    },
    {
        "term": "ETF",
        "slug": "etf",
        "short_definition": "Exchange Traded Fund — Fonds, der wie eine Aktie an der Börse gehandelt wird.",
        "long_explanation": (
            "Ein ETF bündelt viele Titel (Aktien, Anleihen, Rohstoffe) und bildet meist einen Index nach. "
            "Du kaufst und verkaufst ihn während der Börsenzeiten zum aktuellen Marktpreis, nicht nur einmal täglich "
            "wie bei klassischen Fonds. Die laufenden Kosten (TER) sind oft niedrig.\n\n"
            "Für dich in der Schweiz zählen vor allem UCITS-ETFs mit Basisinformationsblatt (KID). "
            "US-ETFs wie VOO oder GLD haben häufig kein PRIIPs-KID — viele Retail-Broker lehnen sie ab. "
            "Pendants sind z. B. VWCE.DE (Welt), SXR8.DE (S&P 500) oder CSSMI.SW (SMI). "
            "Achte auf Währung, Ausschüttung vs. Thesaurierung und ob der ETF physisch oder synthetisch repliziert."
        ),
        "related_terms": ["UCITS", "PRIIPs-KID", "TER", "Index", "Thesaurierend"],
        "chart_hint": None,
    },
    {
        "term": "UCITS",
        "slug": "ucits",
        "short_definition": "EU-Fondsstandard (Undertakings for Collective Investment in Transferable Securities).",
        "long_explanation": (
            "UCITS ist ein Regelwerk aus der EU für Publikumsfonds und ETFs: Streuung, Transparenz, Verwahrung, "
            "Liquidität. Viele in Irland oder Luxemburg aufgelegte ETFs tragen das Label UCITS und dürfen "
            "im EWR und typischerweise auch an Schweizer Privatkunden vertrieben werden — sofern ein KID vorliegt.\n\n"
            "Praktisch: Siehst du im Namen «UCITS ETF» und eine europäische Börse (.DE, .L, .SW, .MI), "
            "ist das meist das Produkt, das dein Broker dir verkaufen darf. Das Gegenteil sind US-domizilierte "
            "ETFs und Mutual Funds ohne KID. UCITS schützt nicht vor Kursverlust — nur vor bestimmten "
            "strukturellen Risiken eines unregulierten Vehikels."
        ),
        "related_terms": ["ETF", "PRIIPs-KID", "Fonds", "ISIN"],
        "chart_hint": None,
    },
    {
        "term": "PRIIPs-KID",
        "slug": "priips-kid",
        "short_definition": "Basisinformationsblatt für verpackte Anlageprodukte — Pflichtlektüre vor dem Kauf.",
        "long_explanation": (
            "PRIIPs sind «verpackte» Retail-Produkte: ETFs, Fonds, strukturierte Produkte. Das KID "
            "(Key Information Document) fasst Ziel, Kosten, Risiken und Performance-Szenarien auf wenigen Seiten zusammen. "
            "Ohne KID dürfen viele Schweizer und EU-Broker das Produkt Privatkunden nicht anbieten.\n\n"
            "Deshalb fehlen VOO, TLT oder VTSAX oft im Orderbuch, während VWCE oder IDTL.L erscheinen. "
            "Das KID ist kein Kaufsignal und keine Garantie. Es hilft, TER, Risikoklasse und empfohlene "
            "Haltedauer zu vergleichen, bevor du den Titel auf die Watchlist oder ins Depot nimmst."
        ),
        "related_terms": ["UCITS", "ETF", "TER", "Fonds"],
        "chart_hint": None,
    },
    {
        "term": "Fonds",
        "slug": "fonds",
        "short_definition": "Sondervermögen, das viele Anleger gemeinsam in Titel investiert — aktiv oder passiv.",
        "long_explanation": (
            "Ein Fonds sammelt Geld und kauft damit Wertpapiere. Aktiv bedeutet: ein Team wählt Titel aus "
            "und verlangt dafür oft höhere Gebühren. Passiv bedeutet: der Fonds folgt einem Index (häufig als ETF).\n\n"
            "US-Mutual-Funds wie VTSAX sind für Schweizer Privatkunden in der Regel nicht erhältlich. "
            "Das übliche Pendant ist ein UCITS-ETF, z. B. ein All-World-ETF statt eines US-Indexfonds. "
            "Klassische CH/LU-Fonds mit Valor gibt es weiter bei Banken — sie werden seltener über Yahoo-Ticker "
            "geführt. Wichtig bleibt: Kosten, Domizil, Ausschüttung und ob du das Produkt bei deinem Broker "
            "überhaupt ordern kannst."
        ),
        "related_terms": ["ETF", "UCITS", "TER", "Thesaurierend"],
        "chart_hint": None,
    },
    {
        "term": "Obligation",
        "slug": "obligation",
        "short_definition": "Anleihe: Du leihst einem Staat oder Unternehmen Geld und erhältst Zins plus Rückzahlung.",
        "long_explanation": (
            "Eine Obligation (Anleihe) ist ein Kredit. Der Emittent zahlt periodisch einen Coupon und am Ende "
            "den Nennwert zurück — sofern er zahlungsfähig bleibt. Steigen die Marktzinsen, fällt der Kurs "
            "bestehender Anleihen meist; sinken die Zinsen, steigt er. Laufzeit und Kreditqualität bestimmen "
            "das Risiko.\n\n"
            "Einzelanleihen (Kantone, Eidgenossenschaft, Konzerne) sind oft unhandlich und schlecht über Yahoo "
            "abgedeckt. Für die Watchlist eignen sich Bond-ETFs mit UCITS-Hülle, z. B. lange US-Treasuries "
            "über IDTL.L statt TLT. Du kaufst dann einen Korb von Anleihen, nicht eine einzelne Serie. "
            "Währungsrisiko (USD vs. CHF) bleibt bestehen, wenn der ETF nicht abgesichert ist."
        ),
        "related_terms": ["ETF", "UCITS", "Volatilität", "Duration"],
        "chart_hint": None,
    },
    {
        "term": "Duration",
        "slug": "duration",
        "short_definition": "Zinssensitivität einer Anleihe: Wie stark der Kurs auf Zinsänderungen reagiert.",
        "long_explanation": (
            "Die Duration (oft Macaulay- oder Modified Duration) misst, wie empfindlich der Anleihekurs "
            "auf eine Zinsänderung ist. Grobe Faustregel: Duration 10 bedeutet, 1 Prozentpunkt höherer Zins "
            "drückt den Kurs um etwa 10 Prozent — und umgekehrt.\n\n"
            "Lange Staatsanleihen (20+ Jahre, TLT bzw. IDTL.L) haben hohe Duration und schwanken deshalb "
            "fast wie Aktien, obwohl sie «sicher» wirken. Kurze Papiere (2 Jahre) sind ruhiger, bringen "
            "bei fallenden Zinsen aber weniger Kursgewinn. Für Signale in dieser App gilt: RSI und MACD "
            "an Bond-ETFs beschreiben Momentum, ersetzen aber keine Zinsanalyse."
        ),
        "related_terms": ["Obligation", "Volatilität", "ETF"],
        "chart_hint": None,
    },
    {
        "term": "Rohstoff",
        "slug": "rohstoff",
        "short_definition": "Physisches Gut wie Gold, Öl oder Weizen — handelbar über ETC, ETF oder Future.",
        "long_explanation": (
            "Rohstoffe werfen keine Dividende ab. Der Ertrag kommt aus Preisänderung und, bei Futures, "
            "aus der Terminkurve (Contango/Backwardation). Privat kaufst du selten den Rohstoff selbst, "
            "sondern ein Vehikel: Gold-ETF an der SIX (z. B. ZGLD.SW), Xetra-Gold (4GLD.DE) oder einen "
            "breiten Rohstoff-UCITS.\n\n"
            "US-Produkte wie GLD sind oft nicht verfügbar. Futures (=F bei Yahoo) sind nichts fürs "
            "gewöhnliche Wertschriftendepot. Gold gilt als Krisen- und Währungshedge, schwankt aber stark "
            "und korreliert nicht immer negativ mit Aktien. Öl-ETCs können durch Rollkosten langfristig "
            "hinter dem Spotpreis zurückbleiben."
        ),
        "related_terms": ["ETC", "ETF", "UCITS", "Volatilität"],
        "chart_hint": None,
    },
    {
        "term": "ETC",
        "slug": "etc",
        "short_definition": "Exchange Traded Commodity — börsengehandeltes Rohstoff-Papier, oft mit Metall hinterlegt.",
        "long_explanation": (
            "Ein ETC bildet den Preis eines Rohstoffs oder eines Rohstoffindex ab. Im Unterschied zum ETF "
            "ist es häufig eine Schuldverschreibung des Emittenten, teilweise mit physischer Hinterlegung "
            "(Goldbarren im Tresor). Das Emittentenrisiko ist deshalb anders als bei einem Sondervermögen.\n\n"
            "In der App behandeln wir Gold-Vehikel wie ZGLD.SW unter Rohstoffe. Lies im KID, ob physisch "
            "hinterlegt wird, welche Gebühr anfällt und in welcher Währung der ETC notiert. Ein ETC ist "
            "kein «sicheres» Depot — der Goldpreis kann über Jahre seitwärts oder nach unten laufen."
        ),
        "related_terms": ["Rohstoff", "ETF", "PRIIPs-KID"],
        "chart_hint": None,
    },
    {
        "term": "Devisen",
        "slug": "devisen",
        "short_definition": "Fremdwährungen. Der Kurs (z. B. USD/CHF) ist ein Wechselkurs, kein Anteilschein.",
        "long_explanation": (
            "Devisen handelst du am Spotmarkt, als Forward oder über den Broker, wenn du Aktien in USD kaufst. "
            "Yahoo-Ticker wie EURUSD=X oder USDCHF=X sind Referenzkurse — du «besitzt» damit kein Papier. "
            "Deshalb tauchen sie in den Signalen dieser App nicht als kaufbare Empfehlung auf.\n\n"
            "Trotzdem wirkt Währung ins Depot: Ein US-ETF in USD gewinnt in CHF, wenn der Dollar steigt — "
            "und verliert, wenn er fällt. Manche UCITS bieten währungsgesicherte Tranchen (hedged). "
            "Absicherung kostet und ist kein Freibrief. Für den Alltag reicht oft: wissen, in welcher "
            "Währung der Titel notiert und wie du CHF in USD wechselst (Spread der Bank)."
        ),
        "related_terms": ["Spread", "UCITS", "ETF"],
        "chart_hint": None,
    },
    {
        "term": "Kryptowährung",
        "slug": "kryptowaehrung",
        "short_definition": "Digitale Assets wie Bitcoin oder Ether — hochvolatil, ohne klassischen Cashflow.",
        "long_explanation": (
            "Krypto-Coins sind keine Aktien: keine Bilanz, keine Dividende, kein Anspruch auf Unternehmensgewinn. "
            "Der Preis folgt Angebot, Nachfrage, Liquidität und Narrativ. In der Schweiz kannst du Coins "
            "über spezialisierte Broker kaufen oder über ETPs/ETNs an EU-Börsen (z. B. ein Bitcoin-ETP auf Xetra).\n\n"
            "Diese App zieht Kurse u. a. von CoinGecko bzw. Yahoo (BTC-USD). Technische Indikatoren funktionieren "
            "rechnerisch, sind aber in 24/7-Märkten mit Wochenendgaps anders zu lesen. Positionen klein halten: "
            "Drawdowns von 50 Prozent und mehr sind historisch üblich, nicht die Ausnahme."
        ),
        "related_terms": ["Volatilität", "Drawdown", "Watchlist"],
        "chart_hint": None,
    },
    {
        "term": "ISIN",
        "slug": "isin",
        "short_definition": "Internationale Wertpapierkennnummer — 12 Stellen, eindeutig pro Emission.",
        "long_explanation": (
            "Die ISIN (z. B. IE00B3RBWM25 für einen Vanguard-All-World-UCITS) identifiziert das Papier, "
            "nicht den Handelsplatz. Derselbe ETF kann als VWCE.DE, VWRA.L oder unter anderem Ticker laufen "
            "und trotzdem dieselbe ISIN haben — gleicher Fonds, andere Börse, anderer Währungspreis.\n\n"
            "In der Schweiz siehst du oft zusätzlich die Valor-Nummer. Für Orders ist die ISIN die sauberste "
            "Angabe, wenn Ticker mehrdeutig sind. Yahoo und diese App arbeiten primär mit Tickern plus "
            "Börsenkürzel (.SW, .DE, .L). Wenn du uns einen Titel nennst, helfen ISIN oder Ticker gleichermassen."
        ),
        "related_terms": ["Yahoo-Ticker", "ETF", "UCITS"],
        "chart_hint": None,
    },
    {
        "term": "Yahoo-Ticker",
        "slug": "yahoo-ticker",
        "short_definition": "Kurssymbol bei Yahoo Finance, oft mit Börsen-Endung: NESN.SW, VWCE.DE, IDTL.L.",
        "long_explanation": (
            "Ohne Endung meint Yahoo meist die USA (AAPL = Nasdaq). Europäische und Schweizer Titel brauchen "
            "das Suffix: .SW für SIX, .DE für Xetra, .L für London, .MI für Mailand, .PA für Paris. "
            "Devisen enden auf =X, Futures auf =F — Letztere sind hier keine empfohlenen Kaufprodukte.\n\n"
            "Dieselbe Firma kann mehrere Ticker haben ( Nestlé als NESN.SW, ADR anderswo). Für UCITS nimmst du "
            "die Börse, an der dein Broker günstig und in der gewünschten Währung handelt. Falsch gewähltes "
            "Suffix liefert leere Kurse oder das US-Produkt, das du nicht ordern kannst."
        ),
        "related_terms": ["ISIN", "SIX Swiss Exchange", "ETF"],
        "chart_hint": None,
    },
    {
        "term": "SIX Swiss Exchange",
        "slug": "six",
        "short_definition": "Die Schweizer Börse in Zürich. Yahoo-Endung: .SW (z. B. NESN.SW, CSSMI.SW).",
        "long_explanation": (
            "An der SIX notieren SMI- und SPI-Titel, Schweizer ETFs und viele strukturierte Produkte. "
            "Handel läuft in CHF, die Aufsicht liegt bei der FINMA bzw. den Börsenregeln. Für dich heißt das: "
            "kurze Abwicklung, oft Stempelabgabe auf den Umsatz, keine US-Quellensteuer auf rein Schweizer Titel.\n\n"
            "ETFs wie CSSMI.SW (SMI) oder ZGLD.SW (Gold) sind typische SIX-Vehikel mit KID. "
            "Nicht jeder UCITS ist in Zürich kotiert — viele handelst du über Xetra oder London und "
            "lieferst ins gleiche Depot. Der Handelsplatz ändert den Fonds nicht, aber Währung, Spread und "
            "Handelszeiten."
        ),
        "related_terms": ["Yahoo-Ticker", "Stempelabgabe", "SMI", "ETF"],
        "chart_hint": None,
    },
    {
        "term": "SMI",
        "slug": "smi",
        "short_definition": "Swiss Market Index — die 20 größten Blue Chips der Schweiz (Nestlé, Novartis, Roche …).",
        "long_explanation": (
            "Der SMI ist der Leitindex der SIX, nach Free Float gewichtet. Wenige Konzerne (Nahrung, Pharma, "
            "Finanz) dominieren — das ist weniger breit als ein Weltindex. CSSMI.SW bildet den SMI als UCITS-ETF ab.\n\n"
            "Für die Einordnung: Hohe Konzentration bedeutet, dass zwei oder drei Titel die Performance treiben. "
            "Ein SMI-ETF ersetzt keinen globalen Aktienbaustein, ergänzt ihn aber um Heimatmarkt und CHF-Notierung. "
            "Dividenden der Konstituenten fließen je nach ETF-Variante aus oder werden thesauriert."
        ),
        "related_terms": ["Index", "ETF", "SIX Swiss Exchange", "Benchmark"],
        "chart_hint": None,
    },
    {
        "term": "Index",
        "slug": "index",
        "short_definition": "Rechengröße für einen Markt, z. B. SMI, S&P 500 oder FTSE All-World — selbst nicht kaufbar.",
        "long_explanation": (
            "Ein Index ist eine Formel: welche Titel, welche Gewichtung, welche Währung. Du kannst den Index "
            "nicht direkt besitzen, nur ein Produkt, das ihn nachbildet (ETF, Fonds, Zertifikat). "
            "Bekannte Beispiele: S&P 500 (große US-Firmen), FTSE All-World (global), SMI (Schweiz).\n\n"
            "Wichtig ist die Methodik: Marktkapitalisierung bevorzugt Große, Equal Weight behandelt alle gleich, "
            "Faktor-Indizes filtern nach Value oder Qualität. Der Tracking Error sagt, wie nah der ETF am Index bleibt. "
            "In den Signalen vergleichen wir das Paper-Depot grob mit einem S&P-500-Vehikel als Benchmark — "
            "nicht mit deinem persönlichen CHF-Ziel."
        ),
        "related_terms": ["ETF", "Benchmark", "SMI", "S&P 500"],
        "chart_hint": None,
    },
    {
        "term": "S&P 500",
        "slug": "sp-500",
        "short_definition": "Index der 500 größten US-börsennotierten Unternehmen, nach Marktkapitalisierung.",
        "long_explanation": (
            "Der S&P 500 gilt als Maßstab für den US-Aktienmarkt. Tech-Giganten haben ein hohes Gewicht — "
            "das Indexrisiko ist nicht «500 gleich große Firmen». VOO ist das bekannte US-ETF, für CH-Retail "
            "meist ungeeignet. UCITS-Pendants sind z. B. SXR8.DE oder CSPX.L.\n\n"
            "Ein S&P-500-ETF ist ein USA-Baustein, kein Weltportfolio: Europa, Schweiz, Schwellenländer fehlen "
            "oder sind nur über ADR-Umwege drin. Währung ist effektiv USD. Als Benchmark in dieser App dient "
            "er zur Einordnung der Paper-Rendite, nicht als Kaufempfehlung."
        ),
        "related_terms": ["Index", "ETF", "UCITS", "Benchmark", "Market Cap"],
        "chart_hint": None,
    },
    {
        "term": "TER",
        "slug": "ter",
        "short_definition": "Total Expense Ratio — laufende jährliche Kosten des Fonds in Prozent des Vermögens.",
        "long_explanation": (
            "Die TER enthält Verwaltungs- und Betriebskosten des ETFs oder Fonds, die täglich dem Vermögen "
            "belastet werden. 0,07 % bis 0,25 % sind bei breiten Aktien-UCITS üblich, Themen- und Rohstoffprodukte "
            "liegen oft höher. Die TER siehst du im KID.\n\n"
            "Nicht in der TER: Handelskosten beim Kaufen (Courtage, Spread, Stempel), Bid-Ask und Steuern. "
            "Ein «günstiger» ETF mit schlechtem Spread an illiquider Börse kann teurer sein als ein etwas "
            "höherer TER an Xetra. Über Jahrzehnte frisst die TER einen sichtbaren Teil der Rendite — "
            "deshalb lohnt der Vergleich, bevor du umschichtest."
        ),
        "related_terms": ["PRIIPs-KID", "ETF", "Spread", "Thesaurierend"],
        "chart_hint": None,
    },
    {
        "term": "Thesaurierend",
        "slug": "thesaurierend",
        "short_definition": "Erträge (Dividenden, Coupons) bleiben im Fonds und werden automatisch wieder angelegt.",
        "long_explanation": (
            "Thesaurierende Tranchen (often «Acc») erhöhen den Inventarwert statt Geld auszuzahlen. "
            "Ausschüttende Tranchen («Dist») überweisen Dividenden aufs Konto — du musst sie selbst versteuern "
            "und entscheiden, ob du neu investierst.\n\n"
            "In der Schweiz sind beide Varianten üblich. Steuerlich zählt nicht nur die Ausschüttung: "
            "auch thesaurierte Erträge können in der Steuererklärung erscheinen (abhängig von Produkt und Kanton). "
            "Fürs Rebalancing ist Acc oft bequemer. Dieselbe ISIN-Familie hat häufig beide Anteilsklassen — "
            "nicht verwechseln beim Ordern."
        ),
        "related_terms": ["Dividende", "ETF", "TER"],
        "chart_hint": None,
    },
    {
        "term": "Replikation",
        "slug": "replikation",
        "short_definition": "Wie ein ETF den Index nachbildet: physisch (Titel kaufen) oder synthetisch (Swap).",
        "long_explanation": (
            "Physisch heißt: der ETF hält die Indexmitglieder oder eine optimierte Stichprobe. "
            "Synthetisch heißt: ein Swap mit einer Bank liefert die Indexrendite; im Fonds liegen Sicherheiten. "
            "Beide Formen sind unter UCITS erlaubt, wenn Limits und Sicherheiten stimmen.\n\n"
            "Für Aktienwelt-ETFs ist physisch der Standard und leichter verständlich. Bei Rohstoffen oder "
            "schwierigen Märkten siehst du häufiger synthetische oder ETC-Strukturen. Lies im Factsheet "
            "«Replication». Synthetisch ist nicht automatisch schlecht — du tauschst Tracking gegen "
            "Gegenparteirisiko, das UCITS begrenzt, aber nicht auf null setzt."
        ),
        "related_terms": ["ETF", "UCITS", "Index", "ETC"],
        "chart_hint": None,
    },
    {
        "term": "Spread",
        "slug": "spread",
        "short_definition": "Abstand zwischen Geld- (Bid) und Briefkurs (Ask) — implizite Handelskosten.",
        "long_explanation": (
            "Du kaufst zum Ask und verkaufst zum Bid. Die Differenz ist der Spread, oft in Basispunkten. "
            "Enge Spreads gibt es bei liquiden UCITS zu Xetra-Hauptzeiten, weite Spreads bei exotischen "
            "Themen-ETFs oder außerhalb der Kernhandelszeit.\n\n"
            "Limit Orders schützen vor ungünstigen Prints; Market Orders fressen den Spread sofort. "
            "Bei Devisen ist der Spread die Marge der Bank. In Charts dieser App siehst du Schlusskurse — "
            "die sagen nichts über den Spread zum Zeitpunkt deiner Order. Große Orders in kleinen ETFs "
            "verschieben den Preis zusätzlich (Marktimpact)."
        ),
        "related_terms": ["Liquidität", "ETF", "Devisen"],
        "chart_hint": None,
    },
    {
        "term": "Liquidität",
        "slug": "liquiditaet",
        "short_definition": "Wie schnell du ohne großen Kursabschlag kaufen oder verkaufen kannst.",
        "long_explanation": (
            "Bei Aktien zählt das tägliche Volumen. Bei ETFs zählt beides: der Handel im ETF selbst und "
            "die Liquidität der enthaltenen Titel — Market Maker können neue Anteile schaffen (Creation/Redemption). "
            "Ein ETF mit kleinem Tagesumsatz kann trotzdem handelbar sein, wenn der Underlying liquide ist.\n\n"
            "Unliquide Papiere haben weite Spreads und sprunghafte Kurse. Das verzerrt technische Indikatoren "
            "und Paper-Fills. Für die Watchlist: SMI- und Welt-UCITS sind in der Regel liquide genug; "
            "Nischen-ETCs und kleine Small Caps nicht. Crypto handelt rund um die Uhr, die Tiefe des Orderbuchs "
            "schwankt trotzdem stark."
        ),
        "related_terms": ["Spread", "ETF", "Volatilität"],
        "chart_hint": None,
    },
    {
        "term": "Stempelabgabe",
        "slug": "stempelabgabe",
        "short_definition": "Schweizer Umsatzabgabe auf den Kauf und Verkauf vieler Wertschriften.",
        "long_explanation": (
            "Die Eidgenössische Stempelabgabe fällt an, wenn ein inländischer Effektenhändler (Bank, Broker) "
            "am Umsatz beteiligt ist. Typische Sätze liegen bei 0,075 % auf inländische und 0,15 % auf "
            "ausländische Papiere — je Seite, Details und Ausnahmen stehen im Gesetz und beim Broker.\n\n"
            "ETFs können je nach Domizil und Handel unterschiedlich getroffen werden. Manche Broker weisen "
            "die Abgabe transparent aus. Sie ist keine Einkommenssteuer und unabhängig vom Gewinn. "
            "Häufiges Umschichten wird dadurch teurer — ein Argument für weniger Trades, nicht für «nie handeln»."
        ),
        "related_terms": ["SIX Swiss Exchange", "ETF", "Quellensteuer"],
        "chart_hint": None,
    },
    {
        "term": "Quellensteuer",
        "slug": "quellensteuer",
        "short_definition": "Steuer, die das Quellenland direkt von Dividende oder Zins abzieht — z. B. USA 30 %.",
        "long_explanation": (
            "Bei US-Aktien behält der US-Staat standardmäßig 30 % der Dividende ein. Mit gültigem W-8BEN "
            "und Doppelbesteuerungsabkommen sinkt der Satz oft auf 15 %; den Rest kannst du unter Umständen "
            "in der Schweiz anrechnen. Obligatorisch ist die sorgfältige Steuererklärung — keine Automatik.\n\n"
            "Irische UCITS auf US-Indizes haben häufig eine günstigere Behandlung der US-Dividenden im Fonds "
            "als der Direkterwerb jeder Aktie, abhängig von Struktur und Abkommen. Das ist ein Grund, warum "
            "viele Europäer S&P 500 über Irland (.DE/.L) statt über VOO halten. Verbindliche Auskunft gibt "
            "Steuerberatung, nicht diese App."
        ),
        "related_terms": ["Dividende", "UCITS", "Aktie", "Stempelabgabe"],
        "chart_hint": None,
    },
    {
        "term": "Dividende",
        "slug": "dividende",
        "short_definition": "Gewinnanteil, den eine AG an die Aktionäre ausschüttet — nicht garantiert.",
        "long_explanation": (
            "Die Dividende beschließt die Generalversammlung auf Antrag des VR. Sie kann steigen, sinken "
            "oder entfallen. Am Ex-Tag fällt der Kurs rechnerisch um die Ausschüttung. Die Rendite "
            "(Dividende/Kurs) allein ist kein Qualitätsmerkmal: hohe Rendite kann einen gefallenen Kurs meinen.\n\n"
            "Im ETF kommt die Summe der Indexdividenden an, abzüglich Kosten, und wird je nach Tranche "
            "ausgeschüttet oder thesauriert. Quellensteuer sitzt oft schon im Fonds oder auf deiner Einzelaktie. "
            "Paper-Trading in dieser App verbucht Kurse, nicht automatisch jede Dividende — die Signale "
            "stützen sich auf Kurs, News und Technik, nicht auf die nächste GV."
        ),
        "related_terms": ["Aktie", "Thesaurierend", "Quellensteuer"],
        "chart_hint": None,
    },
    {
        "term": "Watchlist",
        "slug": "watchlist",
        "short_definition": "Deine Beobachtungsliste: Titel, die Agenten und Kurse regelmäßig prüfen.",
        "long_explanation": (
            "Alles auf der Watchlist wird im Intervall (Standard 30 Minuten) mit News, technischen Indikatoren "
            "und einer Kauf/Halten/Verkauf-Empfehlung versehen. Titel nur «entdeckt» aus Headlines landen "
            "zuerst unwatched — du entscheidest, ob sie dauerhaft beobachtet werden.\n\n"
            "Sinnvoll sind Papiere, die du in der Schweiz kaufen kannst: Einzelaktien, UCITS, SIX-ETFs, "
            "ausgewählte Cryptos. US-ETFs ohne KID und Devisenpaare werden für Signale ausgeblendet, "
            "auch wenn Yahoo einen Kurs liefert. Je länger die Liste, desto mehr Token und desto mehr Rauschen."
        ),
        "related_terms": ["Signal", "UCITS", "Yahoo-Ticker", "Agenten"],
        "chart_hint": None,
    },
    {
        "term": "Signal",
        "slug": "signal",
        "short_definition": "Aktuelle Einschätzung der Agenten zu einem Titel: Kauf, Halten oder Verkauf plus Begründung.",
        "long_explanation": (
            "Ein Signal bündelt Research (News, Sentiment), Quant (RSI, SMA, MACD, Kurs) und den Strategist "
            "(Handlung, Konfidenz, Chance-Risiko). Es ist Paper-Trading-Logik, keine persönliche Beratung "
            "und kein Auftrag an die Börse.\n\n"
            "Nur Titel, die als in der Schweiz handelbar gelten, erscheinen in der Signal-Liste. "
            "«Entdeckt» sind Ideen außerhalb der Watchlist, oft aus Schlagzeilen — prüfe Ticker-Endung "
            "und KID, bevor du übernimmst. Alte Signale zu VOO oder GLD sind bewusst ausgeblendet. "
            "Push gibt es nur bei neuem Kauf oder Verkauf, nicht bei jedem Halten."
        ),
        "related_terms": ["Konfidenz", "Chance-Risiko-Verhältnis", "Watchlist", "Paper-Trading"],
        "chart_hint": None,
    },
    {
        "term": "Konfidenz",
        "slug": "konfidenz",
        "short_definition": "Wie sicher sich der Strategist in der Empfehlung ist — Zahl zwischen 0 und 1.",
        "long_explanation": (
            "Konfidenz 0,8 heißt nicht «80 % Gewinnwahrscheinlichkeit». Es ist die Selbsteinschätzung "
            "des Modells auf Basis der gelieferten News und Technik. Widersprechen sich RSI und Schlagzeilen, "
            "sinkt die Konfidenz und die Aktion tendiert zu Halten.\n\n"
            "Ohne API-Key läuft eine grobe Heuristik (z. B. RSI-Schwellen) mit niedriger Konfidenz. "
            "Mit LLM wird der Wert begründet, bleibt aber modellabhängig. Nutze ihn zum Sortieren, "
            "nicht als alleinigen Trigger. Hohe Konfidenz bei dünner News-Lage ist ein Warnzeichen, "
            "kein Freibrief für Größe der Position."
        ),
        "related_terms": ["Signal", "RSI", "Agenten"],
        "chart_hint": None,
    },
    {
        "term": "Chance-Risiko-Verhältnis",
        "slug": "chance-risiko-verhaeltnis",
        "short_definition": "Erwarteter Gewinnweg geteilt durch akzeptierten Verlustweg — oft als R:R notiert.",
        "long_explanation": (
            "Ein Verhältnis von 2 bedeutet: du siehst doppelt so viel potenziellen Gewinn wie Verlust "
            "bis zum gedachten Stopp. Der Strategist schätzt die Zahl aus Kurs, Volatilität und These — "
            "sie ist keine Garantie, dass das Ziel erreicht wird.\n\n"
            "Ohne definiertes Ziel und Stopp ist R:R Kosmetik. In der App steht der Wert bei vielen "
            "Empfehlungen neben der Begründung. Werte unter 1 heißen: das Risiko ist größer als die "
            "skizzierte Chance — dann ist Halten oft ehrlicher als ein erzwungener Trade."
        ),
        "related_terms": ["Stop-Loss", "Signal", "Konfidenz"],
        "chart_hint": None,
    },
    {
        "term": "Paper-Trading",
        "slug": "paper-trading",
        "short_definition": "Übungsdepot mit virtuellem Geld. Keine echte Order, kein echtes P&L beim Broker.",
        "long_explanation": (
            "Du erfasst Käufe und Verkäufe zum von dir gesetzten Preis und siehst unrealisiertes Ergebnis "
            "gegen den aktuellen Kurs. Ziel ist, Signale und Positionsgröße zu üben, ohne Kapital zu riskieren.\n\n"
            "Grenzen: keine garantierte Ausführung, oft kein Dividenden- und Gebührenabzug wie in echt, "
            "kein Margin Call. Wer Paper-Gewinne 1:1 aufs Live-Konto überträgt, unterschätzt Slippage und Psyche. "
            "Trotzdem nützlich, um Agenten-Empfehlungen zu prüfen, bevor irgendetwas bei Swissquote landet."
        ),
        "related_terms": ["Einstandspreis", "Unrealisierter Gewinn", "Signal"],
        "chart_hint": None,
    },
    {
        "term": "Einstandspreis",
        "slug": "einstandspreis",
        "short_definition": "Durchschnittlicher Kaufpreis deiner Position (Average Cost), gewichtet nach Stückzahl.",
        "long_explanation": (
            "Kaufst du nach, mischt sich der neue Preis in den Durchschnitt. Verkaufst du teilweise, "
            "bleibt der Einstand der Restposition oft gleich (je nach Methode). Darüber liegt Gewinn, "
            "darunter Verlust — unrealisiert, solange du nicht verkaufst.\n\n"
            "Im Depot der App setzt du Einstand und Menge selbst. Der Chart «seit Kauf» legt den Einstand "
            "als Referenzlinie. Am Wochenende oder am Kaufstag gibt es oft noch keine neue Kerze — "
            "dann siehst du die letzten Handelstage als Kontext, nicht als fertige Performance seit Order."
        ),
        "related_terms": ["Unrealisierter Gewinn", "Paper-Trading", "Realisierter Gewinn"],
        "chart_hint": "sma",
    },
    {
        "term": "Unrealisierter Gewinn",
        "slug": "unrealisierter-gewinn",
        "short_definition": "Buchgewinn oder -verlust: aktueller Wert minus Einstand, Position noch offen.",
        "long_explanation": (
            "Solange du hältst, ist das Ergebnis nur gerechnet. Es kann sich mit dem nächsten Tick umkehren. "
            "Grün/rot in der App folgt dem Vorzeichen: plus grün, minus rot, null neutral.\n\n"
            "Steuern und Psychologie knüpfen oft erst am realisierten Geschäft an — trotzdem steuert "
            "unrealisiertes P&L, wie groß das Risiko noch im Markt ist. Eine Position «im Plus» ist "
            "kein Grund, den Stopp zu vergessen. Währungsschwankungen (USD-Titel im CHF-Kopf) sitzen "
            "in diesem Betrag mit drin, wenn Kurs und Einstand in derselben Notierung stehen."
        ),
        "related_terms": ["Realisierter Gewinn", "Einstandspreis", "Paper-Trading"],
        "chart_hint": None,
    },
    {
        "term": "Realisierter Gewinn",
        "slug": "realisierter-gewinn",
        "short_definition": "Abgeschlossenes Geschäft: Verkaufserlös minus Einstand (und ggf. Kosten).",
        "long_explanation": (
            "Erst der Verkauf macht aus Buchgewinn einen realisierten. In der App erscheint er bei "
            "Verkaufstransaktionen. Im echten Leben folgen Courtage, Stempel, Steuern — Paper lässt "
            "vieles davon weg.\n\n"
            "Realisiert heißt nicht «klug». Wer Gewinne früh mitnimmt und Verlierer laufen lässt, "
            "erzeugt viele kleine Plus und seltene große Minus. Die Agenten-Logik versucht, These und "
            "Risiko zu benennen; die Buchung bleibt deine Entscheidung."
        ),
        "related_terms": ["Unrealisierter Gewinn", "Stempelabgabe", "Paper-Trading"],
        "chart_hint": None,
    },
    {
        "term": "Volatilität",
        "slug": "volatilitaet",
        "short_definition": "Schwankungsbreite der Kurse — wie heftig der Preis hin- und herläuft.",
        "long_explanation": (
            "Hohe Volatilität heißt große Tages- und Wochenspannen, nicht automatisch Abwärtstrend. "
            "Gemessen oft als Standardabweichung der Renditen oder implizit über Optionen (VIX-ähnlich). "
            "Crypto und Einzelaktien sind volatiler als ein Welt-ETF; lange Anleihen können zwischendurch "
            "ähnlich wild sein wie Aktien.\n\n"
            "Für Stops und Positionsgröße ist Volatilität zentral: enge Stops in hochvolatilen Titeln "
            "werden ständig ausgelöst. RSI-Schwellen 70/30 stammen aus ruhigeren Aktienregimen — "
            "bei Bitcoin greifen sie anders. Die 24h-Veränderung in der Watchlist ist ein kurzer "
            "Volatilitätsblick, kein Jahresrisiko."
        ),
        "related_terms": ["Drawdown", "RSI", "Stop-Loss", "Sharpe Ratio"],
        "chart_hint": None,
    },
    {
        "term": "Drawdown",
        "slug": "drawdown",
        "short_definition": "Verlust vom bisherigen Höchststand bis zum tiefsten Punkt — die schmerzhafte Strecke.",
        "long_explanation": (
            "Ein Drawdown von 30 % heißt: vom Peak musstest du 30 % verkraften, bevor es wieder aufwärts ging. "
            "Um auf den alten Höchststand zurückzukommen, brauchst du danach rund 43 % Gewinn. "
            "Das vergessen Renditewerbung und kurze Backtests gern.\n\n"
            "Welt-ETFs hatten historisch Drawdowns über 40 % (z. B. 2008, 2020). Einzelaktien und Krypto "
            "können 70 % und mehr verlieren und nie zurückkehren. Paper-Equity glättet das nicht weg. "
            "Signale «Kauf» in einem laufenden Drawdown können richtig sein — oder zu früh. Die Begründung "
            "sollte sagen, was die Meinung ändern würde."
        ),
        "related_terms": ["Volatilität", "Benchmark", "Paper-Trading"],
        "chart_hint": None,
    },
    {
        "term": "Benchmark",
        "slug": "benchmark",
        "short_definition": "Maßstab, gegen den du Depot oder Strategie hältst — hier grob ein S&P-500-Vehikel.",
        "long_explanation": (
            "Ohne Benchmark fühlst du dich klug, wenn alles steigt, und dumm, wenn alles fällt. "
            "Der Vergleich beantwortet: War ich besser als ein einfaches Markt-Exposure? "
            "In der App dient ein S&P-500-Proxy als Referenz für die Paper-Rendite.\n\n"
            "Für ein CHF-Leben ist der S&P 500 unvollständig (Währung, Regionen). Ein persönlicher Maßstab "
            "könnte 80 % VWCE plus 20 % Obligationen-UCITS sein. Wichtig: dieselbe Währung und denselben "
            "Zeitraum vergleichen. Die Agenten optimieren nicht auf die Benchmark — sie bewerten Titel einzeln."
        ),
        "related_terms": ["Index", "S&P 500", "ETF", "Diversifikation"],
        "chart_hint": None,
    },
    {
        "term": "Diversifikation",
        "slug": "diversifikation",
        "short_definition": "Streuung: nicht alles in einen Titel, eine Branche, ein Land oder eine Währung.",
        "long_explanation": (
            "Unkorrelierte Risiken mitteln sich. Ein Welt-ETF ist bereits eine erste Streuung über Hunderte "
            "Firmen. Zehn Tech-Aktien sind das nicht, auch wenn die Liste lang wirkt. Obligationen und Gold "
            "können Aktienrisiken dämpfen — tun es aber nicht in jeder Krise gleich.\n\n"
            "Die Watchlist darf thematisch breit sein; das Depot sollte nicht jedes Signal hebeln. "
            "Heimatbias (nur SMI) und US-Bias (nur S&P) sind die üblichen Fallen. UCITS machen Streuung "
            "billig — sie ersetzen nicht die Entscheidung, wie viel Risiko du überhaupt tragen willst."
        ),
        "related_terms": ["ETF", "Korrelation", "Benchmark", "UCITS"],
        "chart_hint": None,
    },
    {
        "term": "Korrelation",
        "slug": "korrelation",
        "short_definition": "Maß, ob sich zwei Kurse tendenziell gemeinsam, entgegengesetzt oder unabhängig bewegen.",
        "long_explanation": (
            "Korrelation 1: laufen parallel. −1: laufen gegengleich. 0: kein linearer Gleichlauf. "
            "In Stressphasen rutschen viele «unkorrelierte» Anlagen Richtung 1 — Diversifikation versagt "
            "genau dann, wenn du sie brauchst.\n\n"
            "Gold, lange Treasuries und der S&P wechseln ihre Beziehung über Jahrzehnte. "
            "Zwei Tech-Aktien sind hoch korreliert, auch wenn die Stories verschieden klingen. "
            "Die App berechnet keine volle Korrelationsmatrix; wenn Research und Quant dasselbe "
            "Marktregime beschreiben, ist das ein Hinweis auf Gleichlauf, kein Ersatz fürs Rechnen."
        ),
        "related_terms": ["Diversifikation", "Volatilität", "Rohstoff"],
        "chart_hint": None,
    },
    {
        "term": "Agenten",
        "slug": "agenten",
        "short_definition": "Vier Rollen in dieser App: Research, Quant, Strategist, Educator — plus Discover.",
        "long_explanation": (
            "Research liest Schlagzeilen und bildet ein Sentiment, ohne News zu erfinden. "
            "Quant holt Kurse und berechnet RSI, Gleitende Durchschnitte, MACD. "
            "Der Strategist formuliert Kauf, Halten oder Verkauf mit Begründung und Konfidenz. "
            "Der Educator hängt Fachbegriffe an. Discover schlägt Titel außerhalb der Watchlist vor, "
            "die in der Schweiz kaufbar sein sollen.\n\n"
            "Läufe kosten Tokens (Modell 4.1 / 4.1-mini). Ohne Key greift eine Heuristik. "
            "Die Agenten sehen keine Orderbuch-Tiefe und keine Steuer. Ihre Texte sind Diskussionsgrundlage, "
            "kein Auftrag."
        ),
        "related_terms": ["Signal", "Watchlist", "Konfidenz", "RSI"],
        "chart_hint": None,
    },
    {
        "term": "RSI",
        "slug": "rsi",
        "short_definition": "Relative Strength Index — Momentum von 0 bis 100, klassisch über 14 Perioden.",
        "long_explanation": (
            "Der RSI vergleicht durchschnittliche Aufwärts- mit Abwärtsbewegungen. "
            "Über 70 gilt traditionell als überkauft, unter 30 als überverkauft — Schwellen, keine Gesetze. "
            "In starken Trends kann der RSI Wochen über 70 bleiben, während der Kurs weiter steigt. "
            "Umgekehrt bleibt er in Bärenmärkten lange unter 40, ohne zuverlässig zu drehen.\n\n"
            "Die App nutzt RSI-14 auf Tagesschlusskursen. Für Bond-ETFs und Gold sind die gleichen Zahlen "
            "anders zu lesen als für Einzelaktien. Ohne LLM kauft die Heuristik eher bei tiefem RSI "
            "und verkauft bei hohem — das ist grob und verliert in Trendmärkten. Divergenzen "
            "(Kurs hoch, RSI tiefer) erwähnt der Strategist nur, wenn die Daten das hergeben."
        ),
        "related_terms": ["MACD", "SMA", "EMA", "Volatilität"],
        "chart_hint": "rsi",
    },
    {
        "term": "SMA",
        "slug": "sma",
        "short_definition": "Simple Moving Average — arithmetisches Mittel der letzten n Schlusskurse.",
        "long_explanation": (
            "Jeder der n Tage zählt gleich. SMA-20 glättet etwa einen Handelsmonat, SMA-50 ein Quartal, "
            "SMA-200 das grobe Jahresbild. Kurs über der 200-Tage-Linie wird oft als Aufwärtstrend gelesen, "
            "darunter als Abwärtstrend — populär, nicht magisch.\n\n"
            "Kreuzungen (goldenes Kreuz: 50 über 200, Todeskreuz umgekehrt) sind langsam und kommen spät. "
            "Dafür filtern sie Rauschen. In der App siehst du SMA-20 und SMA-50 in den technischen Blöcken "
            "und im Detailchart. Der SMA hängt hinter dem Preis; nach Gaps (Wochenende, News) wirkt er "
            "eine Weile «falsch herum», bis die neuen Kurse durchgelaufen sind."
        ),
        "related_terms": ["EMA", "MACD", "Einstandspreis"],
        "chart_hint": "sma",
    },
    {
        "term": "EMA",
        "slug": "ema",
        "short_definition": "Exponential Moving Average — jüngere Kurse zählen stärker als ältere.",
        "long_explanation": (
            "Der EMA reagiert schneller als der SMA gleicher Länge und eignet sich für kurzfristiges Momentum. "
            "Nachteil: mehr Fehlsignale. MACD baut auf EMA-12 und EMA-26 auf, die Signallinie ist ein EMA-9 "
            "dieser Differenz.\n\n"
            "Händler kombinieren oft EMA-20 als dynamische Unterstützung im Aufwärtstrend. "
            "Das bricht in Seitwärtsphasen. Für langsame Bausteine (Welt-ETF) reicht der SMA; "
            "für Einzelaktien und Krypto siehst du den EMA häufiger in den Quant-Notizen."
        ),
        "related_terms": ["SMA", "MACD", "RSI"],
        "chart_hint": "ema",
    },
    {
        "term": "MACD",
        "slug": "macd",
        "short_definition": "Moving Average Convergence Divergence — Abstand zweier EMAs plus Signallinie.",
        "long_explanation": (
            "MACD-Linie = EMA-12 minus EMA-26. Signal = EMA-9 der MACD-Linie. Histogramm = Differenz der beiden. "
            "Schneidet MACD das Signal von unten, gilt das als bullishes Momentum, von oben als bearish. "
            "Null-Linie: MACD positiv heißt kurzfristiger EMA über dem längeren.\n\n"
            "Wie alle Überlagerungen von Durchschnitten spätet der MACD in engen Ranges und liefert "
            "Peitschenhiebe. In den Empfehlungs-Charts ist das Histogramm als Mini-Balken angedeutet. "
            "Der Strategist soll MACD nicht isoliert gegen klare News stellen — ein positives Histogramm "
            "bei Gewinnwarnung ist kein Kaufgrund."
        ),
        "related_terms": ["EMA", "RSI", "Signal"],
        "chart_hint": "macd",
    },
    {
        "term": "Sharpe Ratio",
        "slug": "sharpe-ratio",
        "short_definition": "Überrendite zum risikofreien Zins, geteilt durch die Volatilität der Renditen.",
        "long_explanation": (
            "Sharpe fragt: Bekomme ich genug Extra-Rendite für das Schwanken? "
            "Wert 1 gilt umgangssprachlich als ordentlich, 2 als stark — abhängig von Periode und Zinsniveau. "
            "Negativer Sharpe heißt: du wurdest fürs Risiko nicht einmal mit mehr Rendite als Cash bezahlt.\n\n"
            "Schwächen: Sharpe straft Aufwärtsvolatilität genauso wie Abwärtsvolatilität und mag glatte "
            "Strategien, die in Crashes zerbrechen. Für ein Paper-Depot über wenige Tage ist die Zahl "
            "unbrauchbar. Sinnvoll wird sie über Jahre und im Vergleich zweier ähnlicher Portfolios, "
            "nicht als Note für eine einzelne Aktienempfehlung."
        ),
        "related_terms": ["Volatilität", "Drawdown", "Benchmark"],
        "chart_hint": None,
    },
    {
        "term": "Stop-Loss",
        "slug": "stop-loss",
        "short_definition": "Verkauf, sobald der Kurs eine Untergrenze berührt — Verlust begrenzen, nicht maximieren.",
        "long_explanation": (
            "Ein Stop-Loss ist eine Regel, kein Gefühl. Zu eng: normales Rauschen wirft dich raus, "
            "du kaufst höher nach. Zu weit: der Stopp kommt einer Kapitulation gleich. "
            "Viele setzen ihn unter ein technisches Tief oder als Vielfaches der durchschnittlichen Tagesspanne.\n\n"
            "In der Schweiz sind Stop-Orders beim Broker üblich, aber nicht garantiert — Gaps über das Limit "
            "sind möglich. Paper-Trading löst sie nicht automatisch aus. Der Strategist soll in der Begründung "
            "sagen, was die These bricht; das ist der gedankliche Stopp, auch ohne Order im Buch."
        ),
        "related_terms": ["Chance-Risiko-Verhältnis", "Volatilität", "Signal"],
        "chart_hint": None,
    },
    {
        "term": "Market Cap",
        "slug": "market-cap",
        "short_definition": "Marktkapitalisierung: Kurs × Anzahl der Aktien (bei Coins: Preis × umlaufende Menge).",
        "long_explanation": (
            "Large Caps (hundert Milliarden und mehr) sind in der Regel liquider und in Indizes schwerer. "
            "Small Caps können stärker steigen und tiefer fallen. Die Market Cap ist Größe, nicht Güte: "
            "ein teures Unternehmen kann «groß» sein, weil der Kurs hoch ist, nicht weil der Gewinn es ist.\n\n"
            "Indizes wie der S&P 500 und der SMI gewichten nach Cap — die Größten bestimmen die ETF-Rendite. "
            "Bei Krypto beschreibt die Cap den Markt, ist aber durch illiquide Coins leicht verzerrt. "
            "Für Orders: große Caps haben engere Spreads. Das allein macht sie nicht zum besseren Investment."
        ),
        "related_terms": ["Index", "Aktie", "Liquidität", "S&P 500"],
        "chart_hint": None,
    },
]
