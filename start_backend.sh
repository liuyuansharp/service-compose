#!/bin/bash

set -euo pipefail

source venv/bin/activate

python3 -m backend.app --config /home/liuyuan/workspace/work/fsys/service/examples/services_config.json --host 0.0.0.0 --port 8080 
