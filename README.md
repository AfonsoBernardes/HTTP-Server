<div align="center">
  <h1>HTTP Server from Scratch</h1>
</div>

<div>
    <p>As Software Engineers, we increasingly rely on libraries, frameworks, and now AI tools to move faster. Speed comes at a cost, as we often focus on <i>how</i> the tool itself works, or its output, without understanding the underlying concepts and what's happening underneath it. Having worked with web frameworks, such as FastAPI, to build APIs for production grade applications, I realised my knowledge of how HTTP requests/ responses are actually received, parsed and routed was thinner than I'd like.</p>
    <p>This project is my attempt to close that gap. I'm building an HTTP Server from scratch to better understand how the protocol works. I'll focus on the most basic features of HTTP, removing the layers of abstraction introduced by web frameworks. AI usage was also deliberately kept to a minimum to avoid cognitive debt, which would be against the project's spirit. My goals are:</p>
      <ul>
        <li>Understand exactly the anatomy of an HTTP/1 request, how a stream of bytes is received and parsed into a request with path, headers and a correctly-delimited body.</li>
        <li>Understand how routing works, how a method and path are assigned to the correct handler.</li>
        <li>Understand how a response is constructed and sent back correctly, with proper headers, body and status code.</li>
        <li>Understand protocol-level details such chunked transfer encoding and persistent connections.</li>
      </ul>
</div>

<div>
	<h2>How It Works</h2>
	
   <h3>Overview</h3>
	  <p>HTTP serves as the foundation of any data exchange on the Web. It follows a client-server model where the client opens a connection to make a request and waits for a response from the server based on resources such as text, images, videos, etc.</p>
    <p>HTTP requires an underlying transport layer to exchange requests and responses between the client and the server. Even though the transport layer does not need to be connection-based, HTTP requires it to be reliable and needs the guarantee that packets are correctly delivered. So, HTTP relies on <b>Transmission Control Protocol (TCP).</b></p>

   <h4>Transmission Control Protocol/ Internet Protocol Model</h4>
    <p>TCP/ IP is a collection/ organisation of network protocols in different layers which models communications in a network. Its main objective it to ensure that the data sent by the sender arrives safely and correctly at the receiver’s end; data is broken down into smaller parts (packets) which travel separately and are reassembled in the correct order once the destination is reached.</p>
    <p>This model has four layers:</p>
    	<ul>
    	  <li><b>Application Layer</b> is the top layer, i.e., the one closest to the user where all the apps we use connect to the network live. It acts like a bridge between a software and the lower layers of the network that actually send and receive data, using HTTP for websites and SMTP for emails. This layers manages data formatting, encryption and session management.</li>
    	  <li><b>Transport Layer</b> is responsible for ensuring data integrity and its reliable transport. This layer can use TCP or UDP (User Datagram Protocol); although UDP is faster, TCP makes sure that the data is correct and complete, checks for errors and resends missing pieces while keeping everything in order.</li>
    	  <li><b>Internet Layer</b> finds the best path for data packets to travel across networks so it reaches the right destination. It gives every device a unique IP address, which identifies where data should go and route the best ways for it to travel.</li>
    	  <li><b>Network Access Layer</b> is the bottom layer of the TCP/IP model and deals with the actual physical connection between devices, making sure data can travel over the hardware, while also checking for basic errors during transmission.</li>
    	</ul>
    <p>So How does it really work? When sending data (sender to reciever),</p>
      <ol>
        <li>The Application Layer prepares the user's data, with HTTP for example.</li>
        <li>The Transport Layer breaks data into segments and ensures reliable (TCP) or fast (UDP) delivery.</li>
        <li>The Internet Layer adds IP addresses and decides the best route for each packet.</li>
        <li>The Network Access Layer converts packets into frames and sends them over the physical network.</li>
      </ol>
    <p>When receiving data (at the destination),</p>
      <ol>
        <li>The Network Access Layer receives bits from the network and rebuilds frames to pass to the next layer.</li>
        <li>The Internet Layer checks the IP address, removes the IP header, and forwards data to the Transport Layer.</li>
        <li>The Transport Layer reassembles segments, checks for errors, and ensures data is complete.</li>
        <li>The Application Layer delivers the final data to the correct application (e.g., displays a web page in the browser).</li>
      </ol>
</div>

<div>
  <h2>Getting Started</h2>
  <p>Some commands here for easy start.</p>
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
