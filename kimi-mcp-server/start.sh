#!/bin/bash
# Kimi MCP Server Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
if [ ! -f ".venv/installed" ] || [ "requirements.txt" -nt ".venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .venv/installed
fi

# Run the MCP server
echo "Starting Kimi MCP Server..."
echo "Mode: ${MCP_TRANSPORT:-stdio}"

if [ "${MCP_TRANSPORT}" == "http" ]; then
    python3 src/core_tools.py --transport http --port ${MCP_PORT:-8080}
else
    python3 src/core_tools.py
fi
