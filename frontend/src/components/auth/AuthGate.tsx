import { useEffect, useState, type ReactNode } from "react";
import { api, type AuthSetup, type AuthStatus } from "@/lib/api";
import { applyChrome, fieldClass, panelClass, primaryActionClass, type Chrome } from "@/lib/platform";

function TotpForm({
  chrome,
  onOk,
  setup,
}: {
  chrome: Chrome;
  onOk: () => void;
  setup: AuthSetup | null;
}) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.verifyTotp(code);
      onOk();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Code ungültig");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      {setup ? (
        <div className="space-y-3">
          <div
            className="mx-auto w-56 rounded-3xl bg-card p-3"
            dangerouslySetInnerHTML={{ __html: setup.qr_svg }}
            aria-label="QR-Code für den Authenticator"
          />
          <p className="break-all text-center text-sm text-muted-foreground">
            Manuell: {setup.secret}
          </p>
        </div>
      ) : null}
      <label className="block">
        <span className="mb-1 block text-sm text-muted-foreground">6-stelliger Code</span>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="[0-9]{6}"
          className={`${fieldClass(chrome)} text-center tracking-[0.4em]`}
          aria-label="Authenticator-Code"
        />
      </label>
      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={busy || code.length !== 6}
        className={`${primaryActionClass(chrome)} w-full disabled:opacity-60`}
      >
        {busy ? "Prüft…" : setup ? "Einrichten und öffnen" : "Öffnen"}
      </button>
    </form>
  );
}

export function AuthGate({ children }: { children: ReactNode }) {
  const [chrome, setChrome] = useState<Chrome>("android");
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [setup, setSetup] = useState<AuthSetup | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const next = await api.authStatus();
    setStatus(next);
    if (!next.configured && !next.authenticated) {
      setSetup(await api.authSetup());
    } else {
      setSetup(null);
    }
  };

  useEffect(() => {
    setChrome(applyChrome("auto"));
    refresh().catch((e: Error) => setError(e.message));
  }, []);

  if (error && !status) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background px-4">
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background px-4">
        <p className="text-sm text-muted-foreground">Prüft Zugang…</p>
      </div>
    );
  }

  if (status.authenticated) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-4 py-8">
      <div className={`${panelClass(chrome)} w-full max-w-md space-y-4 px-5 py-6`}>
        <h1 className="text-2xl font-semibold leading-snug tracking-tight text-primary">Wallstreet</h1>
        {status.configured ? (
          <p className="text-sm text-muted-foreground">
            Einmal den Code aus der Authenticator-App. Danach bleibt dieses Gerät angemeldet.
            Familie nutzt denselben Authenticator-Eintrag, jedes Gerät einmal.
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">
            QR mit Google Authenticator, Aegis oder ähnlichem scannen. Danach denselben Code hier
            eingeben. Familie scannt später denselben QR unter Agenten.
          </p>
        )}
        <TotpForm
          chrome={chrome}
          setup={status.configured ? null : setup}
          onOk={() => {
            setError(null);
            void refresh();
          }}
        />
      </div>
    </div>
  );
}
