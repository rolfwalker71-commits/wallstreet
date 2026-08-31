import type { ReactNode } from "react";
import { money, pct, signedClass } from "@/lib/format";

export function Signed({
  value,
  className = "",
  children,
}: {
  value: string | number | null | undefined;
  className?: string;
  children: ReactNode;
}) {
  return <span className={`${signedClass(value)} tabular-nums ${className}`}>{children}</span>;
}

export function SignedMoney({
  value,
  currency = "USD",
  className = "",
}: {
  value: string | number | null | undefined;
  currency?: string;
  className?: string;
}) {
  return (
    <Signed value={value} className={className}>
      {money(value, currency, { signed: true })}
    </Signed>
  );
}

export function SignedPct({
  value,
  className = "",
}: {
  value: number | null | undefined;
  className?: string;
}) {
  return (
    <Signed value={value} className={className}>
      {pct(value)}
    </Signed>
  );
}
