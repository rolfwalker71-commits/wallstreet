import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { PositionSinceChart } from "@/components/charts/PositionSinceChart";
import { QuoteStamp } from "@/components/market/QuoteStamp";
import { AllocationPanel } from "@/components/portfolio/AllocationPanel";
import { api, type Asset, type Portfolio, type Transaction } from "@/lib/api";
import { SignedMoney, SignedPct } from "@/components/ui/Signed";
import { money, number, when } from "@/lib/format";
import { fieldClass, listTileClass, panelClass, primaryActionClass, type Chrome } from "@/lib/platform";

export function WalletPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [pf, setPf] = useState<Portfolio | null>(null);
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [symbol, setSymbol] = useState("AAPL");
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [qty, setQty] = useState("1");
  const [price, setPrice] = useState("");
  const [targets, setTargets] = useState({
    stock: "60",
    bond: "20",
    commodity: "5",
    crypto: "0",
    cash: "15",
    maxSingle: "5",
  });
  const [targetBusy, setTargetBusy] = useState(false);

  const reload = () =>
    Promise.all([api.portfolio(), api.transactions()]).then(([p, t]) => {
      setPf(p);
      setTxs(t);
    });

  useEffect(() => {
    Promise.all([api.portfolio(), api.transactions(), api.assets()])
      .then(([p, t, a]) => {
        setPf(p);
        setTxs(t);
        setAssets(a.items);
        if (a.items[0]) setSymbol(a.items[0].symbol);
        setTargets({
          stock: String(Number(p.target_stock_pct ?? 60)),
          bond: String(Number(p.target_bond_pct ?? 20)),
          commodity: String(Number(p.target_commodity_pct ?? 5)),
          crypto: String(Number(p.target_crypto_pct ?? 0)),
          cash: String(Number(p.target_cash_pct ?? 15)),
          maxSingle: String(Number(p.max_single_position_pct ?? 5)),
        });
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!symbol) return;
    api
      .quote(symbol)
      .then((q) => setPrice(q.price))
      .catch(() => undefined);
  }, [symbol]);

  const submit = async () => {
    if (!pf) return;
    const qtyN = Number(qty);
    const priceN = Number(price);
    if (!Number.isFinite(qtyN) || qtyN <= 0 || !Number.isFinite(priceN) || priceN <= 0) {
      setError("Anzahl und Preis müssen grösser als 0 sein.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.trade({
        portfolio_id: pf.id,
        symbol,
        side,
        quantity: qtyN,
        price: priceN,
      });
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Buchung fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  if (!pf && !error) return <p>Lädt Depot…</p>;
  if (!pf) return <p role="alert">{error}</p>;

  const cur = pf.base_currency;
  const selected = assets.find((a) => a.symbol === symbol);

  return (
    <div className="space-y-4">
      <div className="mb-1.5 h-1.5 w-14 rounded-full bg-primary" />
      <h2 className="text-2xl font-semibold leading-snug tracking-tight">{pf.name}</h2>
      <p className="text-sm text-muted-foreground">
        {pf.is_paper ? "Paper-Trading" : "Live"} · Menge und Einstand selbst setzen.
      </p>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Eigenkapital</p>
          <p className="text-2xl font-semibold">{money(pf.equity, cur)}</p>
          <p className="text-sm text-muted-foreground">Start {money(pf.initial_capital, cur)}</p>
        </div>
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Cash</p>
          <p className="text-2xl font-semibold">{money(pf.cash_balance, cur)}</p>
        </div>
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Investiert (Einstand)</p>
          <p className="text-2xl font-semibold">{money(pf.invested_cost, cur)}</p>
          <p className="text-sm text-muted-foreground">Marktwert {money(pf.holdings_value, cur)}</p>
        </div>
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Unrealisiert</p>
          <p className="text-2xl font-semibold">
            <SignedMoney value={pf.unrealized_pnl} currency={cur} />
          </p>
        </div>
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Realisiert</p>
          <p className="text-2xl font-semibold">
            <SignedMoney value={pf.realized_pnl} currency={cur} />
          </p>
        </div>
        <div className={`${panelClass(chrome)} px-4 py-4`}>
          <p className="text-sm text-muted-foreground">Gesamtrendite</p>
          <p className="text-2xl font-semibold">
            <SignedPct value={pf.total_return_pct} />
          </p>
          <p className="text-sm text-muted-foreground">
            S&amp;P 500 <SignedPct value={pf.benchmark_return_pct} /> · vs. Benchmark{" "}
            <SignedPct value={pf.vs_benchmark_pct} />
          </p>
        </div>
      </section>

      {pf.allocation ? <AllocationPanel allocation={pf.allocation} chrome={chrome} /> : null}

      <section className={`${panelClass(chrome)} px-4 py-4`}>
        <h3 className="text-lg font-semibold">Zielquoten</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Summe 100 %. Einzelaktien-Deckel gilt nicht für den Kern-ETF (VWCE).
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          {(
            [
              ["stock", "Aktien %"],
              ["bond", "Obligationen %"],
              ["commodity", "Rohstoffe %"],
              ["crypto", "Crypto %"],
              ["cash", "Cash %"],
              ["maxSingle", "Max. Einzeltitel %"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="block">
              <span className="mb-1 block text-sm text-muted-foreground">{label}</span>
              <input
                type="number"
                inputMode="decimal"
                min="0"
                max="100"
                step="1"
                value={targets[key]}
                onChange={(e) => setTargets((prev) => ({ ...prev, [key]: e.target.value }))}
                className={fieldClass(chrome)}
              />
            </label>
          ))}
        </div>
        <button
          type="button"
          disabled={targetBusy}
          className={`mt-3 ${primaryActionClass(chrome)} disabled:opacity-60`}
          onClick={async () => {
            setTargetBusy(true);
            setError(null);
            try {
              const next = await api.setTargets({
                target_stock_pct: Number(targets.stock),
                target_bond_pct: Number(targets.bond),
                target_commodity_pct: Number(targets.commodity),
                target_crypto_pct: Number(targets.crypto),
                target_cash_pct: Number(targets.cash),
                max_single_position_pct: Number(targets.maxSingle),
              });
              setPf(next);
            } catch (e) {
              setError(e instanceof Error ? e.message : "Ziele speichern fehlgeschlagen");
            } finally {
              setTargetBusy(false);
            }
          }}
        >
          {targetBusy ? "Speichert…" : "Ziele speichern"}
        </button>
      </section>

      <section className={`${panelClass(chrome)} px-4 py-4`}>
        <h3 className="text-lg font-semibold">Position buchen</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Anzahl und den Preis, den du bezahlt hast (oder erhalten würdest).
        </p>
        <div
          className="mt-3 flex h-10 min-h-10 w-full max-w-xs gap-0.5 rounded-full bg-muted p-0.5"
          role="tablist"
          aria-label="Seite"
        >
          {(["buy", "sell"] as const).map((s) => (
            <button
              key={s}
              type="button"
              role="tab"
              aria-selected={side === s}
              onClick={() => setSide(s)}
              className={`h-full min-h-0 flex-1 self-stretch rounded-full text-sm leading-none ${
                side === s
                  ? s === "buy"
                    ? "bg-gain text-on-gain"
                    : "bg-loss text-on-loss"
                  : "text-muted-foreground"
              }`}
            >
              {s === "buy" ? "Kauf" : "Verkauf"}
            </button>
          ))}
        </div>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <label className="block">
            <span className="mb-1 block text-sm text-muted-foreground">Titel</span>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className={fieldClass(chrome)}
            >
              {assets.map((a) => (
                <option key={a.id} value={a.symbol}>
                  {a.symbol} · {a.name}
                </option>
              ))}
            </select>
          </label>
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
            <span className="mb-1 block text-sm text-muted-foreground">Preis je Stück</span>
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
        <p className="mt-2 text-sm text-muted-foreground">
          Summe{" "}
          {money(Number(qty) * Number(price) || 0, selected?.currency ?? cur)}
        </p>
        <button
          type="button"
          onClick={submit}
          disabled={busy}
          className={`mt-3 ${
            chrome === "desktop" ? "min-h-11 rounded-md px-4" : "min-h-12 rounded-full px-5"
          } font-medium disabled:opacity-60 ${
            side === "buy" ? "bg-gain text-on-gain" : "bg-loss text-on-loss"
          }`}
        >
          {busy ? "Bucht…" : "Ins Depot übernehmen"}
        </button>
      </section>

      <section>
        <h3 className="mb-2 text-lg font-semibold">Positionen</h3>
        {pf.positions.length === 0 ? (
          <p className={`${listTileClass(chrome)} px-4 py-6 text-muted-foreground`}>
            Noch keine Positionen.{" "}
            <Link to="/empfehlungen" className="text-primary underline-offset-2 hover:underline">
              Startkauf VWCE.DE unter Empfehlungen
            </Link>{" "}
            oder hier manuell buchen.
          </p>
        ) : (
          <ul className="space-y-3">
            {pf.positions.map((p) => (
              <li key={p.id} className={`${listTileClass(chrome)} px-4 py-4`}>
                <p className="font-semibold leading-snug break-words">
                  {p.asset.symbol} · {p.asset.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {number(p.quantity, Number(p.quantity) < 1 ? 4 : 2)} Stück · Einstand{" "}
                  {money(p.avg_cost, p.asset.currency)} · Kosten {money(p.cost_basis, p.asset.currency)}
                </p>
                <p className="mt-1">
                  Jetzt {money(p.current_price, p.asset.currency)} · Wert{" "}
                  {money(p.market_value, p.asset.currency)} ·{" "}
                  <SignedMoney value={p.unrealized_pnl} currency={p.asset.currency} />{" "}
                  (<SignedPct value={p.unrealized_pnl_pct} />)
                </p>
                <QuoteStamp
                  asOf={p.quote_as_of ?? p.asset.last_price_at}
                  delayed={p.delayed}
                  sessionLabel={p.session_label}
                  marketOpen={p.market_open}
                  freshnessLabel={p.freshness_label}
                  asOfPrecision={p.as_of_precision}
                />
                <PositionSinceChart
                  symbol={p.asset.symbol}
                  currency={p.asset.currency}
                  avgCost={Number(p.avg_cost)}
                  quantity={Number(p.quantity)}
                  openedAt={p.opened_at}
                  chrome={chrome}
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3 className="mb-2 text-lg font-semibold">Transaktionen</h3>
        <ul className="space-y-3">
          {txs.map((t) => (
            <li key={t.id} className={`${listTileClass(chrome)} px-4 py-3`}>
              <p className="font-medium leading-snug">
                {t.side === "buy" ? "Kauf" : t.side === "sell" ? "Verkauf" : t.side}{" "}
                {t.asset?.symbol ?? "CASH"} · {number(t.quantity, 4)} @ {money(t.price, t.currency)}
              </p>
              <p className="text-sm text-muted-foreground">
                {when(t.executed_at)}
                {t.realized_pnl ? (
                  <>
                    {" · realisiert "}
                    <SignedMoney value={t.realized_pnl} currency={t.currency} />
                  </>
                ) : (
                  ""
                )}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}