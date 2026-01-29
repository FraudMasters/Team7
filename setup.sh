#!/bin/bash
# TEAM7 Resume Analysis Platform - Local Setup Script
# One-command setup for local development

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TEAM7 Resume Analysis Platform${NC}"
echo -e "${BLUE}  Local Development Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker Desktop first.${NC}"
    echo "  https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not available. Please install Docker Desktop with Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}   Docker is installed${NC}"
echo ""

# 2. Create .env file
echo -e "${YELLOW}[2/6] Setting up environment...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}   Created .env from .env.example${NC}"
    else
        cat > .env << 'EOF'
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=resume_analysis

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Optional: Add your API keys for enhanced features
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
EOF
        echo -e "${GREEN}   Created .env with defaults${NC}"
    fi
else
    echo -e "${GREEN}   .env already exists${NC}"
fi
echo ""

# 3. Create necessary directories
echo -e "${YELLOW}[3/6] Creating directories...${NC}"
mkdir -p backend/models_cache
mkdir -p backend/data/uploads
echo -e "${GREEN}   Directories created${NC}"
echo ""

# 4. Stop any existing containers
echo -e "${YELLOW}[4/6] Stopping existing containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
echo -e "${GREEN}   Cleaned up old containers${NC}"
echo ""

# 5. Build and start services
echo -e "${YELLOW}[5/6] Building and starting services...${NC}"
echo "   This may take 5-10 minutes on first run..."
echo ""

# Start database and Redis first
docker-compose up -d postgres redis

# Wait for database
echo "   Waiting for database..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}   Database is ready${NC}"
        break
    fi
    sleep 1
done

# Build and start all services
docker-compose build
docker-compose up -d
echo ""

# 6. Wait for services and health check
echo -e "${YELLOW}[6/6] Verifying services...${NC}"
sleep 10

# Check backend
for i in {1..20}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}   Backend is healthy${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${YELLOW}   Backend may still be starting... Check logs with: docker-compose logs backend${NC}"
    fi
    sleep 2
done

# Check frontend
if curl -sf http://localhost:5173/ > /dev/null 2>&1; then
    echo -e "${GREEN}   Frontend is healthy${NC}"
else
    echo -e "${YELLOW}   Frontend may still be starting...${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services running at:"
echo "  - Frontend:        ${BLUE}http://localhost:5173${NC}"
echo "  - Backend API:     ${BLUE}http://localhost:8000${NC}"
echo "  - API Docs:        ${BLUE}http://localhost:8000/docs${NC}"
echo "  - Flower Monitor:  ${BLUE}http://localhost:5555${NC}"
echo ""
echo "Useful commands:"
echo "  - View logs:       ${YELLOW}docker-compose logs -f${NC}"
echo "  - Stop services:   ${YELLOW}docker-compose down${NC}"
echo "  - Restart:         ${YELLOW}docker-compose restart${NC}"
echo ""
echo "Load test data (65 resumes + 5 vacancies):"
echo "  - ${YELLOW}bash scripts/load_test_data.sh${NC}"
echo ""
