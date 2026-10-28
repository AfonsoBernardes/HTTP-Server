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


## Features

## How I Built It

This section and its subsections walk us through the code line by line. Here I present what was built and the decisions/trade-offs I made along the way.

<details>
	<summary>
		<h3>TCP Server</h2>
	</summary>

The first building block of this project is a minimal, reusable, protocol-agnostic TCP server which protocol-specific servers, like HTTP, can extend. `TCPServer` is an `ABC` (abstract base class) which implements the transport layer, i.e., it takes care of opening a socket, binding it to an address, listening for connections, and accepting clients. Any subclass only has to implement what to do with a connection once it's open. This keeps the socket setup and configuration in one place and out of the HTTP-specific code.

```python
class TCPServer(ABC):
  def __init__(self):
    self.server_socket = socket(family=AF_INET, type=SOCK_STREAM)
    self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    self.host = os.getenv("HOST", "0.0.0.0")
    self.port = int(os.getenv("BACKEND_PORT", "8000"))
```

First, we set up a TCP socket (`type=SOCK_STREAM`) using IPv4 Internet addressing (`family=AF_INET`). The socket is also configured (`setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)`) so that it can be rebound to the same `port` and IP address (`host`) even if this combination was previously left in a `TIME_WAIT` status, i.e., the interval a closed connection lingers so that late packets aren't mistaken for a new connection; without this configuration step, restarting the server often fails with an "Address already in use" error. The server's `host` and `port` are read from environment variables (`HOST`, `BACKEND_PORT`), defaulting to `0.0.0.0:8000`, so the server can be configured per environment without code changes.

When the TCP server is running, it binds the socket to a specific address and port on the machine and listens for incoming connections. Currently, `listen(0)` makes the pending-connection queue minimal, so additional clients wait or fail to connect while the server is busy handling an existing one.
 
```python
def run_server(self) -> None:
  self.server_socket.bind((self.host, self.port))
  self.server_socket.listen(0)
  
  try:
    while True:
      client_connection, client_address = self.server_socket.accept()
  
      try:
        self.handle_request(client_connection)
      finally:
        client_connection.close()
  finally:
    self.server_socket.close()
```

`accept()` blocks the server while it waits for a connection, and when a client connects, it returns a **new** socket object (`client_connection`) usable to send and receive data on the connection, and the address bound to the socket (`client_address`) on the other end of the connection. `handle_request` (an abstract method implemented by the subclass) reads from and writes to that connection; once it returns or raise an exception, the connection is closed and the server loops back to wait for the next client.

The accept loop closes each *client* connection after it's handled, but the *listening* socket (`self.server_socket`) is a separate, longer-lived resource. Since `run_server()` runs forever, the server socket needs to be wrapped in a `try/finally` block, which guarantees `close()` runs every time the loop exits, no matter what.

The server is simple and has obvious limitations, but these are conscious decisions which allowed me to focus on HTTP and still uncover how it connects to the transport layer.

  * Single connection: the loop is single-threaded, so the server can't call accept() again until the current connection is fully handled and closed, meaning other clients have to wait. This keeps the code simple without sacrificing robustness in the transport layer.

  * No backlog: since I'm focusing on a single connection at a time, the system's pending-connection queue is kept minimal; if the "single connection" constraint is relaxed, backlog expansion or an async model would be worth considering.

With the TCP layer handling connections, we now need to turn raw bytes into a structured request, route the request to the right handler, and build the response to send back. We'll cover each component individually before bringing them together into the HTTP server itself.

</details>

<details>
	<summary>
		<h3>HTTP Request</h2>
	</summary>

An HTTP/1.1 request is a message with a fixed structure: a request line (`<METHOD>` `<TARGET>` `<PROTOCOL>`), a header section followed by an empty line, and an optional body. Parsing a request requires us to first parse the headers, and only then parse the request's body, since the headers provide necessary information about how to parse the body. These stages map to two main functions: `parse_headers` turns the raw header section into a structured request, and `parse_body` uses those headers to read the body.

Everything in a request comes from the client, so I try to keep the logic as strict as possible, rejecting malformed or malicious requests before they can reach the next stage. Let's see how a request moves through both stages, and the reasoning behind the decisions made along the way.

