import logging

from server.http_server import HTTPServer


def run_server():
    logging.basicConfig(level=logging.INFO, style="{", format="{asctime} {levelname} {name}:{lineno} -- {message}")

    # Let's restrict requests to GET, POST.
    # Find out what the structure of a request is like and start parsing line by line.
    # Depending on the request, return a proper response; let's do a "200 OK" or a "400 Bad Request" for now.
    server = HTTPServer()
    server.run_server()


if __name__ == "__main__":
    run_server()
