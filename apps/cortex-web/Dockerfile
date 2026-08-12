# ---- cortex-web Dockerfile ----
FROM node:20-alpine AS base

RUN corepack enable && corepack prepare pnpm@9.12.0 --activate

WORKDIR /app

# ---- development ----
FROM base AS development

# Copy workspace config
COPY package.json pnpm-workspace.yaml ./
COPY apps/cortex-web/package.json ./apps/cortex-web/
COPY packages/ ./packages/

RUN pnpm install --filter cortex-web

COPY apps/cortex-web/ ./apps/cortex-web/

WORKDIR /app/apps/cortex-web

EXPOSE 3000
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]

# ---- builder ----
FROM base AS builder

COPY package.json pnpm-workspace.yaml ./
COPY apps/cortex-web/package.json ./apps/cortex-web/
COPY packages/ ./packages/

RUN pnpm install --filter cortex-web --frozen-lockfile

COPY apps/cortex-web/ ./apps/cortex-web/

WORKDIR /app/apps/cortex-web

RUN pnpm build

# ---- production ----
FROM node:20-alpine AS production

WORKDIR /app

RUN addgroup --system cortex && adduser --system --group cortex

COPY --from=builder /app/apps/cortex-web/.next/standalone ./
COPY --from=builder /app/apps/cortex-web/.next/static ./apps/cortex-web/.next/static
COPY --from=builder /app/apps/cortex-web/public ./apps/cortex-web/public

USER cortex

EXPOSE 3000
ENV PORT=3000 HOSTNAME="0.0.0.0"
CMD ["node", "apps/cortex-web/server.js"]
