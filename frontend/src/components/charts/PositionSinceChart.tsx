import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type HistoryPoint } from "@/lib/api";
import { date, money, number, signedClass } from "@/lib/format";
import { type Chrome } from "@/lib/platform";

export function PositionSinceChart({
  symbol,
  currency,
  avgCost,
  quantity,
  openedAt,
  chrome,
}: {
  symbol: string;
  currency: string;
  avgCost: number;
  quantity: number;
  openedAt: string | null;
  chrome: Chrome;
}) {
  const [points, setPoints] = useState<HistoryPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .history(symbol, "2y", openedAt ?? undefined)
      .then((res) => {
        if (!cancelled) setPoints(res.points);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, openedAt]);

  const data = points.map((p) => ({
    ...p,
    label: date(p.date),
    value: p.close * quantity,
    pnl: (p.close - avgCost) * quantity,
  }));
  const last = data[data.length - 1];
  const lineColor = last && last.pnl < 0 ? "rgb(var(--loss))" : "rgb(var(--gain))";

  return (
    <div className="mt-4">
      <p className="text-sm text-muted-foreground">
        Kurs seit Kauf{openedAt ? ` (${date(openedAt)})` : ""}
        {last ? (
          <>
            {` · jetzt ${money(last.close, currency)} · Position `}
            <span className={signedClass(last.pnl)}>{money(last.pnl, currency)}</span>
          </>
        ) : null}
      </p>
      {error ? (
        <p className="mt-2 text-sm text-destructive" role="alert">
          Chart nicht verfügbar.
        </p>
      ) : null}
      {data.length >= 2 ? (
        <div className={chrome === "desktop" ? "mt-2 h-56" : "mt-2 h-48"}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="rgb(var(--border))" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12, fill: "rgb(var(--muted-foreground))" }}
                interval="preserveStartEnd"
                minTickGap={36}
              />
              <YAxis
                domain={["auto", "auto"]}
                width={56}
                tick={{ fontSize: 12, fill: "rgb(var(--muted-foreground))" }}
                tickFormatter={(v: number) => number(v, 2)}
              />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--card))",
                  border: "1px solid rgb(var(--border))",
                  borderRadius: chrome === "desktop" ? "0.375rem" : "1.25rem",
                  color: "rgb(var(--foreground))",
                }}
                formatter={(value, name) => {
                  const n = typeof value === "number" ? value : Number(value);
                  if (name === "pnl") return [money(n, currency), "Ergebnis"];
                  return [money(n, currency), "Kurs"];
                }}
              />
              <ReferenceLine
                y={avgCost}
                stroke="rgb(var(--muted-foreground))"
                strokeDasharray="4 4"
                label={{ value: "Einstand", fill: "rgb(var(--muted-foreground))", fontSize: 12 }}
              />
              <Line
                type="monotone"
                dataKey="close"
                name="close"
                stroke={lineColor}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : !error ? (
        <p className="mt-2 text-sm text-muted-foreground">Lädt Kursreihe seit Kauf…</p>
      ) : null}
    </div>
  );
}