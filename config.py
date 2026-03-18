
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "tasks.db"),
)

HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 5000))
