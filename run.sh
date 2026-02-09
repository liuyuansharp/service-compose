#!/bin/bash

source venv/bin/activate

nohup sh ./test_example.sh &

nohup python3 dashboard_api.py --host 0.0.0.0 --port 8080 &
