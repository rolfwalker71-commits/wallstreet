export type AssetClass = "stock" | "etf" | "fund" | "crypto" | "bond" | "commodity" | "forex";
export type Action = "buy" | "hold" | "sell";

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_class: AssetClass;
  exchange: string | None;
  currency: string;
  last_price: string | null;
  last_price_at: string | null;
  sector: string | null;
  watched: boolean;
  notes: string | null;
}

type None = null;

export interface AgentLog {
  id: string;
  run_id: string;
  agent_name: "research" | "quant" | "strategist" | "educator";
  step: string;
  status: string;
  reasoning: string | null;
  output_payload: Record<string, unknown> | null;
  duration_ms: number | null;
  created_at: string;
}

export interface Recommendation {
  id: string;
  run_id: string;
  action: Action;
  confidence: string;
  risk_reward_ratio: string | null;
  rationale: string;
  news_summary: string | null;
  news_sources: Array<Record<string, unknown>> | null;
  technicals: Record<string, number | null> | null;
  proposed_qty: string | null;
  proposed_price: string | null;
  status: string;
  glossary_terms: string[] | null;
  suggested_symbols: string[] | null;
  created_at: string;
  asset: Asset;
  agent_logs: AgentLog[];
}

export interface Position {
  id: string;
  quantity: string;
  avg_cost: string;
  cost_basis: string | null;
  current_price: string | null;
  opened_at: string | null;
  asset: Asset;
  market_value: string | null;
  unrealized_pnl: string | null;
  unrealized_pnl_pct: number | null;
}

export interface Portfolio {
  id: string;
  name: string;
  base_currency: string;
  cash_balance: string;
  initial_capital: string;
  is_paper: boolean;
  broker_adapter: string | null;
  equity: string | null;
  invested_cost: string | null;
  holdings_value: string | null;
  unrealized_pnl: string | null;
  realized_pnl: string | null;
  total_return_pct: number | null;
  positions: Position[];
  benchmark_return_pct: number | null;
  vs_benchmark_pct: number | null;
}

export interface Transaction {
  id: string;
  side: string;
  source: string;
  quantity: string;
  price: string;
  fee: string;
  realized_pnl: string | null;
  currency: string;
  executed_at: string;
  note: string | null;
  asset: Asset | null;
}

export interface GlossaryTerm {
  id: string;
  term: string;
  slug: string;
  short_definition: string;
  long_explanation: string | null;
  related_terms: string[] | null;
  chart_hint: string | null;
}

export interface Quote {
  symbol: string;
  name: string | null;
  price: string;
  change_pct: number | null;
  currency: string;
  as_of: string;
}

export interface HistoryPoint {
  date: string;
  close: number;
  sma_20: number | null;
  sma_50: number | null;
}

export interface HistorySeries {
  symbol: string;
  period: string;
  points: HistoryPoint[];
}

