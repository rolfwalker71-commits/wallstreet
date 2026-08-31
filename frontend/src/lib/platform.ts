export type Chrome = "android" | "desktop" | "ios";
export type ChromePref = "auto" | Chrome;

const MQ = "(min-width: 64rem)";

export function detectChrome(pref: ChromePref = "auto"): Chrome {
  if (pref !== "auto") return pref;
  if (typeof window === "undefined") return "android";
  return window.matchMedia(MQ).matches ? "desktop" : "android";
}

export function applyChrome(pref: ChromePref) {
  const chrome = detectChrome(pref);
  document.documentElement.dataset.chrome = chrome;
  return chrome;
}

export function applyTheme(theme: "light" | "dark" | "system") {
  const dark =
    theme === "dark" ||
    (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

export function listTileClass(chrome: Chrome) {
  if (chrome === "desktop") {
    return "rounded-md bg-card ring-1 ring-border";
  }
  return "rounded-3xl bg-card";
}

export function dockBarClass(chrome: Chrome) {
  if (chrome === "desktop") return "hidden";
  return "fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card pb-[env(safe-area-inset-bottom)]";
}

export function fabClass(chrome: Chrome) {
  if (chrome === "desktop") {
    return "size-12 rounded-md bg-primary text-on-primary";
  }
  return "size-16 rounded-[1.75rem] bg-primary text-on-primary";
}

export function primaryActionClass(chrome: Chrome) {
  if (chrome === "desktop") {
    return "inline-flex h-11 min-h-11 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md bg-primary px-4 text-sm font-medium text-on-primary";
  }
  return "inline-flex min-h-12 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full bg-primary px-5 text-sm font-medium text-on-primary";
}

export function fabClearance(chrome: Chrome, docks = 1) {
  if (chrome === "desktop") return "mb-4";
  return docks > 0 ? "mb-24" : "mb-6";
}

export function panelClass(chrome: Chrome) {
  if (chrome === "desktop") {
    return "rounded-md bg-card ring-1 ring-border";
  }
  return "rounded-3xl bg-card";
}

export function fieldClass(chrome: Chrome) {
  if (chrome === "desktop") {
    return "min-h-11 w-full rounded-md bg-background px-3 text-base ring-1 ring-border";
  }
  return "min-h-12 w-full rounded-full bg-background px-4 text-base ring-1 ring-border";
}

export function navItemClass(chrome: Chrome, active: boolean) {
  if (chrome === "desktop") {
    return [
      "flex min-h-12 items-center gap-3 rounded-md px-3 text-base font-semibold",
      active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted",
    ].join(" ");
  }
  return "flex min-h-16 flex-col items-center justify-center gap-1 px-2";
}