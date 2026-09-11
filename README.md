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

---

## Features

---

## How I Built It

### TCP Server

### HTTP Server

### Router

### Request

### Response

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
