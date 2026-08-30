import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { api, type GlossaryTerm } from "@/lib/api";
import { listTileClass, panelClass, type Chrome } from "@/lib/platform";

function MiniChart({ hint }: { hint: string | null }) {
  if (!hint) return null;
  const bars = hint === "rsi" ? [30, 45, 62, 71, 55] : hint === "macd" ? [10, -4, 8, 14, 3] : [20, 24, 22, 30, 28];
  const max = Math.max(...bars.map((b) => Math.abs(b)), 1);
  return (
    <svg viewBox="0 0 120 48" className="mt-3 h-12 w-full" aria-hidden>
      {bars.map((b, i) => {
        const h = (Math.abs(b) / max) * 36;
        const y = b >= 0 ? 40 - h : 24;
        return (
          <rect
            key={i}
            x={8 + i * 22}
            y={y}
            width="14"
            height={h}
            rx="4"
            className="fill-primary"
          />
        );
      })}
    </svg>
  );
}

export function LexiconPage() {
  const { slug } = useParams();
  const { chrome } = useOutletContext<{ chrome: Chrome }>();
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);
  const [q, setQ] = useState("");
  const [active, setActive] = useState<GlossaryTerm | null>(null);

  useEffect(() => {
    api.glossary(q || undefined).then(setTerms).catch(() => setTerms([]));
  }, [q]);

  useEffect(() => {
    if (!slug) {
      setActive(null);
      return;
    }
    api
      .term(slug)
      .then(setActive)
      .catch(() => setActive(null));
  }, [slug]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold leading-snug tracking-tight">Börsen-Lexikon</h2>
      <label className="block">
        <span className="sr-only">Suche</span>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Begriff suchen…"
          className="min-h-12 w-full rounded-full bg-card px-4 text-base ring-1 ring-border focus:ring-2 focus:ring-ring"
        />
      </label>

      {active ? (
        <article className={`${panelClass(chrome)} px-5 py-5`}>
          <Link to="/lexicon" className="text-sm text-primary">
            ← Alle Begriffe
          </Link>
          <h3 className="mt-2 text-xl font-semibold leading-snug">{active.term}</h3>
          <p className="mt-2 leading-relaxed">{active.short_definition}</p>
          {active.long_explanation ? (
            <p className="mt-3 leading-relaxed text-muted-foreground">{active.long_explanation}</p>
          ) : null}
          <MiniChart hint={active.chart_hint} />
        </article>
      ) : (
        <ul className="space-y-3">
          {terms.map((t) => (
            <li key={t.id}>
              <Link to={`/lexicon/${t.slug}`} className={`${listTileClass(chrome)} block px-4 py-4`}>
                <p className="font-semibold leading-snug break-words">{t.term}</p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{t.short_definition}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}