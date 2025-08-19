"use client";

import React, { useState } from "react";

type ApiControlsProps = {
  className?: string;
};

export default function ApiControls({ className }: ApiControlsProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [fireableState, setFireableState] = useState<boolean | null>(null);
  const [trackingMode, setTrackingMode] = useState<string>("off");
  const [solenoidState, setSolenoidState] = useState<boolean | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:80";

  const callApi = async (endpoint: string, params?: { mode?: string }) => {
    setIsLoading(endpoint);
    try {
      let url = `${API_BASE_URL}${endpoint}`;
      
      // Add query parameters for POST endpoints
      if (params?.mode) {
        url += `?mode=${encodeURIComponent(params.mode)}`;
      }

      const options: RequestInit = {
        method: params ? "POST" : "GET",
        headers: {
          "Content-Type": "application/json",
        },
      };

      const response = await fetch(url, options);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || "API call failed");
      }
      
      return result;
    } catch (error) {
      console.error(`API call to ${endpoint} failed:`, error);
      alert(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsLoading(null);
    }
  };

  const toggleFireable = async (mode: "on" | "off") => {
    await callApi("/toggle_fireable", { mode });
    setFireableState(mode === "on");
  };

  const setTrackMode = async (mode: "face" | "hotdog" | "off") => {
    await callApi("/track_mode", { mode });
    setTrackingMode(mode);
  };

  const toggleSolenoid = async (mode: "on" | "off") => {
    await callApi("/solenoid", { mode });
    setSolenoidState(mode === "on");
  };

  const reset = async () => {
    await callApi("/reset");
    // Reset local state
    setFireableState(null);
    setTrackingMode("off");
    setSolenoidState(null);
  };

  const buttonBaseClass = "px-3 py-2 text-sm font-medium rounded-lg border transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const primaryButtonClass = `${buttonBaseClass} bg-blue-600 hover:bg-blue-700 text-white border-blue-600`;
  const secondaryButtonClass = `${buttonBaseClass} bg-white hover:bg-gray-50 text-gray-700 border-gray-300`;
  const dangerButtonClass = `${buttonBaseClass} bg-red-600 hover:bg-red-700 text-white border-red-600`;
  const successButtonClass = `${buttonBaseClass} bg-green-600 hover:bg-green-700 text-white border-green-600`;

  return (
    <div className={`bg-white rounded-2xl border border-black/10 shadow-lg p-3 max-w-xs backdrop-blur-sm bg-white/95 ${className}`}>
      <h3 className="text-sm font-semibold mb-3 text-center">Robot Controls</h3>
      
      {/* Fireable Toggle */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">Fireable</label>
        <div className="flex gap-1">
          <button
            onClick={() => toggleFireable("on")}
            disabled={isLoading === "/toggle_fireable"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              fireableState === true 
                ? "bg-green-600 hover:bg-green-700 text-white border-green-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            ON
          </button>
          <button
            onClick={() => toggleFireable("off")}
            disabled={isLoading === "/toggle_fireable"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              fireableState === false 
                ? "bg-red-600 hover:bg-red-700 text-white border-red-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            OFF
          </button>
        </div>
      </div>

      {/* Tracking Mode */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">Tracking</label>
        <div className="grid grid-cols-3 gap-1">
          <button
            onClick={() => setTrackMode("face")}
            disabled={isLoading === "/track_mode"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              trackingMode === "face" 
                ? "bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            Face
          </button>
          <button
            onClick={() => setTrackMode("hotdog")}
            disabled={isLoading === "/track_mode"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              trackingMode === "hotdog" 
                ? "bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            Dog
          </button>
          <button
            onClick={() => setTrackMode("off")}
            disabled={isLoading === "/track_mode"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              trackingMode === "off" 
                ? "bg-red-600 hover:bg-red-700 text-white border-red-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            Off
          </button>
        </div>
      </div>

      {/* Solenoid Control */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">Solenoid</label>
        <div className="flex gap-1">
          <button
            onClick={() => toggleSolenoid("on")}
            disabled={isLoading === "/solenoid"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              solenoidState === true 
                ? "bg-green-600 hover:bg-green-700 text-white border-green-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            ON
          </button>
          <button
            onClick={() => toggleSolenoid("off")}
            disabled={isLoading === "/solenoid"}
            className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              solenoidState === false 
                ? "bg-red-600 hover:bg-red-700 text-white border-red-600"
                : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
            }`}
          >
            OFF
          </button>
        </div>
      </div>

      {/* Reset Button */}
      <div>
        <button
          onClick={reset}
          disabled={isLoading === "/reset"}
          className="px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-red-600 hover:bg-red-700 text-white border-red-600 w-full"
        >
          {isLoading === "/reset" ? "Resetting..." : "Reset"}
        </button>
      </div>
    </div>
  );
}
