<div align="center">
  <h1>Simple HTTP Server from Scratch</h1>
</div>

<div>
    <p>As Software Engineers, we increasingly rely on libraries, frameworks, and now AI tools to move faster. Speed comes at a cost, as we often focus on <i>how</i> the tool itself works, or its output, without understanding the underlying concepts and what's happening underneath it. Having worked with web frameworks, such as FastAPI, to build APIs for production grade applications, I realised my knowledge of how HTTP requests/ responses are actually received, parsed and routed was thinner than I'd like.</p>
    <p>
      This project is my attempt to close that gap. I'm building an HTTP Server from scratch to better understand how the protocol works. I'll focus on the most basic features of HTTP, removing the layers of abstraction introduced by web frameworks. AI usage was also deliberately kept to a minimum to avoid cognitive debt, which would be against the project's spirit. My goals are:
      <ul>
        <li>Understand exactly the anatomy of an HTTP/1 request, how a stream of bytes is received and parsed into a request with path, headers and a correctly-delimited body.</li>
        <li>Understand how routing works, how a method and path are assigned to the correct handler.</li>
        <li>Understand how a response is constructed and sent back correctly, with proper headers, body and status code.</li>
        <li>Understand protocol-level details such chunked transfer encoding and persistent connections.</li>
      </ul>
    </p>
</div>

<div>
  <h2>Getting Started</h2>
  <p>Some commands here for easy start.</p>
</div>

<div>
  <h2>How It Works</h2>
</div>

<div>
  <h2>Features</h2>
  <h3>HTTP Parsing</h3>
  <h3>HTTP Routing</h3>
</div>

<div>
  <h2>CRUD Endpoints</h2>
</div>

<div>
  <h2>Data Layer</h2>
</div>

<div>
  <h2>Project Structure</h2>
</div>

<div>
  <h2>Testing</h2>
</div>

<div>
  <h2>What I Deliberately Skipped</h2>
  <p>
    <ul>
      <li>HTTPS/TLS is not a core concept of HTTP parsing.</li>
      <li>HTTP/2 is a separate protocol with different set of rules.</li>
      <li>Transfer-Encoding: compress, deflate, gzip is rarely used; moreover, it adds complexity without HTTP insight.</li>
      <li>A real database, since database management is out of scope for this project.</li>
    </ul>
  </p>
</div>

<div>
  <h2>Future Work</h2>
</div>

<div>
  <h2>Resources</h2>
</div>
