import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Wallet } from "lucide-react";
import { api, type Recommendation } from "@/lib/api";
import { ACTION_LABEL, money, number } from "@/lib/format";
import { fieldClass, type Chrome } from "@/lib/platform";
import { isExecutable } from "@/lib/recommendation";

export function ApplyToWalletButton({
  rec,
  chrome,
  onApplied,
}: {
  rec: Recommendation;
  chrome: Chrome;
  onApplied?: (next: Recommendation) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(rec.status === "executed");
  const [error, setError] = useState<string | null>(null);
  const [qty, setQty] = useState(rec.proposed_qty ?? "1");
  const [price, setPrice] = useState(rec.proposed_price ?? "");

  useEffect(() => {
    if (price) return;
    api
      .quote(rec.asset.symbol)
      .then((q) => setPrice(q.price))
      .catch(() => undefined);
  }, [rec.asset.symbol, price]);

  const shape =
    chrome === "desktop"
      ? "min-h-11 rounded-md px-4 text-sm"
      : "min-h-12 rounded-full px-5 text-base";

  if (done || rec.status === "executed") {
    return (
      <p className="text-sm text-muted-foreground">
        Im Paper-Depot.{" "}
        <Link to="/wallet" className="text-primary underline-offset-2 hover:underline">
          Zum Depot
        </Link>
      </p>
    );
  }

  if (!isExecutable(rec)) {
    return <p className="text-sm text-muted-foreground">Halten — kein Trade ins Depot.</p>;
  }

  const qtyN = Number(qty);
  const priceN = Number(price);
  const total = Number.isFinite(qtyN) && Number.isFinite(priceN) ? qtyN * priceN : null;

  const apply = async () => {
    if (!Number.isFinite(qtyN) || qtyN <= 0) {
      setError("Menge muss grösser als 0 sein.");
      return;
    }
    if (!Number.isFinite(priceN) || priceN <= 0) {
      setError("Kaufpreis muss grösser als 0 sein.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.executeRecommendation(rec.id, { quantity: qtyN, price: priceN });
      setDone(true);
      onApplied?.({ ...rec, status: "executed" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trade fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-sm text-muted-foreground">Anzahl</span>
          <input
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            className={fieldClass(chrome)}
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-muted-foreground">
            {rec.action === "sell" ? "Verkaufspreis je Stück" : "Kaufpreis je Stück"}
          </span>
          <input
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className={fieldClass(chrome)}
          />
        </label>
      </div>
      {total != null ? (
        <p className="text-sm text-muted-foreground">
          Summe {money(total, rec.asset.currency)} · {number(qtyN, qtyN < 1 ? 4 : 2)} Stück
        </p>
      ) : null}
      <button
        type="button"
        onClick={apply}
        disabled={busy}
        className={`${shape} inline-flex w-full items-center justify-center gap-2 font-medium disabled:opacity-60 sm:w-auto ${
          rec.action === "sell" ? "bg-loss text-on-loss" : "bg-gain text-on-gain"
        }`}
      >
        <Wallet className="size-5" aria-hidden />
        {busy ? "Bucht…" : `${ACTION_LABEL[rec.action]} ins Depot`}
      </button>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}