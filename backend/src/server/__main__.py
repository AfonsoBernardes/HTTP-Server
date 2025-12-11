from server.core import HttpServer


def run_server():
    # Let's restrict requests to GET, POST.
    # Find out what the structure of a request is like and start parsing line by line.
    # Depending on the request, return a proper response; let's do a "200 OK" or a "400 Bad Request" for now.
    server = HttpServer()
    server.run_server()


if __name__ == "__main__":
    run_server()
