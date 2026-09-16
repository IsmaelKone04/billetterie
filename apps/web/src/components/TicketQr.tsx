"use client";

import QRCode from "qrcode";
import { useEffect, useState } from "react";

export default function TicketQr({ token }: { token: string }) {
  const [dataUrl, setDataUrl] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    QRCode.toDataURL(token, { width: 220, margin: 1 }).then((url) => {
      if (!cancelled) setDataUrl(url);
    });
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (!dataUrl) {
    return <div className="h-[220px] w-[220px] animate-pulse rounded-md bg-slate-100" />;
  }

  // QR généré côté client en data URL, pas une image à optimiser par next/image.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={dataUrl} alt="QR code du billet" width={220} height={220} />;
}
