"use client";

import { useMemo } from "react";

export interface ComplianceTheme {
  bg: string;
  surface: string;
  surfaceAlt: string;
  border: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  hoverBg: string;
  inputBg: string;
  activeBg: string;
}

export function useComplianceTheme(darkMode: boolean): ComplianceTheme {
  return useMemo(
    () => ({
      bg: darkMode ? "bg-[#0d1117]" : "bg-gray-50",
      surface: darkMode ? "bg-[#161b22]" : "bg-white",
      surfaceAlt: darkMode ? "bg-[#1c2128]" : "bg-gray-100",
      border: darkMode ? "border-[#30363d]" : "border-gray-200",
      textPrimary: darkMode ? "text-gray-100" : "text-gray-900",
      textSecondary: darkMode ? "text-gray-400" : "text-gray-600",
      textMuted: darkMode ? "text-gray-500" : "text-gray-400",
      hoverBg: darkMode ? "hover:bg-[#1c2128]" : "hover:bg-gray-100",
      inputBg: darkMode ? "bg-[#0d1117]" : "bg-gray-50",
      activeBg: darkMode
        ? "bg-[#1f6feb]/10 border-[#1f6feb]/40"
        : "bg-blue-50 border-blue-300",
    }),
    [darkMode]
  );
}
