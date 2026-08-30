import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { WatchlistButton } from "@/components/ui/WatchlistButton";
import { api, type Asset, type Quote } from "@/lib/api";
import { CLASS_LABEL, money, pct, signedClass } from "@/lib/format";
import { fieldClass, listTileClass, type Chrome } from "@/lib/platform";

function QuoteChange({ value }: { value: number | null | undefined }) {
  const n = value ?? null;
  if (n === null) return <span className="text-muted-foreground">—</span>;
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-sm font-medium ${
      n > 0
        ? "bg-gain-container text-gain"
        : n < 0
          ? "bg-loss-container text-loss"
          : "bg-muted text-muted-foreground"
    }`}>
      {pct(n)}
    </span>
  );
}

export function MarketsPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("");
  const [busy, setBusy] = useState(false);
  const [scope, setScope] = useState<"watch" | "discover" | "all">("watch");

  const loadQuotes = async (items: Asset[]) => {
    const entries = await Promise.all(
      items.map(async (a) => {
        try {
          return [a.symbol, await api.quote(a.symbol)] as const;
        } catch {
          return [a.symbol, null] as const;
        }
      }),
    );
    const map: Record<string, Quote> = {};
    for (const [sym, q] of entries) {
      if (q) map[sym] = q;
    }
    setQuotes((prev) => ({ ...prev, ...map }));
  };

  const load = async () => {
    const res = await api.assets();
    setAssets(res.items);
    await loadQuotes(res.items);
  };

  useEffect(() => {
    load().catch((e: Error) => setError(e.message));
  }, []);

  const add = async () => {
    const raw = symbol.trim().toUpperCase();
    if (!raw) return;
    setBusy(true);
    setError(null);
    try {
      const asset = await api.addAsset(raw, true);
      setSymbol("");
      setAssets((prev) => {
        const rest = prev.filter((a) => a.symbol !== asset.symbol);
        return [asset, ...rest];
      });
      await loadQuotes([asset]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Titel nicht gefunden");
    } finally {
      setBusy(false);
    }
  };

  const visible = assets.filter((a) => {
    if (scope === "watch") return a.watched;
    if (scope === "discover") return !a.watched;
    return true;
  });
  const watchedCount = assets.filter((a) => a.watched).length;

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1.5 h-1.5 w-14 rounded-full bg-gain" />
        <h2 className="text-2xl font-semibold leading-snug tracking-tight">Märkte</h2>
        <p className="text-sm text-muted-foreground">
          {watchedCount} Titel auf der Watchlist. Entdeckte Empfehlungen kannst du hier übernehmen.
        </p>
      </div>

      {error ? (
        <p className="rounded-3xl bg-loss-container px-4 py-3 text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}

      <form
        className={`${listTileClass(chrome)} flex flex-wrap items-end gap-3 px-4 py-4`}
        onSubmit={(e) => {
          e.preventDefault();
          add();
        }}
      >
        <label className="min-w-[10rem] flex-1">
          <span className="mb-1 block text-sm text-muted-foreground">Titel zur Watchlist</span>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="z. B. TSLA"
            className={fieldClass(chrome)}
            autoCapitalize="characters"
          />
        </label>
        <button
          type="submit"
          disabled={busy || !symbol.trim()}
          className={`${
            chrome === "desktop" ? "min-h-11 rounded-md px-4" : "min-h-12 rounded-full px-5"
          } bg-gain font-medium text-on-gain disabled:opacity-60`}
        >
          {busy ? "Sucht…" : "Hinzufügen"}
        </button>
      </form>

      <div
        className="flex h-10 min-h-10 gap-0.5 overflow-x-auto rounded-full bg-muted p-0.5"
        role="tablist"
        aria-label="Liste"
      >
        {(
          [
            ["watch", "Watchlist"],
            ["discover", "Entdeckt"],
            ["all", "Alle"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={scope === id}
            onClick={() => setScope(id)}
            className={`h-full min-h-0 flex-1 self-stretch rounded-full px-3 text-sm leading-none ${
              scope === id ? "bg-primary text-on-primary" : "text-muted-foreground"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className={`${listTileClass(chrome)} px-5 py-8 text-muted-foreground`}>
          {scope === "discover"
            ? "Noch keine entdeckten Titel. Starte die Agenten — sie scannen News ausserhalb der Watchlist."
            : "Watchlist ist leer. Füge oben ein Symbol hinzu."}
        </p>
      ) : null}

      {chrome === "desktop" ? (
        <div className="overflow-x-auto rounded-md bg-card ring-1 ring-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Symbol</th>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Klasse</th>
                <th className="px-3 py-2 font-medium">Kurs</th>
                <th className="px-3 py-2 font-medium">24h</th>
                <th className="px-3 py-2 font-medium">Watchlist</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((a) => (
                <tr key={a.id} className="border-t border-border">
                  <td className="px-3 py-2 font-medium">{a.symbol}</td>
                  <td className="px-3 py-2">{a.name}</td>
                  <td className="px-3 py-2">{CLASS_LABEL[a.asset_class]}</td>
                  <td className={`px-3 py-2 ${signedClass(quotes[a.symbol]?.change_pct)}`}>
                    {money(quotes[a.symbol]?.price ?? a.last_price, a.currency)}
                  </td>
                  <td className="px-3 py-2">
                    <QuoteChange value={quotes[a.symbol]?.change_pct} />
                  </td>
                  <td className="px-3 py-2">
                    <WatchlistButton
                      asset={a}
                      chrome={chrome}
                      onChanged={(next) =>
                        setAssets((prev) => prev.map((item) => (item.id === next.id ? next : item)))
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <ul className="space-y-3">
          {visible.map((a) => {
            const change = quotes[a.symbol]?.change_pct;
            return (
              <li
                key={a.id}
                className={`${listTileClass(chrome)} ${
                  change != null && change < 0
                    ? "border-l-4 border-loss"
                    : change != null && change > 0
                      ? "border-l-4 border-gain"
                      : "border-l-4 border-primary"
                } px-4 py-4`}
              >
                <p className="text-lg font-semibold leading-snug break-words">
                  {a.symbol} · {a.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {CLASS_LABEL[a.asset_class]}
                  {a.watched ? "" : " · Entdeckt"}
                </p>
                <p className={`mt-2 text-xl font-medium ${signedClass(change)}`}>
                  {money(quotes[a.symbol]?.price ?? a.last_price, a.currency)}
                </p>
                <div className="mt-1">
                  <QuoteChange value={change} />
                </div>
                <div className="mt-3">
                  <WatchlistButton
                    asset={a}
                    chrome={chrome}
                    onChanged={(next) =>
                      setAssets((prev) => prev.map((item) => (item.id === next.id ? next : item)))
                    }
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
