"use client";

import { useState, useEffect, useCallback } from "react";

export interface RobotState {
  fireableState: boolean | null;
  trackingMode: string;
  solenoidState: boolean | null;
  releaseTime: number;
  isLoading: string | null;
}

export interface RobotActions {
  toggleFireable: (mode: "on" | "off") => Promise<void>;
  setTrackMode: (mode: "face" | "hotdog" | "off") => Promise<void>;
  toggleSolenoid: (mode: "on" | "off") => Promise<void>;
  reset: () => Promise<void>;
  setReleaseTimeValue: (time: number) => Promise<void>;
}

export function useRobotState(): [RobotState, RobotActions] {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [fireableState, setFireableState] = useState<boolean | null>(null);
  const [trackingMode, setTrackingMode] = useState<string>("off");
  const [solenoidState, setSolenoidState] = useState<boolean | null>(null);
  const [releaseTime, setReleaseTime] = useState<number>(0.5);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";

  const fetchCurrentState = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/all`);
      if (response.ok) {
        const status = await response.json();
        setFireableState(status.fireable);
        setTrackingMode(status.tracking_mode || "off");
        setReleaseTime(status.release_time || 0.5);
      }
    } catch (error) {
      console.error("Failed to fetch current state:", error);
    }
  }, [API_BASE_URL]);

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
      
      // Fetch updated state after successful API call
      await fetchCurrentState();
      
      return result;
    } catch (error) {
      console.error(`API call to ${endpoint} failed:`, error);
      // Don't show alerts during tip/success screens to avoid interrupting user flow
      if (typeof window !== 'undefined' && !window.location.hash.includes('tip')) {
        alert(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      }
    } finally {
      setIsLoading(null);
    }
  };

  const toggleFireable = async (mode: "on" | "off") => {
    await callApi("/toggle_fireable", { mode });
  };

  const setTrackMode = async (mode: "face" | "hotdog" | "off") => {
    await callApi("/track_mode", { mode });
  };

  const toggleSolenoid = async (mode: "on" | "off") => {
    await callApi("/solenoid", { mode });
    setSolenoidState(mode === "on");
  };

  const reset = async () => {
    await callApi("/reset");
  };

  const setReleaseTimeValue = async (time: number) => {
    setIsLoading("/set_release_time");
    try {
      const response = await fetch(`${API_BASE_URL}/set_release_time?release_time=${time}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.error || "Failed to set release time");
      }
      
      // Fetch updated state after successful API call
      await fetchCurrentState();
      
    } catch (error) {
      console.error(`Failed to set release time:`, error);
      // Don't show alerts during tip/success screens
      if (typeof window !== 'undefined' && !window.location.hash.includes('tip')) {
        alert(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      }
    } finally {
      setIsLoading(null);
    }
  };

  // Initial state fetch and persistent polling
  useEffect(() => {
    // Fetch initial state
    fetchCurrentState();

    // Set up polling interval (every 3 seconds, slightly slower to reduce load)
    const interval = setInterval(() => {
      if (!isLoading) { // Don't poll while an API call is in progress
        fetchCurrentState();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [fetchCurrentState, isLoading]);

  const state: RobotState = {
    fireableState,
    trackingMode,
    solenoidState,
    releaseTime,
    isLoading,
  };

  const actions: RobotActions = {
    toggleFireable,
    setTrackMode,
    toggleSolenoid,
    reset,
    setReleaseTimeValue,
  };

  return [state, actions];
}
