"use client";

import { CheckCircle2, KeyRound, ScanLine, Video, XCircle } from "lucide-react";
import jsQR from "jsqr";
import { useEffect, useRef, useState } from "react";
import { ApiError, scanTicket, type ScanOut } from "@/lib/api";

const SCAN_KEY_STORAGE = "billetterie_scan_key";

export default function ScanPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number | null>(null);

  const [scanKey, setScanKey] = useState("");
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [manualToken, setManualToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ScanOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // sessionStorage n'existe pas côté serveur : ne peut être lu qu'après
    // le montage, côté client.
    try {
      const stored = window.sessionStorage.getItem(SCAN_KEY_STORAGE);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (stored) setScanKey(stored);
    } catch {
      // Stockage indisponible : la clé devra être ressaisie, sans bloquer.
    }
  }, []);

  useEffect(() => {
    try {
      window.sessionStorage.setItem(SCAN_KEY_STORAGE, scanKey);
    } catch {
      // Idem.
    }
  }, [scanKey]);

  function stopCamera() {
    setScanning(false);
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  useEffect(() => stopCamera, []);

  function tick() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
      rafRef.current = requestAnimationFrame(tick);
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);
    if (code && code.data) {
      void handleToken(code.data);
      return;
    }
    rafRef.current = requestAnimationFrame(tick);
  }

  async function startCamera() {
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("Caméra non disponible sur ce navigateur — utilisez la saisie manuelle.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setScanning(true);
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      setCameraError("Accès à la caméra refusé ou indisponible — utilisez la saisie manuelle.");
    }
  }

  async function handleToken(token: string) {
    stopCamera();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await scanTicket(token, scanKey);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Scan impossible.");
    } finally {
      setBusy(false);
    }
  }

  function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (manualToken.trim()) void handleToken(manualToken.trim());
  }

  function scanNext() {
    setResult(null);
    setError(null);
    setManualToken("");
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div className="text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <ScanLine className="h-6 w-6" />
        </span>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">Scan de billets</h1>
        <p className="mt-1 text-slate-600">
          Réservé au personnel présent à l&apos;entrée : clé de scan requise.
        </p>
      </div>

      <label className="block text-sm">
        <span className="flex items-center gap-1.5 text-slate-700">
          <KeyRound className="h-3.5 w-3.5" /> Clé de scan (X-Scan-Key)
        </span>
        <input
          type="password"
          value={scanKey}
          onChange={(e) => setScanKey(e.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder="Fournie par l'organisateur"
        />
      </label>

      {result && (
        <div className="space-y-3 rounded-xl border border-green-200 bg-green-50 p-6 text-center">
          <CheckCircle2 className="mx-auto h-9 w-9 text-green-600" />
          <p className="text-lg font-semibold text-green-800">Billet valide</p>
          <p className="text-sm text-green-700">
            {result.ticket_type_name} — {result.event_title}
          </p>
          <button
            onClick={scanNext}
            className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-green-500"
          >
            Scanner un autre billet
          </button>
        </div>
      )}

      {error && (
        <div className="space-y-3 rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <XCircle className="mx-auto h-9 w-9 text-red-600" />
          <p className="font-semibold text-red-800">Refusé</p>
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={scanNext}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500"
          >
            Réessayer
          </button>
        </div>
      )}

      {!result && !error && (
        <div className="space-y-4">
          <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-black">
            <video ref={videoRef} className="aspect-square w-full object-cover" muted playsInline />
            {!scanning && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-900/60 text-slate-300">
                <Video className="h-8 w-8" />
                <span className="text-xs">Caméra inactive</span>
              </div>
            )}
          </div>
          <canvas ref={canvasRef} className="hidden" />

          {!scanning ? (
            <button
              onClick={startCamera}
              disabled={!scanKey || busy}
              className="flex w-full items-center justify-center gap-1.5 rounded-md bg-gradient-to-br from-indigo-600 to-violet-600 px-4 py-2.5 font-medium text-white shadow-sm transition hover:brightness-110 disabled:cursor-not-allowed disabled:from-slate-300 disabled:to-slate-300"
            >
              <Video className="h-4 w-4" />
              Activer la caméra
            </button>
          ) : (
            <button
              onClick={stopCamera}
              className="w-full rounded-md border border-slate-300 px-4 py-2.5 font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Arrêter la caméra
            </button>
          )}

          {cameraError && <p className="text-sm text-red-700">{cameraError}</p>}

          <form onSubmit={handleManualSubmit} className="space-y-2 border-t border-slate-200 pt-4">
            <label className="block text-sm">
              <span className="text-slate-700">Ou saisir le token du billet manuellement</span>
              <input
                value={manualToken}
                onChange={(e) => setManualToken(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                placeholder="42.abcdef..."
              />
            </label>
            <button
              type="submit"
              disabled={!scanKey || !manualToken.trim() || busy}
              className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? "Vérification..." : "Valider ce billet"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
