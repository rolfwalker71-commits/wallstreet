import { Area, AreaChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
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
  const data = points.map((p) => ({ ...p, label: date(p.date) }));
  const tick = { fontSize: 12, fill: "rgb(var(--muted-foreground))" };
  const axis = { stroke: "rgb(var(--border))" };

  return (
    <div className="h-40 w-full" aria-label="Kursverlauf mit Achsen">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 2 }}>
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
            type="monotone"
            dataKey="close"
            stroke={color}
            fill={color}
            fillOpacity={0.18}
            strokeWidth={2}
            isAnimationActive={false}
          />
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
