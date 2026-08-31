import { useEffect, useState } from "react";
import {
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartRangeTabs } from "@/components/charts/ChartRangeTabs";
import { PeakDateLabel, PeakDot } from "@/components/charts/PeakDateLabel";
import {
  isIntradayPeriod,
  peakIndices,
  showPeakDates,
  type ChartPeriodId,
} from "@/components/charts/periods";
import { api, type HistoryPoint } from "@/lib/api";
import { date, dateShort, number, time } from "@/lib/format";
import { type Chrome } from "@/lib/platform";

export function PriceChart({
  symbol,
  chrome,
}: {
  symbol: string;
  chrome: Chrome;
}) {
  const [period, setPeriod] = useState<ChartPeriodId>("6mo");
  const [points, setPoints] = useState<HistoryPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setPoints([]);
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

  const axisLabel = (iso: string) => (period === "1d" ? time(iso) : date(iso));
  const peaks = new Set(showPeakDates(period) ? peakIndices(points.map((p) => p.close)) : []);
  const data = points.map((p, i) => ({
    ...p,
    label: axisLabel(p.date),
    peakLabel: peaks.has(i) ? dateShort(p.date) : "",
  }));
  const rising = data.length >= 2 && data[data.length - 1].close >= data[0].close;
  const closeColor = rising ? "rgb(var(--gain))" : "rgb(var(--loss))";
  const showSma = !isIntradayPeriod(period);

  return (
    <div>
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h3 className="text-lg font-semibold leading-snug">Kursverlauf {symbol}</h3>
        <ChartRangeTabs period={period} onChange={setPeriod} chrome={chrome} />
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          Chart nicht verfügbar.
        </p>
      ) : null}
      {data.length < 2 && !error ? (
        <p className="text-sm text-muted-foreground">
          {period === "1d"
            ? "Keine Intraday-Daten (Wochenende, Feiertag oder noch keine Kurse)."
            : "Lädt Kursreihe…"}
        </p>
      ) : null}
      {data.length >= 2 ? (
        <div className={chrome === "desktop" ? "h-72" : "h-56"}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: showPeakDates(period) ? 22 : 8, right: 12, left: 0, bottom: 0 }}>
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
                type="linear"
                dataKey="close"
                name="Schluss"
                stroke={closeColor}
                strokeWidth={2}
                dot={PeakDot}
                isAnimationActive={false}
              >
                {showPeakDates(period) ? <LabelList dataKey="peakLabel" content={PeakDateLabel} /> : null}
              </Line>
              {showSma ? (
                <Line
                  type="linear"
                  dataKey="sma_20"
                  name="SMA 20"
                  stroke="rgb(var(--muted-foreground))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              ) : null}
              {showSma ? (
                <Line
                  type="linear"
                  dataKey="sma_50"
                  name="SMA 50"
                  stroke="rgb(var(--destructive))"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls
                  isAnimationActive={false}
                />
              ) : null}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
