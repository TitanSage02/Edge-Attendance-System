#!/bin/bash
# Docker build script for Edge Attendance System Backend
# This script ensures clean builds and proper permissions

echo "🐳 Building Edge Attendance System Backend Docker Image..."

# Ensure proper permissions
chmod +x docker-entrypoint.sh

# Fix line endings if dos2unix is available
if command -v dos2unix >/dev/null 2>&1; then
    echo "🔧 Fixing line endings..."
    dos2unix docker-entrypoint.sh
fi

# Stop and remove any existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.pi-server.yml down --remove-orphans

# Remove existing images to force rebuild
echo "🗑️ Removing existing images..."
docker rmi crec-presence-backend-api 2>/dev/null || true

# Build and start with logs
echo "🚀 Building and starting containers..."
docker compose -f docker-compose.pi-server.yml up --build -d

# Show container status
echo "📊 Container status:"
docker ps --filter "name=crec"

# Show logs for the API container
echo "📝 API Container logs:"
docker logs crec-backend-api --tail 20

echo "✅ Build complete!"
