#!/usr/bin/env python3

"""
Demo: Show log rotation in action

This script writes to a log file until it reaches the rotation size,
then shows how the rotated files are named.
"""

import logging
import logging.handlers
import time
from pathlib import Path

DEMO_LOG_DIR = Path(__file__).resolve().parent / 'logs'
DEMO_LOG_FILE = DEMO_LOG_DIR / 'demo_rotation.log'

# Setup logger with small rotation size for demo (1MB instead of 10MB)
logger = logging.getLogger('demo')
logger.setLevel(logging.DEBUG)

DEMO_LOG_DIR.mkdir(exist_ok=True)

handler = logging.handlers.RotatingFileHandler(
    DEMO_LOG_FILE,
    maxBytes=1*1024*1024,  # 1MB for demo
    backupCount=5
)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

print(f"Demo: Writing to {DEMO_LOG_FILE} (max 1MB per file, 5 backups)")
print("Press Ctrl+C to stop")
print("")

try:
    i = 0
    while True:
        # Write a large line to trigger rotation
        msg = f"Demo message {i}: " + "X" * 500
        logger.info(msg)
        
        # Show file sizes
        if i % 1000 == 0:
            print(f"\nWritten {i} messages:")
            for f in sorted(DEMO_LOG_DIR.glob('demo_rotation.log*')):
                size_kb = f.stat().st_size / 1024
                print(f"  {f.name}: {size_kb:.1f} KB")
        
        i += 1
        time.sleep(0.01)  # 10ms between writes
except KeyboardInterrupt:
    print("\n\nStopped. Final file listing:")
    print(f"Directory: {DEMO_LOG_DIR}")
    for f in sorted(DEMO_LOG_DIR.glob('demo_rotation.log*')):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.1f} KB")
