<div align="center">
  <h1>HTTP Server from Scratch</h1>
</div>

As software engineers, we increasingly rely on libraries, frameworks, and now AI tools to move faster. Speed comes at a cost, as we often focus on _how_ the tool itself works, or its output, without understanding the underlying concepts and what's happening underneath it. Having worked with web frameworks, such as FastAPI, to build APIs for production grade applications, I realised my knowledge of how HTTP requests/ responses are actually received, parsed and routed was thinner than I'd like.

This project is my attempt to close that gap. I'm building an HTTP Server from scratch to better understand how the protocol works. I'll focus on the most basic features of HTTP, removing the layers of abstraction introduced by web frameworks. AI usage was also deliberately kept to a minimum to avoid cognitive debt, which would be against the project's spirit. My goals are:

<ul>
	<li>Understand exactly the anatomy of an HTTP/1 request, how a stream of bytes is received and parsed into a request with path, headers and a correctly-delimited body.</li>
	<li>Understand how routing works, how a method and path are assigned to the correct handler.</li>
	<li>Understand how a response is constructed and sent back correctly, with proper headers, body and status code.</li>
	<li>Understand protocol-level details such chunked transfer encoding and persistent connections.</li>
</ul>

> New to HTTP? See [THEORY.md](./THEORY.md) for the fundamentals of HTTP/TCP. This README focuses on what I built, how I built it and explains the decisions along the way.


## Features
### HTTP Parsing
### HTTP Routing

## How I built It

## Getting Started

Some commands here for easy start.

## Project Structure


## Future Work

## What I Deliberately Skipped
<ul>
	<li>HTTP/2 and HTTP/3 are separate protocols with different sets of rules. HTTP/1.1 is readable as plain-text, which makes the fundamentals visible.</li>
	<li>HTTPS is just HTTP sent over a TLS-encrypted connection, which does not concern this project's scope since it happens before the request is handled.</li>
	<li>Transfer-Encoding: compress, deflate, gzip is rarely used; moreover, it adds complexity without HTTP insight.</li>
	<li>A real database, since database management is out of scope for this project.</li>
</ul>

## Resources
