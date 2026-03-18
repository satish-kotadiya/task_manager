

from http.server import HTTPServer

from app.database import init_db
from app.handlers import TaskHandler


def run_server(host: str, port: int) -> None:
    init_db()
    server = HTTPServer((host, port), TaskHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
