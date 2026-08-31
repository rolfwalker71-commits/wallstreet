import { useEffect, useState } from "react";
import { Bell, BellOff } from "lucide-react";
import { api } from "@/lib/api";
import { activatePush, deactivatePush, thisDeviceSubscribed } from "@/lib/push";
import { panelClass, type Chrome } from "@/lib/platform";

export function NotifyToggle({ chrome }: { chrome: Chrome }) {
  const [on, setOn] = useState(false);
  const [devices, setDevices] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const refresh = async () => {
    const [local, status] = await Promise.all([
      thisDeviceSubscribed().catch(() => false),
      api.pushStatus().catch(() => ({ devices: 0 })),
    ]);
    setOn(local);
    setDevices(status.devices);
  };

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  const shape =
    chrome === "desktop"
      ? "min-h-11 rounded-md px-4 text-sm"
      : "min-h-12 rounded-full px-5 text-sm";

  const toggle = async () => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      if (on) await deactivatePush();
      else await activatePush();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Push fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  const test = async () => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const res = await api.pushTest();
      setNote(
        res.sent === 1
          ? "Test gesendet. Die Meldung sollte gleich erscheinen."
          : `Test an ${res.sent} Geräte gesendet.`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className={`${panelClass(chrome)} space-y-3 px-4 py-4`}>
      <h3 className="text-lg font-semibold leading-snug">Benachrichtigungen</h3>
      <p className="text-sm text-muted-foreground">
        VAPID-Schlüssel liegen in der Datenbank. Hier nur noch aktivieren — dann Push bei neuem
        Kauf oder Verkauf, auch wenn die App zu ist.
      </p>
      <p className="text-sm">
        Dieses Gerät:{" "}
        <span className={on ? "text-gain font-medium" : "text-muted-foreground"}>
          {on ? "aktiv" : "aus"}
        </span>
        {devices > 0 ? ` · ${devices} Gerät${devices === 1 ? "" : "e"} registriert` : ""}
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={toggle}
          disabled={busy}
          className={`${shape} inline-flex items-center justify-center gap-2 font-medium disabled:opacity-60 ${
            on ? "bg-secondary text-primary" : "bg-primary text-on-primary"
          }`}
        >
          {on ? <BellOff className="size-4" aria-hidden /> : <Bell className="size-4" aria-hidden />}
          {on ? "Deaktivieren" : "Aktivieren"}
        </button>
        <button
          type="button"
          onClick={test}
          disabled={busy || !on}
          className={`${shape} bg-gain-container font-medium text-gain disabled:opacity-50`}
        >
          Test senden
        </button>
      </div>
      {note ? <p className="text-sm font-medium text-gain">{note}</p> : null}
      {error ? (
        <p className="text-sm text-loss" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
