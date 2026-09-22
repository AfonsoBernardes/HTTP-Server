<div align="center">
  <h1>HTTP Server from Scratch</h1>
</div>

Software engineers increasingly rely on tools to move faster, yet speed comes at a cost. As a backend engineer building production-grade applications with FastAPI, which abstracts away the HTTP request/response lifecycle, I built an HTTP/1.1 server from scratch to look under the hood. AI usage was deliberately kept to a minimum to avoid cognitive debt, which would be against the project's spirit. Here's what this project does:

<ul>
	<li>Parse raw bytes from a TCP socket into a structured request with method, path, headers and a correctly-delimited body.</li>
	<li>Resolve a request's method and path to the correct handler via a router.</li>
	<li>Serialise a handler's result into a well-formed HTTP response, with the correct headers, status code, and body.</li>
	<li>Support protocol-level behaviour such chunked transfer encoding and persistent (keep-alive) connections.</li>
</ul>

> See [THEORY.md](./THEORY.md) for the fundamentals of HTTP/TCP. This README focuses on what I built, how I built it and explains the decisions along the way.


<details open>
	<summary>
		<h2>Features</h2>
	</summary>
</details>


<details open>
	<summary>
		<h2>How I Built It</h2>
	</summary>

This section and its subsections walk us through the code line by line. Here I present what was built and the decisions/trade-offs I made along the way.


### TCP Server

The first building block of this project is a minimal, reusable, protocol-agnostic TCP server which protocol-specific servers, like HTTP, can extend. `TCPServer` is an `ABC` (abstract base class) which implements the transport layer, i.e, it takes care of opening a socket, binding it to an address, listening for connections, and accepting clients. Any subclass only has to implement what to do with a connection once it's open. This keeps the socket setup and configuration in one place and out of the HTTP-specific code.

```python
class TCPServer(ABC):
    def __init__(self):
        self.server_socket = socket(family=AF_INET, type=SOCK_STREAM)
		self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("BACKEND_PORT", "8000"))
```

First, we setup a TCP socket (`type=SOCK_STREAM`) using IPv4 Internet addressing (`family=AF_INET`). The socket is also configured (`setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)`) so that it can be rebound to the same `port` and IP address (`host`) even if this combination was previously left in a `TIME_WAIT` status, i.e., the interval between closing and opening a new TCP session; without configuration, restarting the server often fails with an "Address already in use" error. The server's `host` and `port` are read from environment variables (`HOST`, `BACKEND_PORT`), defaulting to `0.0.0.0:8000`, so the server can be configured per environment without code changes.

When the TCP server is running, it binds the socket to a specific address and port on the machine and listens to incoming connections. Currently, `listen(0)` defines that the system will refuse new connections while the server is busy handling an existing one.
 
```python
def run_server(self) -> tuple[socket, tuple[str, int]]:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(0)

        try:
            while True:
                client_connection, client_address = self.server_socket.accept()
                self.handle_request(client_connection)
                client_connection.close()
        finally:
            self.server_socket.close()
```

`accept()` blocks while it waits for a connection, and when a client connects, it returns a **new** socket object (`client_connection`) usable to send and receive data on the connection, and the address bound to the socket (`client_address`) on the other end of the connection. `handle_request` (an abstract method implemented by the subclass) reads from and writes to that connection; once it returns, the connection is closed and the server loops back to wait for the next client.

The accept loop closes each *client* connection after it's handled, but the *listening* socket (`self.server_socket`) is a separate, longer-lived resource. Since `run_server()` runs forever, the server socket needs to be wrapped in a `try/finally` block, which guarantees `close()` runs every time the loop exits, no matter what.

The server is simple and has obvious limitations; but these are conscious decisions which allowed me to focus on HTTP and still uncovering how it connects to the transport layer.

  * Single connection: the loop is single-threaded and accept()` blocks new client connections until the current one is fully handled and closed. This keeps the code simple without sacrificing robustness in the transport layer.

  * No backlog: since I'm focusing on a single connection at a time, the system does not accept any backlog either; if the "single connection" constraint is relaxed, backlog expansion or an async model would be worth considering.


### HTTP Server

As we've seen before, `TCPServer` implements everything related to the transport layer, on top of which the protocol is built. `HTTPServer`, which inherits from `TCPServer`, implements protocol-related features like parsing a request, routing it, and building a response. This parent-child relationship keeps concerns separated, allowing for other classes to build on top of the transport layer without affecting the rest of the code.

Before we get into how the server handles a request, we need to look at how it register and resolves routes. Below, we can see the server contemplates two distinct ways of registering routers; `prefixed_routers` uses a prefix string as a key to a `HTTPRouter` object, 

```python
class HTTPServer(TCPServer):
    def __init__(self):
        super().__init__()
        self.prefixed_routers: Dict[str, HTTPRouter] = {}
        self.free_routers: List[HTTPRouter] = []

    def include_router(self, router: HTTPRouter, prefix: Optional[str] = None) -> None:
        if router in self.free_routers or router in self.prefixed_routers.values():
            raise DuplicateRouter()

        if prefix:
            if prefix in self.prefixed_routers:
                raise DuplicateRouterPrefix(prefix=prefix)
            self.prefixed_routers[prefix] = router
        else:
            self.free_routers.append(router)
```
```python
	def resolve_route(self, url: str, method: HTTPRequestMethod) -> Optional[Callable]:
        for prefix in self.prefixed_routers.keys():
            if url.startswith(prefix):
                router = self.prefixed_routers[prefix]
                sub_path = url[len(prefix) :]

                return router.resolve(sub_path, method)

        for free_router in self.free_routers:
            if free_router.routes.get(url):
                return free_router.resolve(url, method)

        return None
```

### Router

### Request

### Response
	
</details>

---

## Getting Started

Some commands here for easy start.

---

## Project Structure

---

## Future Work

---

## What I Deliberately Skipped
<ul>
	<li>HTTP/2 and HTTP/3 are separate protocols with different sets of rules. HTTP/1.1 is readable as plain-text, which makes the fundamentals visible.</li>
	<li>HTTPS is just HTTP sent over a TLS-encrypted connection, which does not concern this project's scope since it happens before the request is handled.</li>
	<li>Transfer-Encoding: compress, deflate, gzip is rarely used; moreover, it adds complexity without HTTP insight.</li>
	<li>A real database, since database management is out of scope for this project.</li>
</ul>

---

## Resources
