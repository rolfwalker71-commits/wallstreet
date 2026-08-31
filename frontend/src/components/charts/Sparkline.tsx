import { Area, AreaChart, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { PeakDateLabel, PeakDot, peakCaption } from "@/components/charts/PeakDateLabel";
import { peakIndices } from "@/components/charts/periods";
import type { HistoryPoint } from "@/lib/api";
import { date, number } from "@/lib/format";

export function Sparkline({
  points,
  rising,
}: {
  points: HistoryPoint[];
  rising?: boolean;
}) {
  if (points.length < 2) return null;
  const color = rising === false ? "rgb(var(--loss))" : "rgb(var(--gain))";
  const peaks = new Set(peakIndices(points.map((p) => p.close), 5));
  const data = points.map((p, i) => ({
    ...p,
    label: date(p.date),
    peakLabel: peaks.has(i) ? peakCaption(p.date, p.close) : "",
  }));
  const tick = { fontSize: 12, fill: "rgb(var(--muted-foreground))" };
  const axis = { stroke: "rgb(var(--border))" };

  return (
    <div className="h-52 w-full" aria-label="Kursverlauf mit Achsen">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 36, right: 12, left: 0, bottom: 2 }}>
          <XAxis
            dataKey="label"
            tick={tick}
            interval="preserveStartEnd"
            minTickGap={36}
            axisLine={axis}
            tickLine={axis}
            tickMargin={6}
          />
          <YAxis
            width={52}
            domain={["auto", "auto"]}
            tick={tick}
            tickFormatter={(v: number) => number(v, 2)}
            axisLine={axis}
            tickLine={axis}
            tickMargin={4}
          />
          <Area
            type="linear"
            dataKey="close"
            stroke={color}
            fill={color}
            fillOpacity={0.18}
            strokeWidth={2}
            dot={PeakDot}
            isAnimationActive={false}
          >
            <LabelList dataKey="peakLabel" content={PeakDateLabel} />
          </Area>
          <CartesianGrid
            stroke="rgb(var(--muted-foreground))"
            strokeWidth={1}
            strokeOpacity={0.18}
            vertical
            horizontal
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
