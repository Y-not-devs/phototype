import subprocess
import sys
import os
import time
import threading
from router.common.utils.logging_service import LoggerService  # <-- put your class in logger_service.py

# Initialize global logger
logger_service = LoggerService("controller")
logger = logger_service.get_logger()

services = [
    {
        "name": "frontend",
        "cmd": [sys.executable, "-m", "flask", "--app", "app.py", "run", "--port=5000"],
        "cwd": "frontend-service",
        "enabled": True,
    },
    {
        "name": "router",
        "cmd": [sys.executable, "app/main.py"],
        "cwd": "router/router-service",
        "enabled": False,
    },
    {
        "name": "preprocessor",
        "cmd": [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host=0.0.0.0", "--port=8001", "--reload"
        ],
        "cwd": "router/preprocessor-service/app",
        "enabled": True,
    },
    {
        "name": "ocr-en",
        "cmd": [sys.executable, "app/main.py"],
        "cwd": "router/ocr-en-service",
        "enabled": False,
    },
]

processes = []

def stream_output(pipe, name):
    svc_logger = LoggerService(name).get_logger()
    for line in iter(pipe.readline, b""):
        svc_logger.info(line.decode().rstrip())
    pipe.close()

try:
    for svc in services:
        if not svc["enabled"]:
            logger.info("Skipping %s (disabled)", svc["name"])
            continue

        logger.info("Starting %s...", svc["name"])
        p = subprocess.Popen(
            svc["cmd"],
            cwd=svc["cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
        processes.append((svc["name"], p))

        threading.Thread(
            target=stream_output, args=(p.stdout, svc["name"]), daemon=True
        ).start()

    logger.info("All enabled services started. Press Ctrl+C to stop.")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    logger.info("Stopping services...")
    for name, p in processes:
        p.terminate()
    logger.info("All services stopped.")
