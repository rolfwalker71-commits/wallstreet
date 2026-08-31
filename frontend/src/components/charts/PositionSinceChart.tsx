import { useEffect, useState } from "react";
import {
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartRangeTabs } from "@/components/charts/ChartRangeTabs";
import { PeakDateLabel, PeakDot } from "@/components/charts/PeakDateLabel";
import { peakIndices, showPeakDates, type ChartPeriodId } from "@/components/charts/periods";
import { api, type HistoryPoint } from "@/lib/api";
import { SignedMoney } from "@/components/ui/Signed";
import { date, dateShort, money, number, time } from "@/lib/format";
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
  const [period, setPeriod] = useState<ChartPeriodId>("1mo");
  const [points, setPoints] = useState<HistoryPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPoints([]);
    api
      .history(symbol, period, openedAt ?? undefined)
      .then((res) => {
        if (!cancelled) setPoints(res.points);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, openedAt, period]);

  const axisLabel = (iso: string) => (period === "1d" ? time(iso) : date(iso));
  const peaks = new Set(showPeakDates(period) ? peakIndices(points.map((p) => p.close)) : []);
  const data = points.map((p, i) => ({
    ...p,
    label: axisLabel(p.date),
    peakLabel: peaks.has(i) ? dateShort(p.date) : "",
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
            <SignedMoney value={last.pnl} currency={currency} />
          </>
        ) : null}
      </p>
      <div className="mt-3">
        <ChartRangeTabs period={period} onChange={setPeriod} chrome={chrome} />
      </div>
      {error ? (
        <p className="mt-2 text-sm text-destructive" role="alert">
          Chart nicht verfügbar.
        </p>
      ) : null}
      {data.length >= 2 ? (
        <div className={chrome === "desktop" ? "mt-2 h-56" : "mt-2 h-48"}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: showPeakDates(period) ? 22 : 8, right: 12, left: 0, bottom: 0 }}>
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
                  if (name === "pnl") return [money(n, currency, { signed: true }), "Ergebnis"];
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
                type="linear"
                dataKey="close"
                name="close"
                stroke={lineColor}
                strokeWidth={2}
                dot={PeakDot}
                isAnimationActive={false}
              >
                {showPeakDates(period) ? <LabelList dataKey="peakLabel" content={PeakDateLabel} /> : null}
              </Line>
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : loading ? (
        <p className="mt-2 text-sm text-muted-foreground">Lädt Kursreihe…</p>
      ) : !error ? (
        <p className="mt-2 text-sm text-muted-foreground">
          {period === "1d"
            ? "Keine Intraday-Daten (Wochenende, Feiertag oder noch keine Kurse)."
            : "Noch keine Handelstage in diesem Zeitraum. Die Kurve erscheint am nächsten Börsentag."}
        </p>
      ) : null}
    </div>
  );
}
