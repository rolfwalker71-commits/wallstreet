export const CHART_PERIODS = [
  { id: "1d", label: "Heute" },
  { id: "5d", label: "Woche" },
  { id: "1mo", label: "Monat" },
  { id: "3mo", label: "Quartal" },
  { id: "6mo", label: "Halbjahr" },
  { id: "1y", label: "Jahr" },
  { id: "5y", label: "5 Jahre" },
] as const;

export type ChartPeriodId = (typeof CHART_PERIODS)[number]["id"];

export function isIntradayPeriod(period: ChartPeriodId) {
  return period === "1d" || period === "5d";
}

export function showPeakDates(period: ChartPeriodId) {
  return period !== "1d";
}

/** Local maxima, spaced so labels do not pile up. */
export function peakIndices(values: number[], maxPeaks = 6): number[] {
  const n = values.length;
  if (n < 5) return [];
  const minSep = Math.max(2, Math.floor(n / (maxPeaks * 2)));
  const candidates: { i: number; v: number }[] = [];
  for (let i = 1; i < n - 1; i++) {
    if (values[i] > values[i - 1] && values[i] >= values[i + 1]) {
      candidates.push({ i, v: values[i] });
    }
  }
  candidates.sort((a, b) => b.v - a.v);
  const picked: number[] = [];
  for (const c of candidates) {
    if (picked.some((p) => Math.abs(p - c.i) < minSep)) continue;
    picked.push(c.i);
    if (picked.length >= maxPeaks) break;
  }
  return picked.sort((a, b) => a - b);
}
