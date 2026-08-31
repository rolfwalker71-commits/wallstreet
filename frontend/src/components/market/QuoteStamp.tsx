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
  return (
    <p className="mt-1 w-full text-sm leading-snug text-muted-foreground">
      {asOf ? <>Stand {when(asOf)}</> : null}
      {delayed === true ? (
        <>
          {asOf ? " · " : ""}
          <span className="font-medium">verzögert</span>
        </>
      ) : delayed === false ? (
        <>
          {asOf ? " · " : ""}
          nahezu aktuell
        </>
      ) : null}
      {sessionLabel ? (
        <>
          {" · "}
          <span className={closed ? "font-medium text-loss" : "text-gain"}>
            {venueLabel ? `${venueLabel}: ` : ""}
            {sessionLabel}
          </span>
        </>
      ) : null}
    </p>
  );
}