Before anything can be parsed, the raw bytes have to be read from the socket; that's the server's job. Since TCP delivers a stream of bytes with no message boundaries, a single `recv()` can return any set of bytes; however, under HTTP rules, a request's headers and body are separated by two "CRLF", so the `HTTPServer` will read raw bytes until it finds `\r\n\r\n`, meaning the header section is complete. To guard against a client never sending a blank line, which would make the server buffer forever, the server rejects the request with `HeaderSectionTooLarge` (`431 Request Header Fields Too Large`) once the header section grows larger than an imposed limit (16 KB) [RFC 9110 §5.4; RFC 6585 §5]. 

```python
raw_data = b""
while b"\r\n\r\n" not in raw_data:
  if len(raw_data) > limits.max_header_section_size:
    raise HeaderSectionTooLarge(header_size=len(raw_data), max_header_size=limits.max_header_section_size)
  
  chunk_data = client_connection.recv(1024)
  if not chunk_data:
    break
  raw_data += chunk_data
```

Once the loop ends, we can separate the header section from the rest of the raw bytes received, which already belong to the request's body or, in principle, to the next request entirely; these bytes are appended to a buffer for later processing. The header section is decoded and sent to a function (`parse_headers`) to parse the request line and the request's headers.

```python
def parse_headers(request_headers: str) -> Tuple[
  HTTPRequestMethod,
  str,
  HTTPProtocol,
  Dict[str, List[str]],
]:
  request_headers = request_headers.split("\r\n")
  
  raw_request_line = request_headers.pop(0)
  request_line = raw_request_line.split(" ", maxsplit=2)
  if len(request_line) != 3:
    raise InvalidRequestLine(raw_request_line)

  try:
    method = HTTPRequestMethod(request_line[0])
  except ValueError:
    raise InvalidHTTPMethod(request_line[0])
  
  url = request_line[1]
  
  try:
    protocol = HTTPProtocol(request_line[2])
  except ValueError:
    raise InvalidHTTPProtocol(request_line[2])
```

First of all, we separate every new line into a list `request_headers`, whose first element should be the request line, hence, we isolate the first element and separate it into exactly three parts: method, target and protocol. To stay strict, any other request line's shape will raise an `InvalidRequestLine` (`400 Bad Request`), since relaxed request-line parsing is a possible smuggling vector [RFC 9112 §3]. Furthermore, we also check the method and protocol against `enums`, raising exceptions with `400 Bad Request` status code, so that the request line is fully validated before parsing the headers.

Secondly, each header line is split at its first colon meaning that a header key cannot have a colon, but a value can (e.g. `Host: localhost:8000`). Header keys can only contain ASCII letters, digits and a few symbols; a space (even one before the colon), a control character, a non-ASCII letter or an empty key gets the request rejected [RFC 9110 §5.6.2; RFC 9112 §5.1]. Header values can't contain NUL, CR or LF because a bare line feed could make another parser see an extra header that this one never saw [RFC 9110 §5.5; RFC 9112 §2.2]. Some headers are defined as comma-separated lists (`Accept-Language`, `Transfer-Encoding`, etc.) meaning they may have more than one value separated by a comma; if that's the case, we split the header value by each comma, if not, the comma is just part of the value [RFC 9110 §5.3, §5.6.1].

```python
INVALID_HEADER_KEY_CHARS = re.compile(r"[^!#$%&'*+\-.^_`|~0-9A-Za-z]")
INVALID_HEADER_VALUE_CHAR = re.compile(r"[\x00\r\n]")

headers = {}
for header in request_headers:
  try:
    key, value = header.split(":", maxsplit=1)
    if not key:
      raise InvalidHTTPHeaders()
    
    invalid_key_char = INVALID_HEADER_KEY_CHARS.search(key)
    if invalid_key_char:
      raise InvalidHTTPHeaderKey(key=key, invalid_char=invalid_key_char.group())
    
    invalid_value_char = INVALID_HEADER_VALUE_CHAR.search(value)
    if invalid_value_char:
      raise InvalidHTTPHeaderValue(key=key, value=value, invalid_char=invalid_value_char.group())
    
    key = key.lower()
    if key in COMMA_SEPARATED_VALUE_HEADERS:
      value_list = [value.strip() for value in value.split(",")]
    else:
      value_list = [value.strip()]
    
    for value in value_list:
      if key not in headers:
        headers[key] = [value]
      else:
        if key in SINGLE_VALUE_HEADERS:
          raise DuplicateHTTPHeader(header_key=key)
        headers[key].append(value)
  except ValueError:
    raise InvalidHTTPHeaders()

