import { useEffect, useState } from "react";
import { api, type HistoryPoint } from "@/lib/api";
import { Sparkline } from "@/components/charts/Sparkline";

const cache = new Map<string, HistoryPoint[]>();

export function RecommendationSparkline({ symbol }: { symbol: string }) {
  const [points, setPoints] = useState<HistoryPoint[]>(cache.get(symbol) ?? []);

  useEffect(() => {
    if (cache.has(symbol)) {
      setPoints(cache.get(symbol) ?? []);
      return;
    }
    let cancelled = false;
    api
      .history(symbol, "3mo")
      .then((res) => {
        cache.set(symbol, res.points);
        if (!cancelled) setPoints(res.points);
      })
      .catch(() => {
        if (!cancelled) setPoints([]);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  if (points.length < 2) return null;
  const rising = points[points.length - 1].close >= points[0].close;
  return (
    <div>
      <Sparkline points={points} rising={rising} />
      <p className="mt-1 text-sm text-muted-foreground">X: Datum · Y: Kurs · 3 Monate</p>
    </div>
  );
}