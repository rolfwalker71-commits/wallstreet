import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { PriceChart } from "@/components/charts/PriceChart";
import { ActionChip } from "@/components/ui/ActionChip";
import { SignedPct } from "@/components/ui/Signed";
import { WatchlistButton } from "@/components/ui/WatchlistButton";
import { api, type Asset, type Dossier, type Quote, type Recommendation, type Technicals } from "@/lib/api";
import { QuoteStamp } from "@/components/market/QuoteStamp";
import { CLASS_LABEL, money, number, pct, recAccentClass, signedClass, when } from "@/lib/format";
import { panelClass, type Chrome } from "@/lib/platform";

type NewsRow = { title: string; url: string; source: string; published_at: string | null };

export function WatchlistDetailPage() {
  const raw = useParams().symbol;
  const symbol = raw ? decodeURIComponent(raw) : "";
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [asset, setAsset] = useState<Asset | null>(null);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [tech, setTech] = useState<Technicals | null>(null);
  const [news, setNews] = useState<NewsRow[]>([]);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    setError(null);
    setAsset(null);
    Promise.all([
      api.asset(symbol),
      api.quote(symbol).catch(() => null),
      api
        .recommendations(new URLSearchParams({ symbol, latest: "true", limit: "1" }))
        .then((rows) => rows[0] ?? null)
        .catch(() => null),
      api.technicals(symbol).catch(() => null),
      api.news(symbol).catch(() => []),
      api.dossier(symbol).catch(() => null),
    ])
      .then(([a, q, r, t, n, d]) => {
        setAsset(a);
        setQuote(q);
        setRec(r);
        setTech(t);
        setNews(n);
        setDossier(d);
      })
      .catch((e: Error) => setError(e.message));
  }, [symbol]);

  const runOne = async () => {
    if (!symbol) return;
    setBusy(true);
    setError(null);
    try {
      const rows = await api.runAgents(symbol);
      if (rows[0]) setRec(rows[0]);
      const q = await api.quote(symbol).catch(() => null);
      if (q) setQuote(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lauf fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  if (error && !asset) return <p role="alert">{error}</p>;
  if (!asset) return <p>Lädt {symbol}…</p>;

  const change = quote?.change_pct;
  const price = quote?.price ?? asset.last_price;
  const techEntries = tech
    ? Object.entries(tech).filter(([k, v]) => k !== "symbol" && v != null)
    : [];

  return (
    <article className="space-y-4">
      <Link
        to="/watchlist"
        className="inline-flex min-h-12 items-center text-sm text-primary"
      >
        ← Zurück zur Watchlist
      </Link>

      <header className={`${panelClass(chrome)} px-5 py-5`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-2xl font-semibold leading-snug tracking-tight break-words">
              {asset.symbol} · {asset.name}
            </h2>
            <p className="text-sm text-muted-foreground">
              {CLASS_LABEL[asset.asset_class] ?? asset.asset_class}
              {asset.isin ? ` · ${asset.isin}` : dossier?.isin ? ` · ${dossier.isin}` : ""}
              {asset.exchange ? ` · ${asset.exchange}` : ""}
              {asset.watched ? "" : " · Entdeckt"}
            </p>
          </div>
          {rec ? <ActionChip action={rec.action} /> : null}
        </div>
        <p className={`mt-4 text-3xl font-semibold ${signedClass(change)}`}>
          {money(price, asset.currency)}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {change != null ? (
            <span
              className={`inline-flex rounded-full px-2.5 py-0.5 text-sm font-medium ${
                change > 0
                  ? "bg-gain-container text-gain"
                  : change < 0
                    ? "bg-loss-container text-loss"
                    : "bg-muted text-muted-foreground"
              }`}
            >
              <SignedPct value={change} /> 24h
            </span>
          ) : null}
          <QuoteStamp
            asOf={quote?.as_of ?? asset.last_price_at}
            delayed={quote?.delayed}
            sessionLabel={quote?.session_label}
            marketOpen={quote?.market_open}
            venueLabel={quote?.venue_label}
            freshnessLabel={quote?.freshness_label}
            asOfPrecision={quote?.as_of_precision}
          />
        </div>
        {asset.notes ? (
          <p className="mt-3 rounded-2xl bg-gain-container px-3 py-2 text-sm text-gain">
            {asset.notes}
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <WatchlistButton
            asset={asset}
            chrome={chrome}
            onChanged={setAsset}
          />
          <button
            type="button"
            onClick={runOne}
            disabled={busy}
            className={`${
              chrome === "desktop" ? "min-h-11 rounded-md px-4" : "min-h-12 rounded-full px-5"
            } bg-primary font-medium text-on-primary disabled:opacity-60`}
          >
            {busy ? "Bewertet…" : "Jetzt bewerten"}
          </button>
        </div>
      </header>

      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}

      <section
        className={`${panelClass(chrome)} ${rec ? recAccentClass(rec.action) : ""} px-5 py-5`}
      >
        <h3 className="text-lg font-semibold">Aktuelle Bewertung</h3>
        {rec ? (
          <>
            <p className="mt-3 text-sm text-muted-foreground">{when(rec.created_at)}</p>
            <p className="mt-2 leading-relaxed">{rec.rationale}</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Konfidenz {pct(Number(rec.confidence) * 100)}
              {rec.risk_reward_ratio
                ? ` · Chance/Risiko ${number(rec.risk_reward_ratio, 2)}`
                : ""}
            </p>
            {rec.news_summary ? (
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{rec.news_summary}</p>
            ) : null}
            <Link
              to={`/signals/${rec.id}`}
              className="mt-3 inline-flex min-h-11 items-center text-sm text-primary"
            >
              Ganze Empfehlung öffnen
            </Link>
          </>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            Noch kein Agenten-Lauf für diesen Titel. «Jetzt bewerten» startet Research, Quant und Strategist.
          </p>
        )}
      </section>

      {dossier ? (
        <section className={`${panelClass(chrome)} px-5 py-5`}>
          <h3 className="text-lg font-semibold">Dossier</h3>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">ISIN</dt>
              <dd className="font-medium break-words">{dossier.isin ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">TER</dt>
              <dd className="font-medium">{dossier.ter != null ? `${number(dossier.ter, 2)} %` : "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">KGV</dt>
              <dd className="font-medium">{number(dossier.pe_ratio, 1)}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Dividendenrendite</dt>
              <dd className="font-medium">
                {dossier.dividend_yield != null ? `${number(dossier.dividend_yield, 2)} %` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Index</dt>
              <dd className="font-medium break-words">{dossier.index_name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Domizil / Ertrag</dt>
              <dd className="font-medium break-words">
                {[dossier.domicile, dossier.distribution].filter(Boolean).join(" · ") || "—"}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-sm text-muted-foreground">{dossier.broker_rule}</p>
          {dossier.notes.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {dossier.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-3 text-sm">
            {dossier.justetf_url ? (
              <a className="text-primary underline-offset-2 hover:underline" href={dossier.justetf_url} target="_blank" rel="noreferrer">
                JustETF / KID-Profil
              </a>
            ) : null}
            {dossier.issuer_url ? (
              <a className="text-primary underline-offset-2 hover:underline" href={dossier.issuer_url} target="_blank" rel="noreferrer">
                Emittent
              </a>
            ) : null}
            <a className="text-primary underline-offset-2 hover:underline" href={dossier.yahoo_url} target="_blank" rel="noreferrer">
              Yahoo Finance
            </a>
          </div>
          {dossier.calendar.length ? (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-primary">Termine (Quelle genannt)</h4>
              <ul className="mt-2 space-y-1 text-sm">
                {dossier.calendar.map((c) => (
                  <li key={`${c.kind}-${c.date}`}>
                    {c.kind === "earnings" ? "Ergebnisse" : "Ex-Dividende"} · {c.date} · {c.source}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Keine gemeldeten Earnings-/Ex-Div-Daten in Yahoo.</p>
          )}
          {dossier.peers.length ? (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-primary">Vergleich (gleiche Sleeve)</h4>
              <ul className="mt-2 space-y-2 text-sm">
                {dossier.peers.map((p) => (
                  <li key={p.symbol}>
                    <Link to={`/watchlist/${encodeURIComponent(p.symbol)}`} className="text-primary">
                      {p.symbol}
                    </Link>
                    {p.isin ? ` · ${p.isin}` : ""}
                    {p.ter != null ? ` · TER ${number(p.ter, 2)} %` : ""}
                    {p.exchange ? ` · ${p.exchange}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <PriceChart symbol={asset.symbol} chrome={chrome} />
      </section>

      {techEntries.length ? (
        <section className={`${panelClass(chrome)} px-5 py-5`}>
          <h3 className="text-lg font-semibold">Technische Indikatoren</h3>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            {techEntries.map(([k, v]) => (
              <div key={k}>
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="font-medium">{number(v as number, 3)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <h3 className="text-lg font-semibold">Letzte Infos</h3>
        {news.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">Keine passenden Meldungen gefunden.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {news.map((n, i) => (
              <li key={`${n.url}-${i}`}>
                <a
                  className="text-primary underline-offset-2 hover:underline"
                  href={n.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {n.title}
                </a>
                <p className="text-sm text-muted-foreground">
                  {n.source}
                  {n.published_at ? ` · ${when(n.published_at)}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
