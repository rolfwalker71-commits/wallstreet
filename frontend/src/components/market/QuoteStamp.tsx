import { when } from "@/lib/format";

type Stamp = {
  asOf?: string | null;
  delayed?: boolean | null;
  sessionLabel?: string | null;
  marketOpen?: boolean | null;
  venueLabel?: string | null;
};

export function QuoteStamp({ asOf, delayed, sessionLabel, marketOpen, venueLabel }: Stamp) {
  if (!asOf && delayed == null && !sessionLabel) return null;
  const closed = marketOpen === false;
  const freshness =
    delayed === true ? "verzögert" : delayed === false ? "nahezu aktuell" : null;

  return (
    <div className="mt-1 w-full min-w-0 space-y-0.5 text-sm leading-snug text-muted-foreground">
      {asOf || freshness ? (
        <p className="break-words">
          {asOf ? `Stand ${when(asOf)}` : null}
          {asOf && freshness ? " · " : null}
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
