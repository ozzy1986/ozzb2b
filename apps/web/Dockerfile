FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json ./
# React 19 RC + @testing-library/react 16 require --legacy-peer-deps.
# Lockfile is intentionally not committed; the image generates its own on
# each build so rollup's platform-specific optional binaries resolve.
RUN --mount=type=cache,target=/root/.npm \
    npm install --legacy-peer-deps --no-audit --no-fund

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
# Remove build-time tools that Next's standalone runtime does not need. This
# shrinks the attack surface (npm bundles its own transitive deps like
# picomatch that Trivy otherwise flags on every scan) and aligns with the
# "runtime image should only contain what runs" rule.
RUN rm -rf \
    /usr/local/lib/node_modules/npm \
    /usr/local/lib/node_modules/corepack \
    /usr/local/bin/npm \
    /usr/local/bin/npx \
    /usr/local/bin/corepack \
    /opt/yarn-*

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD wget -qO- http://127.0.0.1:3000/api/health || exit 1

CMD ["node", "server.js"]
