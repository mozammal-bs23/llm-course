#!/bin/bash
# Startup script for AI Tutoring Assistant Web Frontend

echo "🤖 Starting AI Tutoring Assistant Web Server..."
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: GOOGLE_API_KEY not set!"
    echo "   Set it with: export GOOGLE_API_KEY='your-key-here'"
    echo "   Or create a .env file with: GOOGLE_API_KEY=your-key-here"
    echo ""
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""
python api.py

