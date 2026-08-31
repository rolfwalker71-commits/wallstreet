import { CHART_PERIODS, type ChartPeriodId } from "@/components/charts/periods";
import { type Chrome } from "@/lib/platform";

export function ChartRangeTabs({
  period,
  onChange,
  chrome,
}: {
  period: ChartPeriodId;
  onChange: (id: ChartPeriodId) => void;
  chrome: Chrome;
}) {
  const desktop = chrome === "desktop";
  return (
    <div
      className={
        desktop
          ? "flex flex-wrap gap-0.5 rounded-md bg-muted p-0.5"
          : "flex flex-wrap gap-1 rounded-3xl bg-muted p-1"
      }
      role="tablist"
      aria-label="Zeitraum"
    >
      {CHART_PERIODS.map((p) => {
        const active = period === p.id;
        return (
          <button
            key={p.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(p.id)}
            className={[
              "min-h-10 shrink-0 px-3 text-sm leading-none",
              desktop ? "rounded-sm" : "rounded-full",
              active
                ? desktop
                  ? "bg-primary/10 text-primary"
                  : "bg-primary text-on-primary"
                : "text-muted-foreground",
            ].join(" ")}
          >
            {p.label}
          </button>
        );
      })}
    </div>
  );
}
