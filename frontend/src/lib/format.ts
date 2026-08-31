export const LOCALE = "de-CH";

const dateFmt = new Intl.DateTimeFormat(LOCALE, {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const timeFmt = new Intl.DateTimeFormat(LOCALE, {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

export function date(iso: string | Date | null | undefined) {
  if (!iso) return "—";
  const d = iso instanceof Date ? iso : new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return dateFmt.format(d);
}

export function time(iso: string | Date | null | undefined) {
  if (!iso) return "—";
  const d = iso instanceof Date ? iso : new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return timeFmt.format(d);
}

/** Datum und Zeit: dd.mm.yyyy hh:mm */
export function when(iso: string | Date | null | undefined) {
  if (!iso) return "—";
  const d = iso instanceof Date ? iso : new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return `${dateFmt.format(d)} ${timeFmt.format(d)}`;
}

export function number(value: string | number | null | undefined, digits = 2) {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return "—";
  return new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(n);
}

export function money(
  value: string | number | null | undefined,
  currency = "USD",
  opts?: { signed?: boolean },
) {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return "—";
  const max = n < 1 && n > -1 && n !== 0 ? 4 : 2;
  return new Intl.NumberFormat(LOCALE, {
    style: "currency",
    currency,
    signDisplay: opts?.signed ? "exceptZero" : "auto",
    minimumFractionDigits: 2,
    maximumFractionDigits: max,
  }).format(n);
}

export function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${number(value, 2)} %`;
}

export function asNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isNaN(n) ? null : n;
}

export function signedClass(value: string | number | null | undefined) {
  const n = asNumber(value);
  if (n === null || n === 0) return "text-foreground";
  return n > 0 ? "text-gain" : "text-loss";
}

export function recAccentClass(action: string) {
  if (action === "buy") return "border-l-4 border-gain";
  if (action === "sell") return "border-l-4 border-loss";
  return "border-l-4 border-primary";
}

export const ACTION_LABEL: Record<string, string> = {
  buy: "Kauf",
  hold: "Halten",
  sell: "Verkauf",
};

export const CLASS_LABEL: Record<string, string> = {
  stock: "Aktien",
  etf: "ETFs",
  fund: "Fonds",
  crypto: "Crypto",
  bond: "Obligationen",
  commodity: "Rohstoffe",
  forex: "Devisen",
};