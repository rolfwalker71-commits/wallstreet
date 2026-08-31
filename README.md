# Wallstreet

Selbstgehostete PWA: persönlicher Finanz- & Börsen-Assistent mit Multi-Agenten-Team (Research, Quant, Strategist, Educator).

Die App ist auf **Port 4499** erreichbar.

## Stack

- **Backend:** FastAPI, SQLAlchemy (async), LangGraph, APScheduler, yfinance, CoinGecko
- **Daten:** PostgreSQL 16, Redis
- **Frontend:** Vite + React (PWA) — Material You 3 Expressive (mobil) / Fluent 2 (Desktop `lg+`)

## Schnellstart (Docker / Homelab)

```bash
cp .env.example .env
# OPENAI_API_KEY setzen (optional — ohne Key läuft eine Heuristik)

# Lokal bauen
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose up -d

# Remote / Produktion: nur Images, nie --build
docker compose pull && docker compose up -d
```

Öffnen: [http://localhost:4499](http://localhost:4499)  
API-Docs: [http://localhost:4499/api/docs](http://localhost:4499/api/docs)

`GHCR_OWNER` in `.env` ist der GitHub-User (hier `rolfwalker71-commits`). Images:

- `ghcr.io/rolfwalker71-commits/wallstreet-frontend`
- `ghcr.io/rolfwalker71-commits/wallstreet-backend`

GHCR-Pakete sind nach dem ersten Push privat. Auf dem Server entweder einloggen oder die Pakete unter GitHub → Packages auf **Public** stellen:

```bash
echo TOKEN | docker login ghcr.io -u rolfwalker71-commits --password-stdin
# TOKEN: classic PAT mit read:packages
```

## Lokale Entwicklung

```bash
# Backend (PostgreSQL + Redis müssen laufen, oder Ports aus docker compose)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://wallstreet:wallstreet@localhost:5432/wallstreet
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:4499, proxyt /api → :8000
```

## Agenten

| Rolle | Aufgabe |
|---|---|
| Research & News | RSS (Yahoo, Reuters, CNBC), Sentiment |
| Quant | Kurse (Yahoo / CoinGecko), RSI, SMA/EMA, MACD |
| Senior Strategist | Kauf / Halten / Verkauf + Chance-Risiko + Paper-Trade |
| Finance Educator | Glossar und Begriffserklärungen in Empfehlungen |

Intervall: `AGENT_CRON_MINUTES` (Default 30). Manuell: Button **Agenten starten** oder `POST /api/agents/run`.

Ohne `OPENAI_API_KEY` synthetisiert der Strategist eine regelbasierte Heuristik — das Gerüst bleibt gleich.

## Module

- **Signale:** Filter nach Aktie / ETF / Crypto / Obligation, Denkprozess der Agenten
- **Märkte:** Live-Kurse der Watchlist
- **Depot:** Paper-Wallet, P&L, Rendite vs. S&P 500 (VOO), `broker_adapter` für späteren Live-Broker
- **Lexikon:** Fachbegriffe inkl. Mini-Charts

## Modelle (Kern)

`Asset`, `Recommendation`, `AgentLog`, `Portfolio` / `Position`, `Transaction` — plus `NewsItem` und `GlossaryTerm`.

## GHCR CI

`.github/workflows/deploy.yml` baut `linux/amd64` und pusht beide Images nach `ghcr.io`.
