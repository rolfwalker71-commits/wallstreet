import { useEffect, useState } from "react";
import { api, type Asset, type TitleSearchHit } from "@/lib/api";
import { CLASS_LABEL } from "@/lib/format";
import { fieldClass, listTileClass, type Chrome } from "@/lib/platform";

export function WatchlistSearch({
  chrome,
  onAdded,
}: {
  chrome: Chrome;
  onAdded: (asset: Asset) => void;
}) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<TitleSearchHit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState("");

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setHits([]);
      setSearching(false);
      setError(null);
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setSearching(true);
      setError(null);
      api
        .searchTitles(q)
        .then((rows) => {
          if (!cancelled) {
            setHits(rows);
            setSubmitted(q);
          }
        })
        .catch((e: Error) => {
          if (!cancelled) setError(e.message);
        })
        .finally(() => {
          if (!cancelled) setSearching(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [query]);

  const runNow = () => {
    const q = query.trim();
    if (q.length < 2) return;
    setSearching(true);
    setError(null);
    api
      .searchTitles(q)
      .then((rows) => {
        setHits(rows);
        setSubmitted(q);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSearching(false));
  };

  const add = async (hit: TitleSearchHit) => {
    setAdding(hit.symbol);
    setError(null);
    try {
      const asset = await api.addAsset(hit.symbol, true);
      setHits((prev) =>
        prev.map((row) =>
          row.symbol === hit.symbol ? { ...row, watched: true, in_library: true } : row,
        ),
      );
      onAdded(asset);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Titel nicht gefunden");
    } finally {
      setAdding(null);
    }
  };

  const btn =
    chrome === "desktop"
      ? "min-h-11 rounded-md px-4"
      : "min-h-12 rounded-full px-5";

  return (
    <div className="space-y-3">
      <form
        className={`${listTileClass(chrome)} flex flex-wrap items-end gap-3 px-4 py-4`}
        onSubmit={(e) => {
          e.preventDefault();
          runNow();
        }}
      >
        <label className="min-w-[10rem] flex-1">
          <span className="mb-1 block text-sm text-muted-foreground">Titel suchen</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Name oder Symbol, z. B. Dätwyler"
            className={fieldClass(chrome)}
            autoComplete="off"
            spellCheck={false}
            aria-describedby="title-search-hint"
          />
        </label>
        <button
          type="submit"
          disabled={searching || query.trim().length < 2}
          className={`${btn} bg-primary font-medium text-on-primary disabled:opacity-60`}
        >
          {searching ? "Sucht…" : "Suchen"}
        </button>
      </form>
      <p id="title-search-hint" className="text-sm text-muted-foreground">
        Firma, ETF-Name oder Ticker. Treffer einzeln auf die Watchlist nehmen.
      </p>
      {error ? (
        <p className="rounded-3xl bg-loss-container px-4 py-3 text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
      {query.trim().length >= 2 && searching && hits.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sucht Titel…</p>
      ) : null}
      {!searching && submitted && hits.length === 0 && query.trim().length >= 2 ? (
        <p className={`${listTileClass(chrome)} px-4 py-4 text-sm text-muted-foreground`}>
          Keine Treffer für «{submitted}». Anderen Namen oder das Ticker-Symbol versuchen.
        </p>
      ) : null}
      {hits.length > 0 ? (
        <ul className="space-y-2" aria-label="Suchergebnisse">
          {hits.map((hit) => (
            <li
              key={hit.symbol}
              className={`${listTileClass(chrome)} flex flex-wrap items-center justify-between gap-3 px-4 py-3`}
            >
              <div className="min-w-0 flex-1">
                <p className="font-semibold leading-snug break-words">
                  {hit.symbol} · {hit.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {hit.exchange_label || hit.exchange || "—"}
                  {" · "}
                  {CLASS_LABEL[hit.asset_class] ?? hit.asset_class}
                  {hit.swiss_buyable ? "" : " · In der CH oft nicht kaufbar"}
                </p>
              </div>
              <button
                type="button"
                disabled={hit.watched || adding === hit.symbol}
                onClick={() => add(hit)}
                className={`${btn} shrink-0 bg-gain font-medium text-on-gain disabled:opacity-70`}
              >
                {hit.watched
                  ? "Auf der Watchlist"
                  : adding === hit.symbol
                    ? "Legt an…"
                    : "Zur Watchlist"}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
