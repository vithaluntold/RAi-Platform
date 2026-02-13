// useLocalStorage hook - persist state to localStorage
"use client";

import { useState } from "react";

export const useLocalStorage = <T,>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    const item = window.localStorage.getItem(key);
    if (item) {
      try {
        return JSON.parse(item) as T;
      } catch (e) {
        console.error(`Failed to parse localStorage item ${key}:`, e);
        return initialValue;
      }
    }
    return initialValue;
  });
  const [isLoaded] = useState(true);

  // Update localStorage when state changes
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (e) {
      console.error(`Failed to set localStorage item ${key}:`, e);
    }
  };

  return [storedValue, setValue, isLoaded] as const;
};
