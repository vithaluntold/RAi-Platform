"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL, setAuthToken } from "./lib";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      // Send login credentials to backend
      const formData = new URLSearchParams();
      formData.append("username", email); // OAuth2PasswordRequestForm expects 'username'
      formData.append("password", password);

      const response = await fetch(`${API_BASE_URL}/api/v1/login/access-token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      const data = await response.json();
      
      // Store the JWT token
      setAuthToken(data.access_token);
      
      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Panel — Branding */}
      <div className="hidden lg:flex lg:w-120 xl:w-135 flex-col justify-between bg-sidebar-bg p-10 relative overflow-hidden">
        {/* Geometric pattern overlay */}
        <div className="absolute inset-0 opacity-[0.03]">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        {/* Accent glow */}
        <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-accent/10 rounded-full blur-[100px]" />
        <div className="absolute top-1/3 -right-20 w-60 h-60 bg-accent/5 rounded-full blur-[80px]" />

        <div className="relative z-10">
          <span className="text-[#4A90D9] text-3xl font-bold tracking-tight">RAI</span>
        </div>

        <div className="relative z-10 space-y-6">
          <h1 className="text-white text-3xl xl:text-4xl font-semibold leading-tight tracking-tight">
            Regulatory Intelligence,<br />
            <span className="text-accent-light">Automated.</span>
          </h1>
          <p className="text-sidebar-text text-base leading-relaxed max-w-sm">
            Streamline compliance workflows, manage regulatory documents, and ensure audit readiness with AI-powered intelligence.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-2 pt-2">
            {["Compliance Tracking", "Document Analysis", "Audit Ready", "AI-Powered"].map((feature) => (
              <span
                key={feature}
                className="px-3 py-1.5 text-xs font-medium text-sidebar-text bg-white/4 border border-white/6 rounded-full"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-sidebar-text text-xs">
          &copy; {new Date().getFullYear()} RAi. All rights reserved.
        </div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10 bg-background">
        <div className="w-full max-w-100 animate-fade-in">
          <div className="mb-10 lg:hidden">
            <span className="text-[#4A90D9] text-2xl font-bold tracking-tight">RAI</span>
          </div>

          <div className="mb-8">
            <h2 className="text-text-primary text-2xl font-semibold tracking-tight">
              Welcome back
            </h2>
            <p className="text-text-secondary text-sm mt-1.5">
              Sign in to your account to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="px-3.5 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Email */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-text-primary text-sm font-medium">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                required
                className="w-full h-11 px-3.5 text-sm text-text-primary bg-surface border border-border rounded-lg
                  placeholder:text-text-muted
                  focus:border-accent focus:ring-2 focus:ring-accent/10
                  transition-all duration-150"
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-text-primary text-sm font-medium">
                  Password
                </label>
                <button type="button" className="text-xs text-accent hover:text-accent-light transition-colors font-medium">
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full h-11 px-3.5 pr-10 text-sm text-text-primary bg-surface border border-border rounded-lg
                    placeholder:text-text-muted
                    focus:border-accent focus:ring-2 focus:ring-accent/10
                    transition-all duration-150"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Remember me */}
            <div className="flex items-center gap-2">
              <input
                id="remember"
                type="checkbox"
                className="w-4 h-4 rounded border-border text-accent focus:ring-accent/20 cursor-pointer accent-accent"
              />
              <label htmlFor="remember" className="text-sm text-text-secondary cursor-pointer select-none">
                Keep me signed in
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-11 bg-accent hover:bg-accent-light text-white text-sm font-medium rounded-lg
                transition-all duration-150 active:scale-[0.98]
                disabled:opacity-70 disabled:cursor-not-allowed
                flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="text-center text-xs text-text-muted mt-8">
            Protected by enterprise-grade security
          </p>
        </div>
      </div>
    </div>
  );
}
