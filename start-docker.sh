#!/bin/bash
echo "Starting JobApply AI with Docker Compose (Production)..."
echo ""
docker-compose -f docker-compose.prod.yml up --build
