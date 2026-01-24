# Frontend Dockerfile for AI-Powered Resume Analysis System
# Multi-stage build for optimized production image

# Stage 1: Dependencies
FROM node:20-alpine AS deps

# Install dependencies based on package manager
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build application
RUN npm run build

# Stage 3: Runner (Production)
FROM node:20-alpine AS runner

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache curl

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application from builder
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/node_modules/.vite /app/node_modules/.vite
COPY --from=builder /app/package.json /app/package.json

# Set permissions
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5173/ || exit 1

# Development mode command (for docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production command (use with nginx or serve)
# CMD ["npx", "serve", "-s", "dist", "-l", "5173"]
