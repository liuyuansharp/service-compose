#!/bin/bash

# Example dummy services for testing
# These scripts just run in a loop and can be killed cleanly

SERVICE_NAME="${1:-service}"
SLEEP_DURATION="${2:-30}"

echo "[$SERVICE_NAME] Starting (sleep $SLEEP_DURATION seconds then exit)"

trap "echo '[$SERVICE_NAME] Caught SIGTERM, cleaning up...'; exit 0" SIGTERM SIGINT

# Simulate work
for i in $(seq 1 $SLEEP_DURATION); do
    echo "[$SERVICE_NAME] tick $i"
    sleep 1
done

echo "[$SERVICE_NAME] Exiting normally"
exit 0