return method, url, protocol, headers
```

Lastly, each key points at a list of individual values, either comma separated values from the same header line, or headers which appear more than once on different lines and are allowed to have multiple values. However, some headers must be unique (`Content-Length`, `Host`, etc.) making it so that a repeat raises `DuplicateHTTPHeader` (`400 Bad Request`) since different parsers may pick different values, and that disagreement is what smuggling attacks exploit [RFC 9110 §5.5].

Once the headers are parsed, they should tell us where the body ends. There are two ways to determine it: either with `Content-Length` header telling us the exact number of bytes, or by `Transfer-Encoding: chunked` sending the body in pieces, each announcing their own size, useful when the sender doesn't know the complete body size up front. Notice that a request carrying both headers is rejected with `AmbiguousBodyLength` (`400 Bad Request`), because two framing methods can disagree about where the body ends, opening a window for request smuggling [RFC 9112 §6.1, §6.3, §11.2]. Notice that `POST`, `PUT` and `PATCH` methods are expected to carry content; therefore, when neither header is present, we raise an `UnspecifiedBodyLength` (`411 Length Required`) instead of assuming the body is empty, i.e., the client has to state a length, even if it is zero [RFC 9110 §8.6].

```python
class HTTPRequest:
  def __init__(
    self, method: HTTPRequestMethod, url: str, protocol: HTTPProtocol, headers: Dict[str, List[str]]
  ) -> None:
    self.method = method
    self.url = url
    self.protocol = protocol
    self.headers = headers
    self.body: Optional[str] = None
  
  def parse_body(
    self, client_connection: socket, body_buffer: bytes, limits: ServerLimits = DEFAULT_LIMITS
  ) -> Optional[str]:
    transfer_encoding = self.headers.get("transfer-encoding", None)
    content_length = self.headers.get("content-length", None)
    
    if transfer_encoding is not None and content_length is not None:
      raise AmbiguousBodyLength()
    
    raw_body = b""
    if transfer_encoding is not None:
      ...
    elif content_length is not None:
      ...
    elif self.method in (HTTPRequestMethod.POST, HTTPRequestMethod.PUT, HTTPRequestMethod.PATCH):
      raise UnspecifiedBodyLength(method=self.method)
```

The `Content-Length` branch requires the value to contain ASCII digits only, which is stricter than Python's `int()`, since the latter also accepts `+5`, `1_0` or `-0`. The conversion is still wrapped in a try/except block, because Python refuses to convert strings of more than 4300 digits. Once converted to a valid integer, the declared length is compared with the server limit (10 MB by default), and a larger value raises `BodyTooLarge` (`413 Content Too Large`). If `Content-Length` declares a non-empty body, the parser reads until the `body_buffer` is big enough or breaking the loop if no data is received. In the case the buffer is smaller than the declared body size, an `InvalidBodyLength` (`400 Bad Request`) discards the request.

```python
VALID_CONTENT_LENGTH = re.compile(r"[0-9]+")

content_length = content_length[0]
if not VALID_CONTENT_LENGTH.fullmatch(content_length):
  raise InvalidContentLength(content_length=content_length)

try:
	content_length = int(content_length)
except ValueError:
	raise InvalidContentLength(content_length=content_length)

if content_length > limits.max_body_size:
	raise BodyTooLarge(content_length, limits.max_body_size)

if content_length > 0:
  while len(body_buffer) < content_length:
    chunk_data = client_connection.recv(1024)
    if not chunk_data:
      break
    body_buffer += chunk_data

  if len(body_buffer) < content_length:
    raise InvalidBodyLength(body_length=len(body_buffer), expected_length=content_length)
  else:
    raw_body = body_buffer[:content_length]
    body_buffer = body_buffer[content_length:]
```

The `Transfer-Encoding` path of the logic is slightly longer; instead of declaring the total length up front, the sender splits the body into chunks, transferred as a sequence of length-delimited buffers. Each chunk starts with a string of hexadecimal digits which indicate the size of the chunk-data in octets, followed by "CRLF" and then the chunk itself, followed by another "CRLF". The end of a body is marked by a zero-length chunk, followed by an optional trailer section and a final empty line [RFC 9112 §7.1]. Notice that, even though `Transfer-Encoding` header can have comma separated values, only `chunked` is accepted, and as a single value; if more than one value is declared, or a known one the server doesn't support, it raises `UnsupportedTransferEncoding` (`501 Not Implemented`), any other value raises `InvalidTransferEncoding` (`400 Bad Request`).

```python
if len(transfer_encoding) != 1:
  raise UnsupportedTransferEncoding(transfer_encoding=transfer_encoding)

