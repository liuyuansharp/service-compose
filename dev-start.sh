#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

print_info() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Parse arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false

if [ "$1" = "backend" ]; then
    BACKEND_ONLY=true
elif [ "$1" = "frontend" ]; then
    FRONTEND_ONLY=true
elif [ "$1" = "help" ] || [ "$1" = "-h" ]; then
    echo "Service Manager Dashboard - Development Starter"
    echo ""
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  (no args)    - Start both backend and frontend"
    echo "  backend      - Start only backend server"
    echo "  frontend     - Start only frontend dev server"
    echo "  help|-h      - Show this help message"
    echo "  stop         - Stop all running services"
    echo ""
    exit 0
elif [ "$1" = "stop" ]; then
    print_header "Stopping Services"
    pkill -f "uvicorn main:app" || true
    pkill -f "vite" || true
    print_info "All services stopped"
    exit 0
fi

# Check prerequisites
print_header "Checking Prerequisites"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi
python_version=$(python3 --version | cut -d' ' -f2)
print_info "Python $python_version"

# Check Node
if [ "$FRONTEND_ONLY" = false ]; then
    print_info "Backend mode - Node not required"
else
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    node_version=$(node --version)
    print_info "Node.js $node_version"
fi

# Setup backend
if [ "$FRONTEND_ONLY" = false ]; then
    print_header "Setting Up Backend"
    
    # Install dependencies
    if ! python3 -m pip install -q -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null; then
        print_warning "Failed to install some dependencies, trying with --user flag"
        python3 -m pip install --user -q -r "$SCRIPT_DIR/requirements.txt" || {
            print_error "Failed to install dependencies"
            exit 1
        }
    fi
    print_info "Dependencies installed"
    
    # Check logs directory
    mkdir -p "$SCRIPT_DIR/logs"
    print_info "Logs directory ready"
fi

# Setup frontend
if [ "$BACKEND_ONLY" = false ]; then
    print_header "Setting Up Frontend"
    
    cd "$SCRIPT_DIR/frontend"
    
    # Install npm dependencies
    if [ ! -d "node_modules" ]; then
        print_info "Installing npm dependencies (this may take a moment)..."
        npm install --legacy-peer-deps --silent
    else
        print_info "npm dependencies already installed"
    fi
fi

# Start services
print_header "Starting Services"

if [ "$FRONTEND_ONLY" = false ]; then
    print_info "Starting backend server..."
    cd "$SCRIPT_DIR"
    python3 -m backend.app --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    sleep 2
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_info "Backend running on http://localhost:8080 (PID: $BACKEND_PID)"
        print_info "API docs: http://localhost:8080/api/docs"
    else
        print_error "Failed to start backend"
        exit 1
    fi
fi

if [ "$BACKEND_ONLY" = false ]; then
    print_info "Starting frontend server..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
    sleep 3
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_info "Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"
        
        # Try to open in browser
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:5173" 2>/dev/null || true
        elif command -v open &> /dev/null; then
            open "http://localhost:5173" 2>/dev/null || true
        fi
    else
        print_error "Failed to start frontend"
        exit 1
    fi
fi

echo ""
print_header "Dashboard Ready!"
echo ""

if [ "$FRONTEND_ONLY" = false ]; then
    echo -e "  ${GREEN}Backend:${NC}  http://localhost:8080"
    echo -e "  ${GREEN}API Docs:${NC} http://localhost:8080/api/docs"
fi

if [ "$BACKEND_ONLY" = false ]; then
    echo -e "  ${GREEN}Frontend:${NC} http://localhost:5173"
fi

echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    print_header "Shutting Down"
    
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true
        print_info "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_info "Frontend stopped"
    fi
    
    exit 0
}

# Trap Ctrl+C
trap cleanup EXIT INT TERM

# Keep running
while true; do
    sleep 1
done
