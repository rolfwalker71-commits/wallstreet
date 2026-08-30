import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { HistoryPoint } from "@/lib/api";

export function Sparkline({
  points,
  rising,
}: {
  points: HistoryPoint[];
  rising?: boolean;
}) {
  if (points.length < 2) return null;
  const color = rising === false ? "rgb(var(--loss))" : "rgb(var(--gain))";
  return (
    <div className="h-12 w-full" aria-hidden>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <Area
            type="monotone"
            dataKey="close"
            stroke={color}
            fill={color}
            fillOpacity={0.18}
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}