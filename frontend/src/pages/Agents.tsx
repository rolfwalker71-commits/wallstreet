import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { NotifyToggle } from "@/components/push/NotifyToggle";
import { api, type AgentLog } from "@/lib/api";
import { number, when } from "@/lib/format";
import { listTileClass, panelClass, type Chrome } from "@/lib/platform";
import { actualCost, costBreakdown, usd } from "@/lib/pricing";

type Usage = Awaited<ReturnType<typeof api.usage>>;

function UsageCard({ chrome, usage }: { chrome: Chrome; usage: Usage }) {
  const todayRows = usage.models_today;
  const monthRows = usage.models_month?.length ? usage.models_month : usage.models_today;
  const today4o = costBreakdown(todayRows, "4o");
  const today41 = costBreakdown(todayRows, "41");
  const month4o = costBreakdown(monthRows, "4o");
  const month41 = costBreakdown(monthRows, "41");

  return (
    <section className={`${panelClass(chrome)} space-y-3 px-4 py-4`}>
      <h3 className="text-lg font-semibold">Token-Verbrauch</h3>
      <p className="text-sm text-muted-foreground">{usage.estimate}</p>
      <dl className="grid gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-sm text-muted-foreground">Heute</dt>
          <dd className="text-xl font-semibold">{number(usage.today.total_tokens, 0)}</dd>
          <p className="text-sm text-muted-foreground">
            {number(usage.today.calls, 0)} Aufrufe · {number(usage.today.prompt_tokens, 0)} in /{" "}
            {number(usage.today.completion_tokens, 0)} out
          </p>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">30 Tage</dt>
          <dd className="text-xl font-semibold">{number(usage.month.total_tokens, 0)}</dd>
          <p className="text-sm text-muted-foreground">{number(usage.month.calls, 0)} Aufrufe</p>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Läufe / Tag</dt>
          <dd className="text-xl font-semibold">{number(usage.cycles_per_day, 0)}</dd>
          <p className="text-sm text-muted-foreground">bei aktuellem Intervall</p>
        </div>
      </dl>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className={`${listTileClass(chrome)} px-4 py-3`}>
          <p className="text-sm text-muted-foreground">Kosten 4o-Preise</p>
          <p className="text-xl font-semibold">{usd(today4o.total)}</p>
          <p className="text-sm text-muted-foreground">
            Heute Input {usd(today4o.input)} · Output {usd(today4o.output)}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">30 Tage {usd(month4o.total)}</p>
        </div>
        <div className={`${listTileClass(chrome)} px-4 py-3`}>
          <p className="text-sm text-muted-foreground">Kosten 4.1-Preise</p>
          <p className="text-xl font-semibold">{usd(today41.total)}</p>
          <p className="text-sm text-muted-foreground">
            Heute Input {usd(today41.input)} · Output {usd(today41.output)}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">30 Tage {usd(month41.total)}</p>
        </div>
      </div>

      <p className="text-sm text-muted-foreground">
        Listenpreis je 1 Mio. Token: 4o $2.50 / $10 · 4o-mini $0.15 / $0.60 · 4.1 $2.00 / $8 ·
        4.1-mini $0.40 / $1.60 (Input / Output).
      </p>

      {todayRows.length ? (
        <ul className="space-y-2 text-sm">
          {todayRows.map((m) => {
            const billed = actualCost(m);
            const as4o = costBreakdown([m], "4o");
            const as41 = costBreakdown([m], "41");
            return (
              <li key={m.model}>
                <span className="font-medium">{m.model}</span>
                {": "}
                {number(m.prompt_tokens + m.completion_tokens, 0)} Token ({number(m.calls, 0)}×)
                {" · "}
                {number(m.prompt_tokens, 0)} in / {number(m.completion_tokens, 0)} out
                {" · gebucht "}
                {usd(billed.total)}
                {" · 4o "}
                {usd(as4o.total)}
                {" · 4.1 "}
                {usd(as41.total)}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Noch keine gemessenen Aufrufe in den letzten 24 h.</p>
      )}
    </section>
  );
}

export function AgentsPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [models, setModels] = useState<{ main?: string | null; mini?: string | null }>({});

  useEffect(() => {
    api.logs(new URLSearchParams()).then(setLogs).catch(() => setLogs([]));
    api.usage().then(setUsage).catch(() => setUsage(null));
    api
      .health()
      .then((h) => setModels({ main: h.llm_model, mini: h.llm_mini_model }))
      .catch(() => undefined);
  }, []);

  return (
    <div className="space-y-4">
      <div className="mb-1.5 h-1.5 w-14 rounded-full bg-primary" />
      <h2 className="text-2xl font-semibold leading-snug tracking-tight">Agenten</h2>
      <p className="text-sm text-muted-foreground">
        Laufen im Hintergrund rund um die Uhr
        {usage ? ` — alle ${usage.interval_minutes} Minuten` : ""}
        {models.main ? ` · Strategist ${models.main}` : ""}
        {models.mini ? ` · Mini ${models.mini}` : ""}.
      </p>

      <NotifyToggle chrome={chrome} />

      {usage ? (
        <UsageCard chrome={chrome} usage={usage} />
      ) : null}

      <h3 className="text-lg font-semibold">Logs</h3>
      <ul className="space-y-3">
        {logs.map((log) => (
          <li key={log.id} className={`${listTileClass(chrome)} px-4 py-4`}>
            <p className="font-medium capitalize">
              {log.agent_name} · {log.step} ·{" "}
              <span
                className={
                  log.status === "succeeded"
                    ? "text-gain"
                    : log.status === "failed"
                      ? "text-loss"
                      : "text-primary"
                }
              >
                {log.status}
              </span>
            </p>
            <p className="text-sm text-muted-foreground">{when(log.created_at)}</p>
            <p className="mt-2 text-sm leading-relaxed">{log.reasoning}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
