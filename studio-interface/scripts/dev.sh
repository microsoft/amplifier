#!/bin/bash

# Port management script for Studio development
# Usage: ./scripts/dev.sh [port]

PORT=${1:-3000}

echo "🧹 Cleaning up ports 3000-3003..."
lsof -ti:3000,3001,3002,3003 2>/dev/null | xargs kill -9 2>/dev/null || true

sleep 1

echo "🚀 Starting Studio on port $PORT..."
PORT=$PORT npm run dev
