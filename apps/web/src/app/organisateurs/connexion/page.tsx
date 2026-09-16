"use client";

import { LogIn } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, organizerLogin } from "@/lib/api";
import { storeToken } from "@/lib/auth";

export default function OrganizerLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const auth = await organizerLogin({ email, password });
      storeToken(auth.access_token);
      router.push("/organisateurs/tableau-de-bord");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Connexion impossible.");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <LogIn className="h-6 w-6" />
        </span>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">Connexion organisateur</h1>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <label className="block text-sm">
          <span className="text-slate-700">E-mail</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-700">Mot de passe</span>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </label>

        {error && <p className="text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-gradient-to-br from-indigo-600 to-violet-600 px-4 py-2.5 font-medium text-white shadow-sm transition hover:brightness-110 disabled:opacity-60"
        >
          {submitting ? "Connexion..." : "Se connecter"}
        </button>
      </form>

      <p className="text-center text-sm text-slate-600">
        Pas encore de compte ?{" "}
        <Link href="/organisateurs/inscription" className="font-medium text-indigo-700 underline">
          Devenir organisateur
        </Link>
      </p>
    </div>
  );
}
