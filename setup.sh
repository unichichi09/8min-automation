#!/bin/bash

# Setup Script for 3-Minute Video Automation Tool
# Usage: ./setup.sh

echo "=========================================="
echo "   3-Minute Video Automation Setup"
echo "=========================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 could not be found. Please install Python 3."
    exit 1
fi
echo "✅ Python 3 found."

# 2. Install Python Dependencies
echo ""
echo "--- Installing Python Dependencies ---"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully."
    else
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# 3. Check ImageMagick (Required for MoviePy Text)
echo ""
echo "--- Checking ImageMagick ---"
if ! command -v magick &> /dev/null && ! command -v convert &> /dev/null; then
    echo "⚠️ ImageMagick not found."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "Attempting to install via Homebrew..."
            brew install imagemagick
        else
            echo "❌ Homebrew not found. Please install ImageMagick manually: https://imagemagick.org/"
        fi
    else
        echo "❌ Please install ImageMagick manually: https://imagemagick.org/"
    fi
else
    echo "✅ ImageMagick found."
fi

# 4. Check VOICEVOX (Required for Audio)
echo ""
echo "--- Checking VOICEVOX ---"
echo "Checking if VOICEVOX is running on localhost:50021..."
response=$(curl --write-out %{http_code} --silent --output /dev/null http://localhost:50021/version)

if [ "$response" -eq 200 ]; then
    echo "✅ VOICEVOX is running."
else
    echo "⚠️ VOICEVOX is NOT running or not reachable."
    echo "Please download and start VOICEVOX before running the tool."
    echo "Download: https://voicevox.hiroshiba.jp/"
fi

# 5. Check Policy for ImageMagick (Common Issue)
# Sometimes policy.xml disables text. No easy way to check without running, 
# but we can warn user to checking their policy.xml if text fails.

echo ""
echo "=========================================="
echo "   Setup Complete!"
echo "   Run the tool with: python3 project/scripts/main.py new <ProjectName>"
echo "=========================================="