transfer_encoding = transfer_encoding[0]
if transfer_encoding.lower() == "chunked":
  raw_body = parse_chunked_body(client_connection, body_buffer, limits)
elif transfer_encoding.lower() in ("compress", "deflate", "gzip"):
  raise UnsupportedTransferEncoding(transfer_encoding=transfer_encoding)
else:
  raise InvalidTransferEncoding(transfer_encoding=transfer_encoding)
```

Parsing a chunked body can be divided into several smaller functions so it reads better and it's more easily maintained and tested, avoiding that a single block of code takes on all the responsibility for a rather nuanced logic which inherently raises a lot of edge cases. Before getting into the details on parsing, let's break down the different helper functions: `receive_chunked_data`, `read_exact` and `read_line`.

`receive_chunked_data` is fairly straightforward, it makes a single `recv()` call receiving bytes through the open connection; if no data is received, it means the client closed the connection, and waiting for bytes that will never arrive would hang the single-threaded server [RFC 9112 §8], so it raises `IncompleteChunkedBody` (`400 Bad Request`).

```python
def receive_chunked_data(client_connection: socket) -> bytes:
  chunk_data = client_connection.recv(1024)
  if not chunk_data:
    raise IncompleteChunkedBody(client_connection)

  return chunk_data
```

Reading chunked data takes two kinds of reads: reading a line, like the chunk size or a trailer field, and reading an exact number of bytes, i.e., a chunk's data. `read_line` receives data until "CRLF" is present in the buffer or until the buffer grows past an imposed limit of 4 KB for each chunk line, in which case a `ChunkLineTooLarge` (`413 Content Too Large`) is raised, preventing the buffer from growing forever. Once `\r\n` is found in the body buffer, we separate that chunk line from the rest of the buffer and check for the line size once again. Notice that the first size check compares with `max_line_size + 1` while the second compares to `max_line_size`, why? In the first case, since we're still receiving data, we could go over the limit once a `\r` character without a matching `\n` is received, which shouldn't count for the line size; the second check is in place in case the chunk line arrives complete but too long. Once we know the next chunk's size, `read_exact` receives data until the buffer holds at least the declared number of bytes, reading that exact number as the chunk's body, while the rest remains in the buffer.

```python
def read_line(client_connection: socket, body_buffer: bytes, max_line_size: int) -> Tuple[bytes, bytes]:
  while b"\r\n" not in body_buffer:
    if len(body_buffer) > max_line_size + 1:
      raise ChunkLineTooLarge(chunk_line_size=len(body_buffer), max_chunk_line_size=max_line_size)

    chunk_data = receive_chunked_data(client_connection)
    body_buffer += chunk_data

  chunk_line, body_buffer = body_buffer.split(b"\r\n", maxsplit=1)
  if len(chunk_line) > max_line_size:
    raise ChunkLineTooLarge(chunk_line_size=len(chunk_line), max_chunk_line_size=max_line_size)

  return chunk_line, body_buffer

def read_exact(client_connection: socket, body_buffer: bytes, chunk_size: int) -> Tuple[bytes, bytes]:
  while len(body_buffer) < chunk_size:
    chunk_data = receive_chunked_data(client_connection)
    body_buffer += chunk_data

  body_chunk = body_buffer[:chunk_size]
  body_buffer = body_buffer[chunk_size:]

  return body_chunk, body_buffer
```

With these helpers, every loop iteration in `parse_chunked_body` reads exactly one chunk, starting with the chunk-size line: a size in hexadecimal, possibly followed by extensions after a semicolon. Extensions are ignored, but they still have to be read to find the end of the line, so the whole line is limited to 4 KB by default [RFC 9112 §7.1.1]. The size must be valid hexadecimal and no larger than the 5 MB chunk limit, otherwise `InvalidChunkSize` (`400 Bad Request`) or `ChunkTooLarge` (`413 Content Too Large`) is raised, respectively.

```python
VALID_CHUNK_SIZE = re.compile(rb"^[0-9A-Fa-f]+$")

