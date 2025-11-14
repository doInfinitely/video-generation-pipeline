#!/bin/bash
# Quick setup script for testing play-by-play generation

echo "=========================================="
echo "Video Generation Pipeline - Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "✅ .env file already exists"
else
    echo "📝 Creating .env file from example..."
    cat > .env << 'EOF'
# LLM Provider Configuration (REQUIRED)
OPENAI_API_KEY=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Minimax API Configuration (OPTIONAL - for later)
MINIMAX_API_KEY=

# Video Settings
DEFAULT_FPS=24
CHUNK_DURATION_MS=6000
VIDEO_DURATION_SECONDS=6

# Storage Configuration
VIDEO_STORAGE_PATH=./storage/videos
TEMP_STORAGE_PATH=./storage/temp

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
EOF
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo ""
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo ""
echo "📚 Installing dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

echo ""
echo "📁 Creating storage directories..."
mkdir -p storage/videos storage/temp
echo "✅ Storage directories ready"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your API key:"
echo "   OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Test play-by-play generation:"
echo "   python test_play_by_play.py"
echo ""
echo "See TESTING_GUIDE.md for more details!"
echo ""

