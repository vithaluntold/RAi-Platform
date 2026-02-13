// useAuth hook - manage authentication state
"use client";

import { useState, useEffect, useCallback } from "react";
import { getAuthToken } from "@/lib";
import { authApi } from "@/api/auth";
import { LoginRequest } from "@/types/auth";
import { User } from "@/types/user";

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user has token on mount
  useEffect(() => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      setLoading(true);
      setError(null);
      try {
        await authApi.login(credentials);
        setIsAuthenticated(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await authApi.logout();
      setIsAuthenticated(false);
      setUser(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Logout failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    isAuthenticated,
    user,
    loading,
    error,
    login,
    logout,
  };
};
