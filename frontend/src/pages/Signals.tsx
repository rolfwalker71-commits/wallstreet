import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { Play } from "lucide-react";
import { RecommendationSparkline } from "@/components/charts/RecommendationSparkline";
import { ApplyToWalletButton } from "@/components/recommendations/ApplyToWalletButton";
import { ActionChip } from "@/components/ui/ActionChip";
import { SuggestedTickers, WatchlistButton } from "@/components/ui/WatchlistButton";
import { api, type Asset, type Recommendation } from "@/lib/api";
import { ACTION_LABEL, CLASS_LABEL, number, pct, recAccentClass, when } from "@/lib/format";
import { listTileClass, primaryActionClass, type Chrome } from "@/lib/platform";

const FILTERS: Array<{ id: string; label: string; value?: string }> = [
  { id: "all", label: "Alle" },
  { id: "watch", label: "Watchlist" },
  { id: "discover", label: "Entdeckt" },
  { id: "stock", label: "Aktien", value: "stock" },
  { id: "etf", label: "ETFs", value: "etf" },
  { id: "fund", label: "Fonds", value: "fund" },
  { id: "bond", label: "Obligationen", value: "bond" },
  { id: "commodity", label: "Rohstoffe", value: "commodity" },
  { id: "forex", label: "Devisen", value: "forex" },
  { id: "crypto", label: "Crypto", value: "crypto" },
];

export function SignalsPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [items, setItems] = useState<Recommendation[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [llm, setLlm] = useState<{
    on: boolean;
    model?: string | null;
    mini?: string | null;
  }>({ on: false });

  const load = async (id: string) => {
    const params = new URLSearchParams({ latest: "true" });
    if (id === "watch") params.set("watched", "true");
    if (id === "discover") params.set("watched", "false");
    const cls = FILTERS.find((f) => f.id === id)?.value;
    if (cls) params.set("asset_class", cls);
    const data = await api.recommendations(params);
    setItems(data);
  };

  useEffect(() => {
    load(filter).catch((e: Error) => setError(e.message));
  }, [filter]);

  useEffect(() => {
    api
      .health()
      .then((h) =>
        setLlm({
          on: Boolean(h.llm_enabled),
          model: h.llm_model,
          mini: h.llm_mini_model,
        }),
      )
      .catch(() => undefined);
  }, []);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.runAgents();
      await load(filter);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lauf fehlgeschlagen");
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

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1.5 h-1.5 w-14 rounded-full bg-primary" />
          <h2 className="text-2xl font-semibold leading-snug tracking-tight">Signale</h2>
          <p className="text-sm text-muted-foreground">
            {llm.on
              ? `Modelle ${llm.model}${llm.mini ? ` / ${llm.mini}` : ""} nur zum Lesen von Schlagzeilen. Kauf, Halten, Verkauf kommt aus RSI-Regeln. Texte sind Zahlen und wörtliche Headlines.`
              : "Ohne OpenAI-Key: nur RSI-Regeln und gespeicherte Kurse. Key gehört in die .env im Projektroot."}
          </p>
        </div>
        <button
          type="button"
          onClick={run}
          disabled={busy}
          className={`${primaryActionClass(chrome)} disabled:opacity-60`}
        >
          <Play className="size-5 shrink-0" aria-hidden />
          <span>{busy ? "Läuft…" : "Agenten starten"}</span>
        </button>
      </div>

      <div
        className="flex h-10 min-h-10 gap-0.5 overflow-x-auto rounded-full bg-muted p-0.5"
        role="tablist"
        aria-label="Filter"
      >
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            onClick={() => setFilter(f.id)}
            className={`h-full min-h-0 shrink-0 self-stretch rounded-full px-3 text-sm leading-none ${
              filter === f.id ? "bg-primary text-on-primary" : "text-muted-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error ? (
        <p className="rounded-3xl bg-loss-container px-4 py-3 text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}

      {items.length === 0 && !error ? (
        <p className={`${listTileClass(chrome)} px-5 py-8 text-muted-foreground`}>
          Noch keine Signale. Starte die Agenten — sie begründen Kauf, Halten oder Verkauf und holen Ideen aus den News.
        </p>
      ) : null}

      <ul className="space-y-3">
        {items.map((rec) => (
          <li
            key={rec.id}
            className={`${listTileClass(chrome)} ${recAccentClass(rec.action)} px-4 py-4`}
          >
            <Link to={`/signals/${rec.id}`} className="block">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-lg font-semibold leading-snug break-words">
                    {rec.asset.symbol} · {rec.asset.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {CLASS_LABEL[rec.asset.asset_class]} · {when(rec.created_at)}
                    {rec.asset.watched ? "" : " · Entdeckt"}
                  </p>
                </div>
                <ActionChip action={rec.action} />
              </div>
              <div className="mt-3">
                <RecommendationSparkline symbol={rec.asset.symbol} />
              </div>
              {!rec.asset.watched && rec.asset.notes ? (
                <p className="mt-3 rounded-2xl bg-gain-container px-3 py-2 text-sm text-gain">
                  Idee: {rec.asset.notes}
                </p>
              ) : null}
              <p className="mt-3 text-sm font-medium text-primary">Begründung</p>
              <p className="mt-1 text-sm leading-relaxed text-foreground">{rec.rationale}</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Konfidenz {pct(Number(rec.confidence) * 100)}
                {rec.risk_reward_ratio
                  ? ` · Chance/Risiko ${number(rec.risk_reward_ratio, 2)}`
                  : ""}
                {` · ${ACTION_LABEL[rec.action]}`}
              </p>
            </Link>
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
      </ul>
    </div>
  );
}
