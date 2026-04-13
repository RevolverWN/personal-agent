#!/bin/bash
set -e

echo "=== Personal Agent Setup ==="
echo ""

# 检查 Python 3.11+
echo "Checking Python 3.11+..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $PYTHON_VERSION is installed, but Python 3.11+ is required."
    exit 1
fi
echo "Python $PYTHON_VERSION found."

# 检查 Node.js 20+
echo "Checking Node.js 20+..."
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 20 or higher."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "Error: Node.js version $NODE_VERSION is installed, but Node.js 20+ is required."
    exit 1
fi
echo "Node.js $(node -v) found."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 安装后端
echo ""
echo "=== Setting up Backend ==="
cd "$PROJECT_ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 安装前端
echo ""
echo "=== Setting up Frontend ==="
cd "$PROJECT_ROOT/frontend"
npm install
npm run build

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the application:"
echo "  ./scripts/start.sh"
echo ""
echo "Or run manually:"
echo "  Backend: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
