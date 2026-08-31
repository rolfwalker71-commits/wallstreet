import { money, number } from "@/lib/format";
import type { Allocation } from "@/lib/api";
import { panelClass, type Chrome } from "@/lib/platform";

export function AllocationPanel({
  allocation,
  chrome,
}: {
  allocation: Allocation;
  chrome: Chrome;
}) {
  return (
    <section className={`${panelClass(chrome)} px-4 py-4`}>
      <h3 className="text-lg font-semibold">Ziel vs. Bestand</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Quoten am Eigenkapital {money(allocation.equity, allocation.currency)}. Lücke positiv =
        unter der Zielquote.
      </p>
      <ul className="mt-3 space-y-3">
        {allocation.sleeves.map((s) => (
          <li key={s.sleeve}>
            <div className="flex flex-wrap justify-between gap-2 text-sm">
              <span className="font-medium">{s.label}</span>
              <span className="text-muted-foreground">
                Ist {number(s.current_pct, 1)} % · Ziel {number(s.target_pct, 1)} % · Lücke{" "}
                {number(s.gap_pct, 1)} % ({money(s.gap_value, allocation.currency)})
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-primary"
                style={{ width: `${Math.min(100, Math.max(0, s.current_pct))}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
