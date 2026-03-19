import React, { useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router";

import { liveTools, previewFeatures } from "../data/features";
import { clearSession, getSession } from "../lib/api";
import { Button, cn } from "./ui";

export function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = getSession();

  useEffect(() => {
    if (!session) {
      navigate("/", { replace: true });
    }
  }, [navigate, session]);

  if (!session) {
    return null;
  }

  const handleLogout = () => {
    clearSession();
    navigate("/", { replace: true });
  };

  return (
    <div className="flex min-h-screen bg-[#F9F8F4] font-sans text-slate-900">
      <aside className="hidden w-80 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="border-b border-slate-200 p-6">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#115E59] text-white shadow-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <div className="font-serif text-xl font-bold text-slate-900">Enterprise AI</div>
              <div className="text-xs font-medium uppercase tracking-widest text-slate-400">{session.user.workspace}</div>
            </div>
          </Link>
        </div>

        <div className="border-b border-slate-200 bg-slate-50/60 px-6 py-5">
          <div className="text-xs font-bold uppercase tracking-widest text-slate-400">Signed In</div>
          <div className="mt-2 text-sm font-semibold text-slate-900">{session.user.name}</div>
          <div className="mt-1 text-sm text-slate-500">{session.user.email}</div>
          <div className="mt-3 inline-flex rounded-full bg-[#115E59]/10 px-3 py-1 text-xs font-semibold text-[#115E59]">
            {session.user.provider === "password" ? "Password Session" : `${session.user.provider} Demo SSO`}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <nav className="space-y-8">
            <div>
              <Link
                to="/dashboard"
                className={cn(
                  "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                  location.pathname === "/dashboard"
                    ? "bg-[#115E59]/10 text-[#115E59]"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                Dashboard Home
              </Link>
            </div>

            <div>
              <div className="px-4 text-xs font-bold uppercase tracking-widest text-slate-400">Live Tools</div>
              <div className="mt-3 space-y-1">
                {liveTools.map((tool) => {
                  const isActive = location.pathname === `/dashboard/${tool.id}`;
                  return (
                    <Link
                      key={tool.id}
                      to={`/dashboard/${tool.id}`}
                      className={cn(
                        "block rounded-xl px-4 py-3 text-sm transition-colors",
                        isActive ? "bg-[#115E59] text-white shadow-sm" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                      )}
                    >
                      {tool.title}
                    </Link>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="px-4 text-xs font-bold uppercase tracking-widest text-slate-400">Expanded Modules</div>
              <div className="mt-3 space-y-1">
                {previewFeatures.map((tool) => {
                  const isActive = location.pathname === `/dashboard/${tool.id}`;
                  return (
                    <Link
                      key={tool.id}
                      to={`/dashboard/${tool.id}`}
                      className={cn(
                        "flex items-center justify-between rounded-xl px-4 py-3 text-sm transition-colors",
                        isActive ? "bg-orange-100 text-orange-900" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      )}
                    >
                      <span className="truncate">{tool.title}</span>
                      <span className="text-[10px] font-bold uppercase tracking-widest opacity-70">Beta</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          </nav>
        </div>

        <div className="border-t border-slate-200 bg-slate-50 p-4">
          <Button variant="outline" className="w-full" onClick={handleLogout}>
            Sign Out
          </Button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4 lg:hidden">
          <Link to="/dashboard" className="font-serif text-xl font-bold text-slate-900">
            Enterprise AI
          </Link>
          <div className="flex items-center gap-2">
            <Link to="/dashboard">
              <Button variant="outline" size="sm">
                Home
              </Button>
            </Link>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Sign Out
            </Button>
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
