#!/bin/bash

set -euo pipefail

source venv/bin/activate

python3 -m backend.app --config examples/config.json --host 0.0.0.0 --port 8080 
