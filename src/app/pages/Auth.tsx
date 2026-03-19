import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { getSession, loginWithPassword, loginWithProvider } from "../lib/api";
import { Button, Card, Input } from "../components/ui";

export function Auth() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@enterprise-ai.local");
  const [password, setPassword] = useState("demo123");
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getSession()) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate]);

  const handlePasswordLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading("password");
    setError("");

    try {
      await loginWithPassword(email, password);
      navigate("/dashboard", { replace: true });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Sign in failed.");
    } finally {
      setLoading(null);
    }
  };

  const handleProviderLogin = async (provider: "google" | "microsoft") => {
    setLoading(provider);
    setError("");

    try {
      await loginWithProvider(provider);
      navigate("/dashboard", { replace: true });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Provider sign in failed.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F9F8F4] p-4">
      <div className="absolute right-0 top-0 -mr-20 -mt-20 h-96 w-96 rounded-full bg-[#115E59]/5 blur-3xl" />
      <div className="absolute bottom-0 left-0 -mb-20 -ml-20 h-80 w-80 rounded-full bg-orange-500/5 blur-3xl" />

      <Card className="relative z-10 w-full max-w-md border-slate-200/60 p-8 shadow-2xl">
        <div className="mb-6 flex justify-center">
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[10px] font-bold tracking-widest text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-orange-500 animate-pulse" />
            ET GENAI HACKATHON SUBMISSION
          </div>
        </div>

        <div className="mb-8 text-center">
          <h1 className="font-serif text-3xl font-bold text-slate-900">Sign In</h1>
          <p className="mt-3 text-sm font-medium text-slate-600">Full-stack enterprise AI workspace with all 20 modules wired to a live backend.</p>
        </div>

        <form onSubmit={handlePasswordLogin} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700" htmlFor="email">
              User ID / Email
            </label>
            <Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700" htmlFor="password">
              Password
            </label>
            <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </div>

          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}

          <Button type="submit" className="w-full" disabled={loading !== null}>
            {loading === "password" ? "Signing In..." : "Sign In"}
          </Button>
        </form>

        <div className="mt-6 flex items-center justify-center space-x-2 text-sm text-slate-500">
          <span className="h-px w-full bg-slate-200" />
          <span className="shrink-0 px-2">or continue with</span>
          <span className="h-px w-full bg-slate-200" />
        </div>

        <div className="mt-6 space-y-3">
          <Button variant="outline" className="w-full" type="button" onClick={() => handleProviderLogin("google")} disabled={loading !== null}>
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            {loading === "google" ? "Connecting Google..." : "Sign in with Google"}
          </Button>

          <Button variant="outline" className="w-full" type="button" onClick={() => handleProviderLogin("microsoft")} disabled={loading !== null}>
            <svg className="mr-2 h-4 w-4" viewBox="0 0 21 21">
              <path fill="#f25022" d="M1 1h9v9H1z" />
              <path fill="#00a4ef" d="M1 11h9v9H1z" />
              <path fill="#7fba00" d="M11 1h9v9h-9z" />
              <path fill="#ffb900" d="M11 11h9v9h-9z" />
            </svg>
            {loading === "microsoft" ? "Connecting Microsoft..." : "Sign in with Microsoft"}
          </Button>
        </div>

        <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
          Local demo credentials are prefilled. You can also use the Google and Microsoft buttons for demo SSO sessions backed by the new API.
        </div>
      </Card>
    </div>
  );
}
