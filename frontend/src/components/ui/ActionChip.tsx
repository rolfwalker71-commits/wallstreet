import { ACTION_LABEL } from "@/lib/format";

export function ActionChip({ action }: { action: string }) {
  const tone =
    action === "buy"
      ? "bg-gain text-on-gain"
      : action === "sell"
        ? "bg-loss text-on-loss"
        : "bg-secondary text-primary";
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${tone}`}>
      {ACTION_LABEL[action] ?? action}
    </span>
  );
}
