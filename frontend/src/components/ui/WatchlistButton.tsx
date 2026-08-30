import { useState, type MouseEvent } from "react";
import { Eye, EyeOff, Star } from "lucide-react";
import { api, type Asset } from "@/lib/api";
import { type Chrome } from "@/lib/platform";

export function WatchlistButton({
  asset,
  chrome,
  compact,
  onChanged,
}: {
  asset: Asset;
  chrome: Chrome;
  compact?: boolean;
  onChanged?: (next: Asset) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shape =
    chrome === "desktop"
      ? "min-h-11 rounded-md px-3 text-sm"
      : "min-h-12 rounded-full px-4 text-sm";

  const toggle = async (event?: MouseEvent) => {
    event?.preventDefault();
    event?.stopPropagation();
    setBusy(true);
    setError(null);
    try {
      const next = await api.setWatched(asset.symbol, !asset.watched);
      onChanged?.(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Watchlist fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={toggle}
        disabled={busy}
        className={`${shape} inline-flex items-center justify-center gap-2 font-medium disabled:opacity-60 ${
          asset.watched
            ? "bg-secondary text-primary"
            : "bg-gain text-on-gain"
        }`}
      >
        {asset.watched ? (
          compact ? <EyeOff className="size-4" aria-hidden /> : <Star className="size-4" aria-hidden />
        ) : (
          <Eye className="size-4" aria-hidden />
        )}
        {asset.watched ? "Von Watchlist nehmen" : "Zur Watchlist"}
      </button>
      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function SuggestedTickers({
  symbols,
  chrome,
  exclude,
  onAdded,
}: {
  symbols: string[];
  chrome: Chrome;
  exclude?: string[];
  onAdded?: (asset: Asset) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [done, setDone] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const skip = new Set((exclude ?? []).map((s) => s.toUpperCase()));
  const unique = [...new Set(symbols.map((s) => s.toUpperCase()))].filter((s) => !skip.has(s));

  if (unique.length === 0) return null;

  const add = async (symbol: string) => {
    setBusy(symbol);
    setError(null);
    try {
      const asset = await api.addAsset(symbol, true);
      setDone((prev) => [...prev, symbol]);
      onAdded?.(asset);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Titel nicht gefunden");
    } finally {
      setBusy(null);
    }
  };

  const chip =
    chrome === "desktop" ? "rounded-md px-3 py-1.5 text-sm" : "rounded-full px-3 py-1.5 text-sm";

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-primary">Interessante Titel in dieser Empfehlung</p>
      <ul className="flex flex-wrap gap-2">
        {unique.map((symbol) => {
          const added = done.includes(symbol);
          return (
            <li key={symbol}>
              <button
                type="button"
                disabled={busy === symbol || added}
                onClick={() => add(symbol)}
                className={`${chip} bg-gain-container text-gain disabled:opacity-70`}
              >
                {added ? `${symbol} · Watchlist` : busy === symbol ? `${symbol}…` : `${symbol} merken`}
              </button>
            </li>
          );
        })}
      </ul>
      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
