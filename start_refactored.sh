#!/bin/bash

# Start Scriptum API Server (Refactored Version)
# Clean, modular architecture with service-oriented design

echo "=========================================="
echo "🚀 Starting Scriptum v2.1 (Refactored)"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Stop any running instances
echo "🛑 Stopping existing servers..."
pkill -f sync_api.py 2>/dev/null
pkill -f app_refactored.py 2>/dev/null
sleep 1

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create .env with your API keys:"
    echo "   TMDB_API_KEY=your_key"
    echo "   OPENSUBTITLES_API_KEY=your_key"
    echo "   GEMINI_API_KEY=your_key"
    echo ""
fi

# Start refactored server
echo "🎬 Launching refactored server..."
arch -arm64 venv/bin/python app_refactored.py > /tmp/scriptum_refactored.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Check if server is running
if curl -s http://localhost:5001/health > /dev/null; then
    echo ""
    echo "✅ Server started successfully!"
    echo ""
    echo "📊 Architecture: Service-Oriented (Modular)"
    echo "🌐 URL: http://localhost:5001"
    echo "📄 Logs: /tmp/scriptum_refactored.log"
    echo "🆔 PID: $SERVER_PID"
    echo ""
    echo "Available endpoints:"
    echo "  GET  /health"
    echo "  POST /analyze-video"
    echo "  POST /recognize-movie"
    echo "  POST /remux-mkv-to-mp4"
    echo "  POST /convert-to-mp4"
    echo "  POST /extract-mkv-subtitles"
    echo ""
    echo "To view logs: tail -f /tmp/scriptum_refactored.log"
    echo "To stop: pkill -f app_refactored.py"
else
    echo ""
    echo "❌ Failed to start server!"
    echo "Check logs: cat /tmp/scriptum_refactored.log"
    exit 1
fi
