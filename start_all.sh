#!/bin/bash

set -euo pipefail

source venv/bin/activate

nohup python3 manage_services.py start --config examples/services_config.json --daemon &
nohup python3 -m backend.app --config examples/services_config.json --host 0.0.0.0 --port 8080 &
