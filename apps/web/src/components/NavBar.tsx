"use client";

import { LayoutDashboard, LogOut, ScanLine, Ticket, TicketPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearToken, getStoredToken } from "@/lib/auth";

export default function NavBar() {
  const router = useRouter();
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // localStorage n'existe pas côté serveur : l'état de connexion ne peut
    // être connu qu'après le montage, côté client.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setConnected(Boolean(getStoredToken()));
  }, []);

  function handleLogout() {
    clearToken();
    setConnected(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-sm">
            <Ticket className="h-4.5 w-4.5" strokeWidth={2.25} />
          </span>
          billetterie
        </Link>
        <div className="flex flex-wrap items-center gap-1 text-sm font-medium text-slate-600 sm:gap-2">
          <Link
            href="/"
            className="rounded-md px-2.5 py-1.5 transition hover:bg-slate-100 hover:text-indigo-700"
          >
            Événements
          </Link>
          <Link
            href="/mes-billets"
            className="rounded-md px-2.5 py-1.5 transition hover:bg-slate-100 hover:text-indigo-700"
          >
            Mes billets
          </Link>
          <Link
            href="/scan"
            className="hidden items-center gap-1.5 rounded-md px-2.5 py-1.5 transition hover:bg-slate-100 hover:text-indigo-700 sm:flex"
          >
            <ScanLine className="h-4 w-4" />
            Scan
          </Link>
          {connected ? (
            <>
              <Link
                href="/organisateurs/tableau-de-bord"
                className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 transition hover:bg-slate-100 hover:text-indigo-700"
              >
                <LayoutDashboard className="h-4 w-4" />
                Tableau de bord
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
              >
                <LogOut className="h-3.5 w-3.5" />
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link
                href="/organisateurs/connexion"
                className="rounded-md px-2.5 py-1.5 transition hover:bg-slate-100 hover:text-indigo-700"
              >
                Connexion organisateur
              </Link>
              <Link
                href="/organisateurs/inscription"
                className="flex items-center gap-1.5 rounded-md bg-gradient-to-br from-indigo-600 to-violet-600 px-3 py-1.5 text-white shadow-sm transition hover:brightness-110"
              >
                <TicketPlus className="h-4 w-4" />
                Devenir organisateur
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
