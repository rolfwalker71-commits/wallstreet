import { date, when } from "@/lib/format";

type Stamp = {
  asOf?: string | null;
  delayed?: boolean | null;
  sessionLabel?: string | null;
  marketOpen?: boolean | null;
  venueLabel?: string | null;
  freshnessLabel?: string | null;
  asOfPrecision?: string | null;
};

export function QuoteStamp({
  asOf,
  delayed,
  sessionLabel,
  marketOpen,
  venueLabel,
  freshnessLabel,
  asOfPrecision,
}: Stamp) {
  if (!asOf && delayed == null && !sessionLabel && !freshnessLabel) return null;
  const closed = marketOpen === false;
  const freshness =
    freshnessLabel
    ?? (delayed === true ? "verzögert" : delayed === false ? "nahezu aktuell" : null);
  const stand = asOf
    ? asOfPrecision === "day"
      ? `Stand ${date(asOf)}`
      : `Stand ${when(asOf)}`
    : null;

  return (
    <div className="mt-1 w-full min-w-0 space-y-0.5 text-sm leading-snug text-muted-foreground">
      {stand || freshness ? (
        <p className="break-words">
          {stand}
          {stand && freshness ? " · " : null}
          {freshness ? <span className="font-medium">{freshness}</span> : null}
        </p>
      ) : null}
      {sessionLabel ? (
        <p className={`break-words ${closed ? "font-medium text-loss" : "font-medium text-gain"}`}>
          {sessionLabel}
          {venueLabel ? ` · ${venueLabel}` : ""}
        </p>
      ) : null}
    </div>
  );
}
