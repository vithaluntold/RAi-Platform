// useFetch hook - simplify data fetching
"use client";

import { useState, useEffect } from "react";
import { apiCall } from "@/lib";

interface UseFetchOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  skip?: boolean;
}

export const useFetch = <T,>(
  endpoint: string,
  options: UseFetchOptions = {}
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (options.skip) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiCall<T>(endpoint, {
          method: options.method || "GET",
        });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint, options.skip, options.method]);

  return { data, loading, error };
};