def parse_chunked_body(client_connection: socket, body_buffer: bytes, limits: ServerLimits = DEFAULT_LIMITS) -> bytes:
  chunks: List[bytes] = []
  body_size: int = 0

  while True:
    chunk_size_line, body_buffer = read_line(client_connection, body_buffer, limits.max_chunk_line_size)

    chunk_size = chunk_size_line.split(b";", maxsplit=1)[0]
    if not chunk_size or not VALID_CHUNK_SIZE.fullmatch(chunk_size):
      raise InvalidChunkSize(chunk_size)

    chunk_size = int(chunk_size.decode("ascii"), 16)
    if chunk_size > limits.max_chunk_size:
      raise ChunkTooLarge(chunk_size, limits.max_chunk_size)
```

A `chunk_size` of zero is the last chunk, followed only by an optional the trailer section, which is read line by line and thrown away. However, if the trailer section is larger than 8 KB, the server raises a `TrailerSectionTooLarge` (`413 Content Too Large`) [RFC 9112 §7.1.2]. An empty line ends both the section and the body, so the break leaves the loop with the buffer positioned right after the request.

```python
    if chunk_size == 0:
      trailer_size = 0
      while True:
      trailer_line, body_buffer = read_line(client_connection, body_buffer, limits.max_chunk_line_size)
    
      if trailer_line == b"":
        break
    
      trailer_size += len(trailer_line)
      if trailer_size > limits.max_trailer_section_size:
        raise TrailerSectionTooLarge(trailer_size, limits.max_trailer_section_size)
      break
```

Any other size means data is present. Two more limits are checked before the data is read. so the chunk that would cross either limit is never read from the socket: the body can’t grow past 10 MB (`BodyTooLarge`, `413 Content Too Large`), and it can’t have more than 100,000 chunks, which would stress the server (`TooManyChunks`, `413 Content Too Large`).

Then, the server reads the exact bytes the chunk size declared, appends them to the `chunks` list and read the two bytes after them which must be the delimiter `\r\n`; if they aren't, the client lied about the chunk's size or sent more data than it declared, and the request is rejected with `InvalidChunkDelimiter` (`400 Bad Request`), because otherwise the parser would carry on from the wrong place. Every read returns the rest of the buffer, so after each step `body_buffer` starts exactly where the next read has to begin. The chunks are collected in a list, joined once at the end, because appending to a bytes object copies the whole body every time.

```python
    if body_size + chunk_size > limits.max_body_size:
      raise BodyTooLarge(body_size + chunk_size, limits.max_body_size)
    
    if len(chunks) >= limits.max_chunk_count:
      raise TooManyChunks(chunk_count=len(chunks) + 1, max_chunk_count=limits.max_chunk_count)
    
    body_chunk, body_buffer = read_exact(client_connection, body_buffer, chunk_size)
    chunks.append(body_chunk)
    body_size += chunk_size
    
    delimiter, body_buffer = read_exact(client_connection, body_buffer, 2)
    if delimiter != b"\r\n":
      raise InvalidChunkDelimiter(delimiter)

  raw_body = b"".join(chunks)
  return raw_body
```

HTTP/1.1 is a protocol which supports many features and many variants more, making their rigorous implementation and test a job for multiple, very skilled engineers. This parser focuses on the core fundamentals: safely reading, parsing and validating a request; when in doubt, the request is rejected. These limitations are conscious decisions, which include, but are not limited to, the bullet point below.

  * A `Content-Length` list or repeated `Content-Length` lines are rejected even when the values are identical [RFC 9112 §6.3], and so are empty list elements such as `chunked,` [RFC 9110 §5.6.1.2] and whitespace before the semicolon in a chunk-size line [RFC 9112 §7.1.1]. A `POST`, `PUT` or `PATCH` without `Content-Length` or `Transfer-Encoding` gets a `411 Length Required`, where the RFC would treat the body as empty [RFC 9112 §6.3].

  * HTTP/1.1 requires a `400 Bad Request` for a missing `Host` [RFC 9112 §3.2], but the server accepts it, while repeats are rejected.

  * Headers are split on commas even inside quotes, `Cookie` isn't split, and headers are parsed as decoded text, not as raw octets [RFC 9112 §2.2].

  * No timeouts and no keep-alive connections make a silent client blocks the server, moreover each connection carries one request, so leftover bytes after the body are discarded.

</details>

<details>
	<summary>
		<h3>HTTP Router</h2>
	</summary>

As we've seen in the previous section and in [THEORY.md](./THEORY.md), a HTTP request states what a client wants to do (`METHOD`) with/ to which resource (`PATH`). When a request is sent, once it is parsed, the server needs to figure out what it intends to do: can the intended action be performed on the stated resource, if so, how? Does the server even know the resource exists?

A router's main job is to map a `METHOD`/ `PATH` pair to a handler, i.e., a function which uses the request's information to produce a response. The `HTTPRequest` class is simply a collection of resources and the actions which can be performed on them. At its core, `routes` stores all this information using `path` as the first-level key, which points to a dictionary where a `HTTPRequestMethod` points to a handler. This way, the same path can point to several different method, but the `path` - `METHOD` combination is unique; if we try to include a duplicate combination, we get `DuplicateRoute` (`409 Conflict`).

```python
class HTTPRouter:

  def __init__(self):
    self.routes: Dict[str, Dict[HTTPRequestMethod, Callable]] = {}

  def include_route(self, path: str, method: HTTPRequestMethod, handler: Callable) -> None:
    self.routes.setdefault(path, {})

    if method in self.routes[path]:
      raise DuplicateRoute(path, method)

    self.routes[path][method] = handler
