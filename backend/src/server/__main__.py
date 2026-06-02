import logging
import time

from api import users
from server.http_server import HTTPServer


def run_server():
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="{asctime} {levelname} {name}:{lineno} -- {message}",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    server = HTTPServer()

    server.include_router(prefix="/users", router=users.router)
    server.run_server()


if __name__ == "__main__":
    run_server()
