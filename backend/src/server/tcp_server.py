import os
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket


class TCPServer:
    def __init__(self):
        # AF_INET is the Internet address family for IPv4.
        # SOCK_STREAM is the socket type for TCP, the protocol that will be used to transport messages in the network.
        self.server_socket = socket(family=AF_INET, type=SOCK_STREAM)

        # SOL_SOCKET -> there are socket-level options, IP-level options, TCP-level options, SOL_SOCKET makes option affect the socket object itself as a whole.
        # REUSEADDR -> socket-level option which allows the server to reuse (i.e., accept connections) the same ip and port, while it's in close-wait or time-wait state.
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("BACKEND_PORT", "8080"))

    def run_server(self) -> tuple[socket, tuple[str, int]]:
        # associate the socket with the server address
        self.server_socket.bind((self.host, self.port))

        # puts the socket into server mode, listening for up to "n" connections
        self.server_socket.listen(1)

        print(f"Server started on {self.host}:{self.port}")
        while True:
            # waits for an incoming connection
            # conn is a new socket object usable to send and receive data on the connection,
            # address is the address bound to the socket on the other end of the connection.
            client_connection, client_address = self.server_socket.accept()
            print(f"Client {client_address} connected")

            response = self.handle_request(client_connection)
            print(response)

    @staticmethod
    def handle_request(client_connection: socket) -> str:
        client_connection.recv(1024).decode("utf-8")

        response = "Hello World!"
        client_connection.send(response.encode("utf-8")) # encode as bytes
        client_connection.close()

        return response

    def __enter__(self):
        self.run_server()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Stopping server on {self.host}:{self.port}")
        self.server_socket.close()
