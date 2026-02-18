#!/bin/bash

# SC902 Installer - Made by SSI902 😎
echo "🚀 Installing SC902 - Advanced BTC Brain Wallet Scanner"
echo "Made by SSI902 - The Finest Investor 😎"
echo "========================================"

# Create directory
mkdir -p ~/.sc902

# Copy all files
cp config.py ~/.sc902/
cp wordlist.py ~/.sc902/
cp sc902.py ~/.sc902/
cp sc902 ~/.sc902/

# Set permissions
cd ~/.sc902
chmod +x sc902 sc902.py

# Install dependencies
echo "📦 Installing dependencies..."
pkg update -y
pkg install python clang -y
pip install mnemonic ecdsa base58 requests bech32 pyarmor

# Create log file
touch sweep.log

# Start scanner
echo "🚀 Starting SC902..."
./sc902 start

echo ""
echo "✅✅✅ INSTALLATION COMPLETE! ✅✅✅"
echo "========================================"
echo "Made by SSI902 - The Finest Investor 😎"
echo "========================================"
echo "Commands:"
echo "  cd ~/.sc902"
echo "  ./sc902 dashboard  - Show menu"
echo "  ./sc902 start      - Start scanner"
echo "  ./sc902 stop       - Stop scanner"
echo "  ./sc902 log --live - Watch live finds"
echo "========================================"
