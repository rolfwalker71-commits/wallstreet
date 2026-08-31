import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { RefreshCw } from "lucide-react";
import { AllocationPanel } from "@/components/portfolio/AllocationPanel";
import { RecommendationSparkline } from "@/components/charts/RecommendationSparkline";
import { ApplyToWalletButton } from "@/components/recommendations/ApplyToWalletButton";
import { ActionChip } from "@/components/ui/ActionChip";
import { SuggestedTickers, WatchlistButton } from "@/components/ui/WatchlistButton";
import { api, type Allocation, type Asset, type Portfolio, type Recommendation } from "@/lib/api";
import { CLASS_LABEL, money, number, recAccentClass, when } from "@/lib/format";
import { listTileClass, primaryActionClass, type Chrome } from "@/lib/platform";

export function EmpfehlungenPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [items, setItems] = useState<Recommendation[]>([]);
  const [pf, setPf] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = async (refresh = false) => {
    const [data, port] = await Promise.all([
      refresh ? api.refreshPicks() : api.picks(),
      api.portfolio().catch(() => null),
    ]);
    setItems(data);
    if (port) setPf(port);
  };

  useEffect(() => {
    setLoading(true);
    load()
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const refresh = async () => {
    setBusy(true);
    setError(null);
    try {
      await load(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Aktualisieren fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  const patchAsset = (next: Asset) => {
    setItems((prev) =>
      prev.map((item) =>
        item.asset.symbol === next.symbol ? { ...item, asset: { ...item.asset, ...next } } : item,
      ),
    );
  };

  const empty = (pf?.positions.length ?? 0) === 0;
  const allocation: Allocation | null = pf?.allocation ?? null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1.5 h-1.5 w-14 rounded-full bg-gain" />
          <h2 className="text-2xl font-semibold leading-snug tracking-tight">Empfehlungen</h2>
          <p className="text-sm text-muted-foreground">
            {empty
              ? "Leeres Depot: erster Kauf ist VWCE.DE (Welt-Aktien-UCITS, ISIN IE00BK5BQT80). Keine Einzelaktien, kein 20-Jahre-Bond zum Start."
              : "Käufe füllen die Lücke zur Zielquote. Texte sind ISIN, TER, Betrag und Stück — keine Prognose."}
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={busy || loading}
          className={`${primaryActionClass(chrome)} disabled:opacity-60`}
        >
          <RefreshCw className={`size-5 shrink-0 ${busy ? "animate-spin" : ""}`} aria-hidden />
          <span>{busy ? "Rechnet…" : "Neu berechnen"}</span>
        </button>
      </div>

      {allocation ? <AllocationPanel allocation={allocation} chrome={chrome} /> : null}

      {error ? (
        <p className="rounded-3xl bg-loss-container px-4 py-3 text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className={`${listTileClass(chrome)} px-5 py-8 text-muted-foreground`}>
          Rechnet Lücken und Stückzahlen…
        </p>
      ) : null}

      {!loading && items.length === 0 && !error ? (
        <p className={`${listTileClass(chrome)} px-5 py-8 text-muted-foreground`}>
          Keine Lücke über 1 %, oder der vorgeschlagene Betrag reicht nicht für ein Stück. Ziele im
          Depot anpassen oder Cash erhöhen.
        </p>
      ) : null}

      <ol className="space-y-3">
        {items.map((rec, index) => (
          <li
            key={rec.id}
            className={`${listTileClass(chrome)} ${recAccentClass(rec.action)} px-4 py-4`}
          >
            <Link to={`/signals/${rec.id}`} className="block">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-gain">
                    {empty && rec.asset.symbol === "VWCE.DE" ? "Startkauf" : `Lücke ${index + 1}`}
                  </p>
                  <p className="text-lg font-semibold leading-snug break-words">
                    {rec.asset.symbol} · {rec.asset.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {CLASS_LABEL[rec.asset.asset_class] ?? rec.asset.asset_class}
                    {rec.asset.isin ? ` · ${rec.asset.isin}` : ""}
                    {rec.asset.exchange ? ` · ${rec.asset.exchange}` : ""}
                    {` · ${when(rec.created_at)}`}
                  </p>
                </div>
                <ActionChip action={rec.action} />
              </div>
              {rec.proposed_qty && rec.proposed_price ? (
                <p className="mt-3 text-sm font-medium">
                  {number(rec.proposed_qty, 0)} Stück @ {money(rec.proposed_price, rec.asset.currency)}
                </p>
              ) : null}
              <div className="mt-3">
                <RecommendationSparkline symbol={rec.asset.symbol} />
              </div>
              <p className="mt-3 text-sm font-medium text-primary">Fakten</p>
              <p className="mt-1 text-sm leading-relaxed text-foreground">{rec.rationale}</p>
            </Link>
            <div className="mt-3 flex flex-wrap gap-3">
              <Link
                to={`/watchlist/${encodeURIComponent(rec.asset.symbol)}`}
                className="inline-flex min-h-11 items-center text-sm font-medium text-primary"
              >
                Dossier öffnen
              </Link>
            </div>
            <div className="mt-3 space-y-3">
              <WatchlistButton asset={rec.asset} chrome={chrome} onChanged={patchAsset} />
              {rec.suggested_symbols?.length ? (
                <SuggestedTickers
                  symbols={rec.suggested_symbols}
                  chrome={chrome}
                  exclude={[rec.asset.symbol]}
                  onAdded={patchAsset}
                />
              ) : null}
              <ApplyToWalletButton
                rec={rec}
                chrome={chrome}
                onApplied={(next) =>
                  setItems((prev) => prev.map((item) => (item.id === next.id ? next : item)))
                }
              />
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
