import { api } from "@/lib/api";

function urlBase64ToUint8Array(base64: string) {
  const normalized = base64.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const raw = atob(padded);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
}

function subBody(sub: PushSubscription) {
  const json = sub.toJSON();
  return {
    endpoint: json.endpoint || "",
    keys: {
      p256dh: json.keys?.p256dh || "",
      auth: json.keys?.auth || "",
    },
  };
}

export async function thisDeviceSubscribed() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return false;
  const reg = await navigator.serviceWorker.ready;
  return Boolean(await reg.pushManager.getSubscription());
}

export async function activatePush() {
  if (!("Notification" in window) || !("serviceWorker" in navigator)) {
    throw new Error("Dieser Browser unterstützt keine Web-Push-Nachrichten.");
  }
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Berechtigung wurde nicht erteilt.");
  }
  const status = await api.pushStatus();
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(status.public_key),
  });
  await api.pushSubscribe(subBody(sub));
}

export async function deactivatePush() {
  if (!("serviceWorker" in navigator)) return;
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;
  await api.pushUnsubscribe(subBody(sub));
  await sub.unsubscribe();
}
