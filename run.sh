#!/bin/bash

source venv/bin/activate

nohup python3 manage_services.py start --config examples/services_config_example.json --daemon &
nohup python3 -m backend.app --host 0.0.0.0 --port 8080 &
