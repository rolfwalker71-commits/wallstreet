import { Navigate, Route, Routes } from "react-router-dom";
import { AuthGate } from "@/components/auth/AuthGate";
import { AppShell } from "@/components/layout/AppShell";
import { AgentsPage } from "@/pages/Agents";
import { LexiconPage } from "@/pages/Lexicon";
import { MarketsPage } from "@/pages/Markets";
import { SignalDetailPage } from "@/pages/SignalDetail";
import { SignalsPage } from "@/pages/Signals";
import { WalletPage } from "@/pages/Wallet";
import { WatchlistDetailPage } from "@/pages/WatchlistDetail";
import { EmpfehlungenPage } from "@/pages/Empfehlungen";

export function App() {
  return (
    <AuthGate>
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<SignalsPage />} />
        <Route path="empfehlungen" element={<EmpfehlungenPage />} />
        <Route path="signals/:id" element={<SignalDetailPage />} />
        <Route path="watchlist" element={<MarketsPage />} />
        <Route path="watchlist/:symbol" element={<WatchlistDetailPage />} />
        <Route path="markets" element={<Navigate to="/watchlist" replace />} />
        <Route path="wallet" element={<WalletPage />} />
        <Route path="lexicon" element={<LexiconPage />} />
        <Route path="lexicon/:slug" element={<LexiconPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
    </AuthGate>
  );
}