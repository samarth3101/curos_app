# Frontend Architecture

## Overview

Cortex OI web frontend is built with **Next.js 16** (App Router), TypeScript strict mode, and Tailwind CSS v4.

## Directory Structure

```
src/
├── app/                    # Next.js App Router pages and layouts
│   ├── layout.tsx          # Root layout (fonts, global CSS)
│   ├── page.tsx            # Root redirect → /dashboard
│   └── (dashboard)/        # Dashboard route group
├── components/
│   └── ui/                 # Design system primitives (buttons, inputs, etc.)
├── features/               # Feature-specific components, hooks, and logic
│   └── <feature>/
│       ├── components/
│       ├── hooks/
│       └── services/
├── lib/
│   ├── api.ts              # Axios instance (baseURL + auth interceptor)
│   └── utils.ts            # Shared utilities (cn, formatDate, etc.)
├── hooks/                  # Shared custom React hooks
├── services/               # API service functions (call lib/api.ts)
├── stores/                 # Zustand global state stores
└── types/
    └── api.generated.ts    # AUTO-GENERATED — do not edit manually
```

## Type Generation

Frontend TypeScript types are **auto-generated** from the backend OpenAPI spec:

```bash
# Requires cortex-api running
pnpm --filter @curos/types generate
```

This calls `openapi-typescript` and outputs to `packages/types/src/api.generated.ts`.

**Never hand-write types that mirror backend schemas.** Always regenerate.

## State Management

- **Server state**: Fetch directly in Server Components or via service functions
- **Client state**: Zustand stores in `src/stores/`
- **Form state**: React Hook Form (add when forms are built)
- **Auth state**: Zustand store in `src/stores/auth.ts` (future)

## API Communication

All HTTP calls go through `src/lib/api.ts` (Axios instance):
- `baseURL` = `process.env.NEXT_PUBLIC_API_URL`
- Automatic `Authorization: Bearer <token>` injection
- Structured backend error unpacking

## Key Rules

1. Feature-specific logic lives in `features/<feature>/` — not in `components/`
2. `components/ui/` is design system only — no business logic
3. Server Components by default; `"use client"` only when needed
4. No direct `fetch()` calls in components — use service functions
