#!/bin/bash

# Quick test of the service manager with dummy services
# This script sets up and tests the manager with example services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Service Manager Test Example"
echo "================================"
echo ""
echo "This example uses dummy services to test the manager."
echo "Real services would replace ./examples/dummy_service.sh with actual startup scripts."
echo ""

# Make dummy service executable
chmod +x examples/dummy_service.sh

echo "Step 1: View configuration"
echo "  Config file: examples/services_config.json"
echo ""
cat examples/services_config.json | head -20
echo "  ..."
echo ""

echo "Step 2: Start services with test config"
echo "  Command: python3 manage_services.py start --config examples/services_config.json"
echo "  This will:"
echo "    - Start platform (runs for 60s)"
echo "    - Wait 2s"
echo "    - Start service_A (runs for 45s)"
echo "    - Start service_B (runs for 50s)"
echo "    - Monitor and auto-restart if they exit"
echo "    - Press Ctrl+C to stop all services"
echo ""
echo "Step 3: In another terminal, check status"
echo "  Command: python3 manage_services.py status"
echo ""
echo "Step 4: View logs"
echo "  Location: logs/"
echo "  Files: platform.log, service_A.log, service_B.log, manager.log"
echo "  Example: tail -f logs/platform.log"
echo ""
echo "Step 5: Check PID files"
echo "  Files: platform.pid, service_A.pid, service_B.pid"
echo "  Example: cat platform.pid"
echo ""
echo "Step 6: Try killing a service"
echo "  Command: kill \$(cat service_A.pid)"
echo "  Result: manager should auto-restart it with exponential backoff delay"
echo ""

read -p "Ready to start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 manage_services.py start --config examples/services_config.json --daemon
else
    echo "Cancelled."
fi
