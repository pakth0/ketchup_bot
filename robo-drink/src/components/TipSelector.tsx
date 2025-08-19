"use client";

import React, { useEffect, useRef, useState } from "react";

type TipSelectorProps = {
  subtotalCents: number;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (tipCents: number) => void;
};

function formatMoneyFromCents(cents: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(cents / 100);
}

const TIP_PERCENTS = [15, 20, 25] as const;

export default function TipSelector({ subtotalCents, isOpen, onClose, onConfirm }: TipSelectorProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customInput, setCustomInput] = useState<string>("");
  const customRef = useRef<HTMLInputElement>(null);
  const [animateIn, setAnimateIn] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    setAnimateIn(false);
    const id = requestAnimationFrame(() => setAnimateIn(true));
    return () => cancelAnimationFrame(id);
  }, [isOpen]);

  // Start/stop camera when the tip screen opens/closes
  useEffect(() => {
    let stopped = false;
    async function startCamera() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
        if (stopped) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch {
        // ignore permission errors silently
      }
    }
    function stopCamera() {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
    if (isOpen) startCamera();
    else stopCamera();

    return () => {
      stopped = true;
      stopCamera();
    };
  }, [isOpen]);

  async function capturePhoto(): Promise<string | null> {
    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return null;
      const width = video.videoWidth;
      const height = video.videoHeight;
      if (!width || !height) return null;
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(video, 0, 0, width, height);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
      // try upload to get a clean URL
      try {
        const res = await fetch("/api/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dataUrl }),
        });
        if (res.ok) {
          const json = (await res.json()) as { url?: string };
          if (json.url) {
            try { window.localStorage.setItem("lastTipPhotoUrl", json.url); } catch {}
            return json.url;
          }
        }
      } catch {}
      try { window.localStorage.setItem("lastTipPhoto", dataUrl); } catch {}
      return null;
    } catch {
      return null;
    }
  }

  if (!isOpen) return null;

  const handlePercentClick = async (percent: number) => {
    const tipCents = Math.round((percent / 100) * subtotalCents);
    await capturePhoto();
    onConfirm(tipCents);
  };

  const handleNoTip = async () => {
    await capturePhoto();
    onConfirm(0);
  };

  const handleCustomOpen = () => {
    setShowCustom(true);
    setTimeout(() => customRef.current?.focus(), 0);
  };

  const handleCustomConfirm = async () => {
    const cents = Math.round(parseFloat(customInput || "0") * 100);
    if (!Number.isNaN(cents)) {
      await capturePhoto();
      onConfirm(Math.max(0, cents));
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-white text-black">
      {/* subtle background animation layer for transition */}
      <div className={`absolute inset-0 transition-transform duration-300 ${animateIn ? "scale-100" : "scale-105"}`} />
      <div
        className={`relative h-full w-full flex flex-col items-center px-6 py-8 transition-all duration-300 ${
          animateIn ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
        }`}
      >
        {/* Hidden video/canvas elements used for capture */}
        <video ref={videoRef} playsInline muted autoPlay className="hidden" />
        <canvas ref={canvasRef} className="hidden" />
        <div className="w-full max-w-2xl flex items-center justify-between">
          <button type="button" onClick={onClose} className="text-blue-600 text-base font-medium">Back</button>
          <h3 className="text-3xl font-semibold">Add a tip?</h3>
          <div className="opacity-0 select-none">Back</div>
        </div>

        <div className="mt-8 w-full max-w-2xl grid grid-cols-1 sm:grid-cols-3 gap-4">
          {TIP_PERCENTS.map((p) => {
            const tipCents = Math.round((p / 100) * subtotalCents);
            return (
              <button
                key={p}
                type="button"
                onClick={() => handlePercentClick(p)}
                className="rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-6 py-8 shadow-sm transition-colors"
              >
                <div className="text-3xl font-bold">{p}%</div>
                <div className="text-base mt-2 opacity-90">{formatMoneyFromCents(tipCents)}</div>
              </button>
            );
          })}
        </div>

        <div className="mt-6 w-full max-w-2xl">
          <button
            type="button"
            onClick={handleCustomOpen}
            className="w-full rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-5 text-lg font-semibold shadow-sm"
          >
            Custom
          </button>
          {showCustom ? (
            <div className="mt-4 flex items-center gap-3">
              <span className="text-xl">$</span>
              <input
                ref={customRef}
                inputMode="decimal"
                placeholder="0.00"
                className="flex-1 rounded-xl border border-black/10 px-4 py-4 bg-transparent text-xl"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value.replace(/[^0-9.]/g, ""))}
              />
              <button
                type="button"
                onClick={handleCustomConfirm}
                className="rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-4 text-lg font-semibold"
              >
                Confirm
              </button>
            </div>
          ) : null}
        </div>

        <div className="mt-4 w-full max-w-2xl">
          <button
            type="button"
            onClick={handleNoTip}
            className="w-full rounded-2xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-5 text-lg font-semibold shadow-sm"
          >
            No tip
          </button>
        </div>

        <div className="mt-8 text-center text-base text-black/60">
          Subtotal: {formatMoneyFromCents(subtotalCents)}
        </div>
      </div>
    </div>
  );
}


