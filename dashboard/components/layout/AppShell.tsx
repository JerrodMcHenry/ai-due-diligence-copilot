"use client";

import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";

type AppShellProps = {
  children: React.ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);

  useEffect(() => {
    if (!mobileNavigationOpen) {
      return;
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileNavigationOpen(false);
      }
    };

    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [mobileNavigationOpen]);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-72">
        <Sidebar />
      </div>

      {mobileNavigationOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setMobileNavigationOpen(false)}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          />

          <div className="relative h-full w-72 max-w-[85vw] shadow-2xl">
            <Sidebar onNavigate={() => setMobileNavigationOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-72">
        <header className="sticky top-0 z-30 flex h-16 items-center border-b border-slate-800 bg-slate-950/90 px-4 backdrop-blur md:px-6 lg:hidden">
          <button
            type="button"
            onClick={() => setMobileNavigationOpen(true)}
            aria-label="Open navigation"
            aria-expanded={mobileNavigationOpen}
            className="inline-flex size-10 items-center justify-center rounded-lg border border-slate-700 text-slate-300 transition-colors hover:bg-slate-900 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          >
            <span aria-hidden="true" className="text-xl leading-none">
              ☰
            </span>
          </button>

          <div className="ml-4">
            <p className="text-sm font-semibold text-white">
              Startup Intelligence
            </p>
          </div>
        </header>

        <main className="min-h-screen">
          <div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