```

</details>

<details>
	<summary>
		<h3>HTTP Response</h2>
	</summary>
</details>

<details>
	<summary>
		<h3>HTTP Server</h2>
	</summary>

As we've seen before, `TCPServer` implements everything related to the transport layer, on top of which the protocol is built. `HTTPServer`, which inherits from `TCPServer`, implements protocol-related features like parsing a request, routing it, and building a response. This parent-child relationship keeps concerns separated, allowing for other classes to build on top of the transport layer without affecting the rest of the code.

Before we get into how the server handles a request, we need to look at how it register and resolves routes. Below, we can see the server contemplates two distinct ways of registering routers:

- `prefixed_routers` links a prefix string to a `HTTPRouter` object, grouping all routes for a given resource in a single router. Furthermore, the dictionary keyed by prefix is able to check for duplicates in O(1) time.
- `free_routers` are registered with no prefix, so `HTTPRouter` owns the full path of it's routes.

`sorted_prefixes` is a list (computed from `prefixed_routers`) which orders the prefixes from longest to shortest. The why of this structure's existence will become clear once we see how routes are resolved, for the time being, let's just note that routers are registered by the developer at startup and before the server accepts connections, so this list is computed once per registration rather than on every request, with minimum impact on performance.

```python
class HTTPServer(TCPServer):
    def __init__(self):
        super().__init__()
        self.prefixed_routers: Dict[str, HTTPRouter] = {}
		self._sorted_prefixes: List[str] = []
        self.free_routers: List[HTTPRouter] = []
```

The server has no knowledge of individual paths/ routes, it only knows about `HTTPRouter`, each owning a group of related routes. `include_router` records the router in the server as a way of letting the server access those routes which, once resolved after a request, will return a handler function as we'll see later.

Registration time is when the server learns about a router, so before anything else, it checks if the router was previously registered, with our without prefix. This avoids including a router twice by mistake which could lead to ambiguous resolution. If no prefix is present, we just add the router to the `free_routers` list. If a prefix is present, we must check if it is a duplicate before creating a new key-value entry in the `prefixed_routers` dictionary. Since a new prefixed router was added, we need to recompute the sorted prefixes list, hence the "once-per-registration" statement we made earlier.

```python
    def include_router(self, router: HTTPRouter, prefix: Optional[str] = None) -> None:
        if router in self.free_routers or router in self.prefixed_routers.values():
            raise DuplicateRouter()

        if prefix:
            if prefix in self.prefixed_routers:
                raise DuplicateRouterPrefix(prefix=prefix)
            self.prefixed_routers[prefix] = router

            self._sorted_prefixes = sorted(self.prefixed_routers.keys(), key=len, reverse=True)
        else:
            self.free_routers.append(router)
```

To undertstand the userior to Python 3.6, dictionaries were unordered structures, however, as of Python 3.7 dictionaries maintain the order of insertion of its key-value pairs.

```python
	def resolve_route(self, url: str, method: HTTPRequestMethod) -> Optional[Callable]:
        for prefix in self._sorted_prefixes:
            if url.startswith(prefix):
                router = self.prefixed_routers[prefix]
                sub_path = url[len(prefix) :]

                return router.resolve(sub_path, method)

        for free_router in self.free_routers:
            if free_router.routes.get(url):
                return free_router.resolve(url, method)

        return None
```
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
