"use client";

import React, { useState } from "react";
import type { RobotState, RobotActions } from "@/hooks/useRobotState";

type ApiControlsProps = {
  className?: string;
  robotState: RobotState;
  robotActions: RobotActions;
};

export default function ApiControls({ className, robotState, robotActions }: ApiControlsProps) {
  const { fireableState, trackingMode, solenoidState, releaseTime, isLoading } = robotState;
  const { toggleFireable, setTrackMode, toggleSolenoid, reset, setReleaseTimeValue } = robotActions;
  
  // Local state for release time to provide immediate UI feedback
  const [localReleaseTime, setLocalReleaseTime] = useState(releaseTime);
  
  // Update local state when prop changes (from polling)
  React.useEffect(() => {
    setLocalReleaseTime(releaseTime);
  }, [releaseTime]);



  return (
    <div className={`bg-white rounded-2xl border border-black/10 shadow-lg p-3 max-w-xs backdrop-blur-sm bg-white/95 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">Robot Controls</h3>
        <div className={`w-2 h-2 rounded-full bg-green-500`} 
             title="Live sync enabled" />
      </div>
      
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
            Burger
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

      {/* Release Time Control */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Release Time: {localReleaseTime}s
        </label>
        <div className="space-y-1">
          <input
            type="range"
            min="0.1"
            max="10.0"
            step="0.1"
            value={localReleaseTime}
            onChange={(e) => {
              const newTime = parseFloat(e.target.value);
              setLocalReleaseTime(newTime);
              setReleaseTimeValue(newTime);
            }}
            disabled={isLoading === "/set_release_time"}
            className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>0.1s</span>
            <span>10s</span>
          </div>
          <div className="grid grid-cols-4 gap-1">
            {[0.5, 1.0, 2.0, 5.0].map((time) => (
              <button
                key={time}
                onClick={() => {
                  setLocalReleaseTime(time);
                  setReleaseTimeValue(time);
                }}
                disabled={isLoading === "/set_release_time"}
                className={`px-2 py-1 text-xs font-medium rounded border transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  Math.abs(localReleaseTime - time) < 0.05
                    ? "bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                    : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
                }`}
              >
                {time}s
              </button>
            ))}
          </div>
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
