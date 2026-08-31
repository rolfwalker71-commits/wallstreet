import { dateShort, number } from "@/lib/format";

export function peakCaption(iso: string, close: number) {
  return `${dateShort(iso)}\n${number(close, 2)}`;
}

export function PeakDot({
  cx,
  cy,
  payload,
  stroke,
}: {
  cx?: number;
  cy?: number;
  payload?: { peakLabel?: string };
  stroke?: string;
}) {
  if (!payload?.peakLabel || cx == null || cy == null) return <g />;
  return <circle cx={cx} cy={cy} r={3} fill={stroke} />;
}

export function PeakDateLabel({
  x,
  y,
  value,
}: {
  x?: number | string;
  y?: number | string;
  value?: string | number;
}) {
  if (value == null || value === "") return null;
  const nx = typeof x === "number" ? x : Number(x);
  const ny = typeof y === "number" ? y : Number(y);
  if (!Number.isFinite(nx) || !Number.isFinite(ny)) return null;
  const [when, price] = String(value).split("\n");
  const firstY = ny - (price ? 22 : 10);
  return (
    <text
      x={nx}
      y={firstY}
      textAnchor="middle"
      fill="rgb(var(--muted-foreground))"
      fontSize="0.6875rem"
    >
      <tspan x={nx} dy="0">
        {when}
      </tspan>
      {price ? (
        <tspan x={nx} dy="1.1em" fontWeight={600} fill="rgb(var(--foreground))">
          {price}
        </tspan>
      ) : null}
    </text>
  );
}
