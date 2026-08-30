import type { Recommendation } from "@/lib/api";

export function isExecutable(rec: Recommendation) {
  return rec.status === "open" && (rec.action === "buy" || rec.action === "sell");
}