from server.core import HttpServer


def run_server():
    # Let's restrict requests to GET, POST.
    # Find out what the structure of a request is like and start parsing line by line.
    # Depending on the request, return a proper response; let's do a "200 OK" or a "400 Bad Request" for now.
    server = HttpServer()
    while True:
        client_connection, client_address = server.run_server()
        print(f"Client Conn: {client_connection}, Client Address: {client_address}")

        request = client_connection.recv(1024).decode('utf-8')


if __name__ == "__main__":
    run_server()
