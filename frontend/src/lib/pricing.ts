/** OpenAI-Listenpreise in USD je 1 Mio. Token (Input / Output), Stand 2026. */

export type TokenRow = {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  calls?: number;
};

export type Rate = { input: number; output: number; label: string };

export const RATES_4O: Record<string, Rate> = {
  flagship: { input: 2.5, output: 10, label: "gpt-4o" },
  mini: { input: 0.15, output: 0.6, label: "gpt-4o-mini" },
};

export const RATES_41: Record<string, Rate> = {
  flagship: { input: 2, output: 8, label: "gpt-4.1" },
  mini: { input: 0.4, output: 1.6, label: "gpt-4.1-mini" },
};

export function usd(value: number) {
  return new Intl.NumberFormat("de-CH", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

export function normalizeFamily(model: string): "mini" | "flagship" {
  const m = model.toLowerCase();
  if (m.includes("mini") || m.includes("nano")) return "mini";
  return "flagship";
}

export function costForModel(row: TokenRow, family: "4o" | "41") {
  const tier = normalizeFamily(row.model);
  const rate = family === "41" ? RATES_41[tier] : RATES_4O[tier];
  const input = (row.prompt_tokens / 1_000_000) * rate.input;
  const output = (row.completion_tokens / 1_000_000) * rate.output;
  return { input, output, total: input + output, rate, tier };
}

export function costBreakdown(rows: TokenRow[], family: "4o" | "41") {
  return rows.reduce(
    (acc, row) => {
      const c = costForModel(row, family);
      acc.input += c.input;
      acc.output += c.output;
      acc.total += c.total;
      return acc;
    },
    { input: 0, output: 0, total: 0 },
  );
}

export function actualCost(row: TokenRow) {
  const m = row.model.toLowerCase();
  const family: "4o" | "41" = m.includes("4.1") ? "41" : "4o";
  return costForModel(row, family);
}
