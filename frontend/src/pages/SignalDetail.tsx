import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { PriceChart } from "@/components/charts/PriceChart";
import { ApplyToWalletButton } from "@/components/recommendations/ApplyToWalletButton";
import { ActionChip } from "@/components/ui/ActionChip";
import { SuggestedTickers, WatchlistButton } from "@/components/ui/WatchlistButton";
import { api, type Recommendation } from "@/lib/api";
import { money, number, pct, recAccentClass, when } from "@/lib/format";
import { panelClass, type Chrome } from "@/lib/platform";

export function SignalDetailPage() {
  const { id } = useParams();
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.recommendation(id).then(setRec).catch((e: Error) => setError(e.message));
  }, [id]);

  if (error) return <p role="alert">{error}</p>;
  if (!rec) return <p>Lädt…</p>;

  const tech = rec.technicals || {};

  return (
    <article className="space-y-4">
      <Link to="/" className="inline-flex min-h-12 items-center text-sm text-primary">
        ← Signale
      </Link>
      <header className={`${panelClass(chrome)} ${recAccentClass(rec.action)} px-5 py-5`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-2xl font-semibold leading-snug tracking-tight break-words">
              {rec.asset.symbol} · {rec.asset.name}
            </h2>
            <p className="text-sm text-muted-foreground">
              {when(rec.created_at)}
              {rec.asset.watched ? "" : " · Noch nicht auf der Watchlist"}
            </p>
          </div>
          <ActionChip action={rec.action} />
        </div>
        {!rec.asset.watched && rec.asset.notes ? (
          <p className="mt-4 rounded-2xl bg-gain-container px-3 py-2 text-sm text-gain">
            Idee: {rec.asset.notes}
          </p>
        ) : null}
        <p className="mt-4 text-sm font-medium text-primary">Begründung</p>
        <p className="mt-1 leading-relaxed">{rec.rationale}</p>
        <p className="mt-3 text-sm text-muted-foreground">
          Konfidenz {pct(Number(rec.confidence) * 100)}
          {rec.proposed_qty
            ? ` · Vorschlag ${rec.proposed_qty} @ ${money(rec.proposed_price, rec.asset.currency)}`
            : ""}
        </p>
        <div className="mt-4 space-y-3">
          <WatchlistButton
            asset={rec.asset}
            chrome={chrome}
            onChanged={(next) => setRec({ ...rec, asset: { ...rec.asset, ...next } })}
          />
          {rec.suggested_symbols?.length ? (
            <SuggestedTickers
              symbols={rec.suggested_symbols}
              chrome={chrome}
              exclude={[rec.asset.symbol]}
            />
          ) : null}
          <ApplyToWalletButton rec={rec} chrome={chrome} onApplied={setRec} />
        </div>
      </header>

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <PriceChart symbol={rec.asset.symbol} chrome={chrome} />
      </section>

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <h3 className="text-lg font-semibold">Technische Indikatoren</h3>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          {Object.entries(tech).map(([k, v]) => (
            <div key={k}>
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="font-medium">{v == null ? "—" : number(v, 3)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <h3 className="text-lg font-semibold">News-Quellen</h3>
        <p className="mt-2 text-sm leading-relaxed">{rec.news_summary}</p>
        <ul className="mt-3 space-y-2">
          {(rec.news_sources || []).map((n, i) => (
            <li key={i}>
              <a
                className="text-primary underline-offset-2 hover:underline"
                href={String(n.url || "#")}
                target="_blank"
                rel="noreferrer"
              >
                {String(n.title || n.url)}
              </a>
              <span className="text-sm text-muted-foreground"> · {String(n.source || "")}</span>
            </li>
          ))}
        </ul>
      </section>

      {rec.glossary_terms?.length ? (
        <section className={`${panelClass(chrome)} px-5 py-5`}>
          <h3 className="text-lg font-semibold">Fachbegriffe</h3>
          <ul className="mt-3 flex flex-wrap gap-2">
            {rec.glossary_terms.map((t) => (
              <li key={t}>
                <Link
                  to={`/lexicon/${t.toLowerCase().replace(/\s+/g, "-")}`}
                  className="inline-flex min-h-11 items-center rounded-full bg-secondary px-3 py-1 text-sm text-primary"
                >
                  {t}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className={`${panelClass(chrome)} px-5 py-5`}>
        <h3 className="text-lg font-semibold">Denkprozess</h3>
        <ol className="mt-3 space-y-3">
          {rec.agent_logs.map((log) => (
            <li key={log.id} className="border-l-2 border-primary pl-3">
              <p className="text-sm font-medium capitalize">
                {log.agent_name} · {log.step}
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">{log.reasoning}</p>
            </li>
          ))}
        </ol>
      </section>
    </article>
  );
}