export interface Technicals {
  symbol: string;
  rsi_14: number | null;
  sma_20: number | null;
  sma_50: number | null;
  macd: number | null;
  macd_signal: number | null;
  last_close: number | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const parsed = JSON.parse(text) as { detail?: unknown };
      if (typeof parsed.detail === "string") throw new Error(parsed.detail);
    } catch (err) {
      if (err instanceof Error && err.message !== text) throw err;
    }
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () =>
    request<{
      status: string;
      llm_enabled?: boolean;
      llm_model?: string | null;
      llm_mini_model?: string | null;
    }>("/api/health"),
  assets: (opts?: { assetClass?: AssetClass; watched?: boolean }) => {
    const q = new URLSearchParams();
    if (opts?.assetClass) q.set("asset_class", opts.assetClass);
    if (opts?.watched !== undefined) q.set("watched", String(opts.watched));
    const suffix = q.toString() ? `?${q}` : "";
    return request<{ items: Asset[]; total: number }>(`/api/assets${suffix}`);
  },
  asset: (symbol: string) =>
    request<Asset>(`/api/assets/${encodeURIComponent(symbol)}`),
  addAsset: (symbol: string, watched = true) =>
    request<Asset>("/api/assets", {
      method: "POST",
      body: JSON.stringify({ symbol, watched }),
    }),
  setWatched: (symbol: string, watched: boolean) =>
    request<Asset>(`/api/assets/${encodeURIComponent(symbol)}/watch`, {
      method: "PATCH",
      body: JSON.stringify({ watched }),
    }),
  recommendations: (params: URLSearchParams) =>
    request<Recommendation[]>(`/api/recommendations?${params}`),
  picks: (refresh = false) =>
    request<Recommendation[]>(
      `/api/recommendations/picks${refresh ? "?refresh=true" : ""}`,
    ),
  refreshPicks: () =>
    request<Recommendation[]>("/api/recommendations/picks/refresh", { method: "POST" }),
  recommendation: (id: string) => request<Recommendation>(`/api/recommendations/${id}`),
  logs: (params: URLSearchParams) => request<AgentLog[]>(`/api/agents/logs?${params}`),
  runAgents: (symbols?: string) =>
    request<Recommendation[]>(
      `/api/agents/run${symbols ? `?symbols=${encodeURIComponent(symbols)}` : ""}`,
      { method: "POST" },
    ),
  portfolio: () => request<Portfolio>("/api/portfolio"),
  transactions: () => request<Transaction[]>("/api/portfolio/transactions"),
  trade: (body: {
    portfolio_id: string;
    symbol: string;
    side: "buy" | "sell";
    quantity: number;
    price?: number;
    recommendation_id?: string;
  }) =>
    request<Transaction>("/api/portfolio/trades", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  glossary: (q?: string) =>
    request<GlossaryTerm[]>(`/api/glossary${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  term: (slug: string) => request<GlossaryTerm>(`/api/glossary/${slug}`),
  quote: (symbol: string) =>
    request<Quote>(`/api/market/quote/${encodeURIComponent(symbol)}`),
  technicals: (symbol: string) =>
    request<Technicals>(`/api/market/technicals/${encodeURIComponent(symbol)}`),
  history: (symbol: string, period = "6mo", since?: string) => {
    const q = new URLSearchParams({ period });
    if (since) q.set("since", since);
    return request<HistorySeries>(`/api/market/history/${encodeURIComponent(symbol)}?${q}`);
  },
  executeRecommendation: (
    id: string,
    body?: { quantity?: number; price?: number },
  ) =>
    request<Transaction>(`/api/recommendations/${id}/execute`, {
      method: "POST",
      body: JSON.stringify(body ?? {}),
    }),
  usage: () =>
    request<{
      today: { prompt_tokens: number; completion_tokens: number; total_tokens: number; calls: number };
      month: { prompt_tokens: number; completion_tokens: number; total_tokens: number; calls: number };
      all: { prompt_tokens: number; completion_tokens: number; total_tokens: number; calls: number };
      models_today: Array<{
        model: string;
        prompt_tokens: number;
        completion_tokens: number;
        calls: number;
      }>;
      models_month?: Array<{
        model: string;
        prompt_tokens: number;
        completion_tokens: number;
        calls: number;
      }>;
      interval_minutes: number;
      cycles_per_day: number;
      estimate: string;
    }>("/api/agents/usage"),
  pushStatus: () =>
    request<{ public_key: string; devices: number; ready: boolean }>("/api/push/status"),
  pushSubscribe: (body: { endpoint: string; keys: { p256dh: string; auth: string } }) =>
    request<{ ok: boolean }>("/api/push/subscribe", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  pushUnsubscribe: (body: { endpoint: string; keys: { p256dh: string; auth: string } }) =>
    request<{ ok: boolean }>("/api/push/subscribe", {
      method: "DELETE",
      body: JSON.stringify(body),
    }),
  pushTest: () => request<{ ok: boolean; sent: number }>("/api/push/test", { method: "POST" }),
  news: (symbol?: string) =>
    request<Array<{ title: string; url: string; source: string; published_at: string | null }>>(
      `/api/market/news${symbol ? `?symbol=${encodeURIComponent(symbol)}` : ""}`,
    ),
};