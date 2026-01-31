# Frontend Dockerfile for AI-Powered Resume Analysis System
# Multi-stage build for optimized production image

# Stage 1: Builder
FROM node:20 AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Workaround for rollup ARM64 bug - install missing binary manually
RUN npm install @rollup/rollup-linux-arm64-gnu --no-save || \
    npm install @rollup/rollup-linux-arm64-musl --no-save || \
    npm install @rollup/rollup-darwin-arm64 --no-save || \
    true

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build application
RUN npm run build

# Stage 2: Production Runner (uses nginx to serve static files)
FROM nginx:alpine AS production

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Stage 3: Development Runner
FROM node:20 AS development

WORKDIR /app

# Copy package files
COPY package.json ./

# Install all dependencies (including platform-specific binaries)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Install curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5173/ || exit 1

# Development mode command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
