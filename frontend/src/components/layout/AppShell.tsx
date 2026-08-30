import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  BookOpen,
  Bot,
  CandlestickChart,
  Moon,
  Radar,
  Sun,
  Wallet,
} from "lucide-react";
import {
  applyChrome,
  applyTheme,
  dockBarClass,
  fabClearance,
  navItemClass,
  type Chrome,
} from "@/lib/platform";

const NAV = [
  { to: "/", label: "Signale", icon: Radar },
  { to: "/watchlist", label: "Watchlist", icon: CandlestickChart },
  { to: "/wallet", label: "Depot", icon: Wallet },
  { to: "/lexicon", label: "Lexikon", icon: BookOpen },
  { to: "/agents", label: "Agenten", icon: Bot },
];

export function AppShell() {
  const [chrome, setChrome] = useState<Chrome>("android");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const sync = () => setChrome(applyChrome("auto"));
    sync();
    applyTheme("system");
    const mq = window.matchMedia("(min-width: 64rem)");
    const dark = window.matchMedia("(prefers-color-scheme: dark)");
    const onDark = () => {
      const next = dark.matches ? "dark" : "light";
      setTheme(next);
      applyTheme("system");
    };
    onDark();
    mq.addEventListener("change", sync);
    dark.addEventListener("change", onDark);
    return () => {
      mq.removeEventListener("change", sync);
      dark.removeEventListener("change", onDark);
    };
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  };

  return (
    <div className="min-h-dvh bg-background text-foreground">
      {chrome === "desktop" ? (
        <header className="mica sticky top-0 z-30 flex items-center justify-between border-b border-border px-4 py-2">
          <span className="text-lg font-semibold tracking-tight text-primary">Wallstreet</span>
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex min-h-11 items-center gap-2 rounded-md px-3 text-sm hover:bg-muted"
            aria-label="Design umschalten"
          >
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </button>
        </header>
      ) : (
        <header className="sticky top-0 z-30 bg-secondary px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <h1 className="text-xl font-semibold leading-snug tracking-tight text-primary">
              Wallstreet
            </h1>
            <button
              type="button"
              onClick={toggleTheme}
              className="inline-flex size-12 items-center justify-center rounded-full bg-secondary text-primary"
              aria-label="Design umschalten"
            >
              {theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
            </button>
          </div>
        </header>
      )}

      <div className={chrome === "desktop" ? "flex" : ""}>
        {chrome === "desktop" ? (
          <aside className="sticky top-14 h-[calc(100dvh-3.5rem)] w-56 shrink-0 border-r border-border p-3">
            <nav className="flex flex-col gap-1" aria-label="Hauptnavigation">
              {NAV.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    [
                      navItemClass("desktop", isActive),
                      isActive ? "border-l-2 border-primary" : "border-l-2 border-transparent",
                    ].join(" ")
                  }
                >
                  <item.icon className="size-4" aria-hidden />
                  <span className="break-words leading-snug">{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </aside>
        ) : null}

        <main className={`mx-auto w-full max-w-6xl flex-1 px-4 py-4 ${fabClearance(chrome)}`}>
          <Outlet context={{ chrome }} />
        </main>
      </div>

      <nav className={`${dockBarClass(chrome)} lg:hidden`} aria-label="Hauptnavigation">
        <ul className="grid grid-cols-5">
          {NAV.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => navItemClass("android", isActive)}
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`inline-flex size-12 items-center justify-center rounded-full ${
                        isActive ? "bg-secondary text-primary" : "text-muted-foreground"
                      }`}
                    >
                      <item.icon className="size-6" aria-hidden />
                    </span>
                    <span
                      className={`text-xs leading-snug ${
                        isActive ? "text-primary font-medium" : "text-muted-foreground"
                      }`}
                    >
                      {item.label}
                    </span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}