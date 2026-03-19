# ==============================================================================
# LitigationOS — Self-Hosted Deployment
# Multi-stage build: Node 20, Next.js, better-sqlite3
# ==============================================================================

# --- Stage 1: Dependencies ---
FROM node:20-alpine AS deps
RUN apk add --no-cache python3 make g++ sqlite-dev
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev && \
    npm rebuild better-sqlite3

# --- Stage 2: Build ---
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# --- Stage 3: Production Runtime ---
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN apk add --no-cache sqlite-libs tini && \
    addgroup --system --gid 1001 litigos && \
    adduser --system --uid 1001 litigos

# Copy built assets
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Data directory for SQLite databases
RUN mkdir -p /app/data /app/backups && \
    chown -R litigos:litigos /app/data /app/backups

VOLUME ["/app/data", "/app/backups"]

USER litigos
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["node", "server.js"]
