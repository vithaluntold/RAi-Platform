"use client";

import { useEffect } from "react";

interface ErrorBoundaryProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ComplianceError({ error, reset }: ErrorBoundaryProps) {
  useEffect(() => {
    console.error("Compliance module error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-8">
      <div className="max-w-md rounded-xl border border-red-300 bg-red-50 p-8 text-center dark:border-red-800 dark:bg-red-950">
        <div className="mb-4 text-4xl">⚠️</div>
        <h2 className="mb-2 text-lg font-semibold text-red-800 dark:text-red-200">
          Something went wrong
        </h2>
        <p className="mb-6 text-sm text-red-600 dark:text-red-400">
          {error.message || "An unexpected error occurred in the compliance module."}
        </p>
        <button
          onClick={reset}
          className="rounded-lg bg-red-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
