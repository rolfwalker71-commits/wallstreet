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
  return (
    <text
      x={nx}
      y={ny - 10}
      textAnchor="middle"
      fill="rgb(var(--muted-foreground))"
      fontSize="0.6875rem"
    >
      {String(value)}
    </text>
  );
}
