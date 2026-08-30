import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api, type AgentLog } from "@/lib/api";
import { when } from "@/lib/format";
import { listTileClass, type Chrome } from "@/lib/platform";

export function AgentsPage() {
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [logs, setLogs] = useState<AgentLog[]>([]);

  useEffect(() => {
    api.logs(new URLSearchParams()).then(setLogs).catch(() => setLogs([]));
  }, []);

  return (
    <div className="space-y-4">
      <div className="mb-1.5 h-1.5 w-14 rounded-full bg-primary" />
      <h2 className="text-2xl font-semibold leading-snug tracking-tight">Agenten-Logs</h2>
      <p className="text-sm text-muted-foreground">
        Research, Quant, Strategist und Educator — jeder Schritt eines Laufs.
      </p>
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