"use client";

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
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-4">
        <Link href="/" className="text-lg font-bold text-indigo-700">
          billetterie
        </Link>
        <div className="flex flex-wrap items-center gap-4 text-sm font-medium text-slate-600">
          <Link href="/" className="hover:text-indigo-700">
            Événements
          </Link>
          <Link href="/mes-billets" className="hover:text-indigo-700">
            Mes billets
          </Link>
          <Link href="/scan" className="hover:text-indigo-700">
            Scan
          </Link>
          {connected ? (
            <>
              <Link href="/organisateurs/tableau-de-bord" className="hover:text-indigo-700">
                Tableau de bord
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-50"
              >
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link href="/organisateurs/connexion" className="hover:text-indigo-700">
                Connexion organisateur
              </Link>
              <Link
                href="/organisateurs/inscription"
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-white hover:bg-indigo-500"
              >
                Devenir organisateur
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
