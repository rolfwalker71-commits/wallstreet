import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type HistoryPoint } from "@/lib/api";
import { date, number } from "@/lib/format";
import { type Chrome } from "@/lib/platform";

const PERIODS = [
  { id: "1mo", label: "1M" },
  { id: "3mo", label: "3M" },
  { id: "6mo", label: "6M" },
  { id: "1y", label: "1J" },
] as const;

export function PriceChart({
  symbol,
  chrome,
}: {
  symbol: string;
  chrome: Chrome;
}) {
  const [period, setPeriod] = useState<(typeof PERIODS)[number]["id"]>("6mo");
  const [points, setPoints] = useState<HistoryPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    api
      .history(symbol, period)
      .then((res) => {
        if (!cancelled) setPoints(res.points);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, period]);

  const data = points.map((p) => ({
    ...p,
    label: date(p.date),
  }));
  const rising = data.length >= 2 && data[data.length - 1].close >= data[0].close;
  const closeColor = rising ? "rgb(var(--gain))" : "rgb(var(--loss))";

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold leading-snug">Kursverlauf {symbol}</h3>
        <div
          className="flex h-10 min-h-10 min-w-0 gap-0.5 overflow-x-auto rounded-full bg-muted p-0.5"
          role="tablist"
          aria-label="Zeitraum"
        >
          {PERIODS.map((p) => (
            <button
              key={p.id}
              type="button"
              role="tab"
              aria-selected={period === p.id}
              onClick={() => setPeriod(p.id)}
              className={`h-full min-h-0 shrink-0 self-stretch rounded-full px-3 text-sm leading-none ${
                period === p.id ? "bg-primary text-on-primary" : "text-muted-foreground"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          Chart nicht verfügbar.
        </p>
      ) : null}
      {data.length < 2 && !error ? (
        <p className="text-sm text-muted-foreground">Lädt Kursreihe…</p>
      ) : null}
      {data.length >= 2 ? (
        <div className={chrome === "desktop" ? "h-72" : "h-56"}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="rgb(var(--border))" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12, fill: "rgb(var(--muted-foreground))" }}
                interval="preserveStartEnd"
                minTickGap={28}
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
                labelStyle={{ fontWeight: 600 }}
                formatter={(value) => number(typeof value === "number" ? value : Number(value), 2)}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="close"
                name="Schluss"
                stroke={closeColor}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="sma_20"
                name="SMA 20"
                stroke="rgb(var(--muted-foreground))"
                strokeWidth={1.5}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="sma_50"
                name="SMA 50"
                stroke="rgb(var(--destructive))"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}