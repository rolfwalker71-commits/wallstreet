import { useState } from "react";
import { api, type AuthSetup } from "@/lib/api";
import { panelClass, primaryActionClass, type Chrome } from "@/lib/platform";

export function FamilyTotp({ chrome }: { chrome: Chrome }) {
  const [setup, setSetup] = useState<AuthSetup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const show = async () => {
    setBusy(true);
    setError(null);
    try {
      setSetup(await api.authSetup());
    } catch (e) {
      setError(e instanceof Error ? e.message : "QR nicht verfügbar");
    } finally {
      setBusy(false);
    }
  };

  const logout = async () => {
    await api.authLogout();
    window.location.reload();
  };

  return (
    <section className={`${panelClass(chrome)} space-y-3 px-4 py-4`}>
      <h3 className="text-lg font-semibold">Zugang Familie</h3>
      <p className="text-sm text-muted-foreground">
        Ein gemeinsamer Authenticator-Eintrag. Jedes Gerät gibt den Code einmal ein und bleibt
        angemeldet. QR nur Personen zeigen, die die App nutzen dürfen — kein öffentlicher Link.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => void show()} className={primaryActionClass(chrome)}>
          {busy ? "Lädt…" : setup ? "QR neu laden" : "QR für Familie zeigen"}
        </button>
        <button
          type="button"
          onClick={() => void logout()}
          className={
            chrome === "desktop"
              ? "inline-flex h-11 min-h-11 items-center rounded-md bg-muted px-4 text-sm"
              : "inline-flex min-h-12 items-center rounded-full bg-muted px-5 text-sm"
          }
        >
          Dieses Gerät abmelden
        </button>
      </div>
      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
      {setup ? (
        <div className="space-y-2">
          <div
            className="w-56 rounded-3xl bg-card p-3"
            dangerouslySetInnerHTML={{ __html: setup.qr_svg }}
            aria-label="QR-Code für die Familie"
          />
          <p className="break-all text-sm text-muted-foreground">Manuell: {setup.secret}</p>
        </div>
      ) : null}
    </section>
  );
}
