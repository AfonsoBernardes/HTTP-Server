import os
from socket import AF_INET, SOCK_STREAM, socket


class HttpServer:
    def __init__(self):
        # AF_INET is the Internet address family for IPv4.
        # SOCK_STREAM is the socket type for TCP, the protocol that will be used to transport messages in the network.
        self.socket = socket(family=AF_INET, type=SOCK_STREAM)
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("BACKEND_PORT", "8080"))

    def run_server(self) -> tuple[socket, int]:
        # associate the socket with the server address
        self.socket.bind((self.host, self.port))

        # puts the socket into server mode, listening for up to "n" connections
        self.socket.listen(1)

        # waits for an incoming connection
        # conn is a new socket object usable to send and receive data on the connection,
        # address is the address bound to the socket on the other end of the connection.
        client_connection, client_address = self.socket.accept()

        return client_connection, client_address

    def __enter__(self):
        self.run_server()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Stopping server on {self.host}:{self.port}")
        self.socket.close()
