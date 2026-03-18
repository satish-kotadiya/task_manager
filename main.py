"""
Entry point — starts the Task Manager API server.

Usage:
    python main.py
"""

from app.server import run_server
from config import HOST, PORT

if __name__ == "__main__":
    print(f"Task Manager API running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.\n")
    run_server(HOST, PORT)
