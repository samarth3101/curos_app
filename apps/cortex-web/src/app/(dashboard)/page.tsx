import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Cortex OI",
  description: "Cortex OI Dashboard",
};

/**
 * Dashboard placeholder.
 * This will be replaced with the real dashboard when product features are built.
 */
export default function DashboardPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-6 text-center">
        <div className="space-y-2">
          <p className="text-sm font-semibold tracking-widest uppercase text-neutral-500">
            Curos
          </p>
          <h1 className="text-4xl font-bold tracking-tight">
            Cortex OI
          </h1>
          <p className="text-lg text-neutral-600">
            Organizational Intelligence Platform
          </p>
        </div>

        <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-6 text-left space-y-3">
          <h2 className="font-semibold text-neutral-800">Engineering Foundation</h2>
          <ul className="text-sm text-neutral-600 space-y-1">
            <li>✅ FastAPI backend (Python 3.13)</li>
            <li>✅ Next.js 16 frontend (TypeScript strict)</li>
            <li>✅ PostgreSQL + Redis via Docker Compose</li>
            <li>✅ Alembic migrations configured</li>
            <li>✅ Ruff + MyPy + Pytest configured</li>
            <li>✅ pnpm workspaces + uv</li>
            <li>✅ Clean Architecture module structure</li>
            <li>✅ JWT/OIDC-ready identity abstraction</li>
            <li>⏳ Product features — coming next</li>
          </ul>
        </div>

        <div className="text-xs text-neutral-400">
          Health check:{" "}
          <a
            href="http://localhost:8000/api/v1/health/ready"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-neutral-600 transition-colors"
          >
            localhost:8000/api/v1/health/ready
          </a>
        </div>
      </div>
    </main>
  );
}
