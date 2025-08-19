"use client";

import React, { useEffect, useState } from "react";

type SuccessScreenProps = {
  isOpen: boolean;
  onClose: () => void;
  autoCloseMs?: number;
  tipAmount?: number;
};

export default function SuccessScreen({ isOpen, onClose, autoCloseMs = 1600, tipAmount = 0 }: SuccessScreenProps) {
  const [animateIn, setAnimateIn] = useState(false);
  const [configuring, setConfiguring] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setAnimateIn(false);
    setConfiguring(false);
    const raf = requestAnimationFrame(() => setAnimateIn(true));
    
    // Start showing configuration message after 1 second
    const configTimer = setTimeout(() => setConfiguring(true), 1000);
    
    const timer = setTimeout(() => onClose(), autoCloseMs);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(timer);
      clearTimeout(configTimer);
    };
  }, [isOpen, onClose, autoCloseMs]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-white text-black flex items-center justify-center">
      <div
        className={`flex flex-col items-center transition-all duration-300 ${
          animateIn ? "opacity-100 translate-y-0 scale-100" : "opacity-0 translate-y-2 scale-95"
        }`}
      >
        <div className="h-32 w-32 rounded-full bg-blue-600 flex items-center justify-center shadow-md">
          <svg
            viewBox="0 0 24 24"
            className="h-16 w-16 text-white"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M20 6L9 17l-5-5" />
          </svg>
        </div>
        <p className="mt-6 text-2xl font-semibold">You're all set!</p>
        
        {configuring && (
          <div className="mt-4 text-center">
            <div className="text-sm text-gray-600 mb-2">🤖 Configuring robot...</div>
            {tipAmount === 0 ? (
              <div className="text-sm font-medium text-red-600">
                🎯 Face targeting mode activated<br/>
                <span className="text-xs text-gray-500">No tip = mischief mode 😈</span>
              </div>
            ) : (
              <div className="text-sm font-medium text-green-600">
                🌭 Hotdog targeting mode activated<br/>
                <span className="text-xs text-gray-500">Thanks for the tip! 😊</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


