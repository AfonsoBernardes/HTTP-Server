<div align="center">
  <h1>HTTP Server from Scratch</h1>
</div>

<div>
		<p>As software engineers, we increasingly rely on libraries, frameworks, and now AI tools to move faster. Speed comes at a cost, as we often focus on <i>how</i> the tool itself works, or its output, without understanding the underlying concepts and what's happening underneath it. Having worked with web frameworks, such as FastAPI, to build APIs for production grade applications, I realised my knowledge of how HTTP requests/ responses are actually received, parsed and routed was thinner than I'd like.</p>
		<p>This project is my attempt to close that gap. I'm building an HTTP Server from scratch to better understand how the protocol works. I'll focus on the most basic features of HTTP, removing the layers of abstraction introduced by web frameworks. AI usage was also deliberately kept to a minimum to avoid cognitive debt, which would be against the project's spirit. My goals are:</p>
			<ul>
				<li>Understand exactly the anatomy of an HTTP/1 request, how a stream of bytes is received and parsed into a request with path, headers and a correctly-delimited body.</li>
				<li>Understand how routing works, how a method and path are assigned to the correct handler.</li>
				<li>Understand how a response is constructed and sent back correctly, with proper headers, body and status code.</li>
				<li>Understand protocol-level details such chunked transfer encoding and persistent connections.</li>
			</ul>
</div>
<br>
<div>
	<h2>Theory</h2>
	
   <h3>Overview</h3>
	  	<p>HTTP serves as the foundation of any data exchange on the Web. It follows a client-server model where the client opens a connection to make a request and waits for a response from the server based on resources such as text, images, videos, etc.</p>
    	<p>HTTP requires an underlying transport layer to exchange requests and responses between the client and the server. Even though the transport layer does not need to be connection-based, HTTP requires it to be reliable and needs the guarantee that packets are correctly delivered. So, HTTP relies on <b>Transmission Control Protocol (TCP).</b></p>
   		
   <h4>Transmission Control Protocol/ Internet Protocol Model</h4>
				<p>TCP/ IP is a collection/ organisation of network protocols in different layers which models communications in a network. Its main objective is to ensure that the data sent by the sender arrives safely and correctly at the receiver’s end; data is broken down into smaller parts (packets) which travel separately and are reassembled in the correct order once the destination is reached.</p>
				<p>This model has four layers:</p>
		    	<ul>
		    	  <li><b>Application Layer</b> is the top layer, i.e., the one closest to the user where all the apps we use connect to the network live. It acts like a bridge between a software and the lower layers of the network that actually send and receive data, using HTTP for websites and SMTP for emails. This layer manages data formatting, encryption and session management.</li>
		    	  <li><b>Transport Layer</b> is responsible for ensuring data integrity and its reliable transport. This layer can use TCP or UDP (User Datagram Protocol); although UDP is faster, TCP makes sure that the data is correct and complete, checks for errors and resends missing pieces while keeping everything in order.</li>
		    	  <li><b>Internet Layer</b> finds the best path for data packets to travel across networks so it reaches the right destination. It gives every device a unique IP address, which identifies where data should go and route the best ways for it to travel.</li>
		    	  <li><b>Network Access Layer</b> is the bottom layer of the TCP/IP model and deals with the actual physical connection between devices, making sure data can travel over the hardware, while also checking for basic errors during transmission.</li>
		    	</ul>
				<p>So How does it really work? When sending data (sender to receiver),</p>
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
			
   <h4>Fundamentals of HTTP</h4>
	 		<p>As we've seen before, when a client wants to communicate with a server, it first needs to open a TCP connection to send a request and receive an answer; it may open a new connection, reuse an existing one, or even open several TCP connections. Once the connection is open, the client can send a message to the server, and consequently read the server's response. Once it's done, the connection can be closed or reused.</p>
			<p>However, some questions are left unanswered; how exactly does the server understand these messages? How does it know which resources were requested by the client? To demystify these concepts, we need to take a look at what an <b>Uniform Resource Locator (URL)</b> is and how these HTTP messages are organised.</p>
			<h5>Uniform Resource Locator (URL)</h5>
		 		<p>A URL is the address of a unique resource on the internet. Each valid URL points to a unique resource. A URL is composed of several parts:</p>
				
```
<Scheme>://<DomainName>:<Port>/<PathToResource>?<Parameters><Anchor>
```

   <p>The <b>"Scheme"</b> indicates the protocol that the browser must use to request the resource (HTTP or HTTPS). The <b>"DomainName"</b> indicates which Web server is being requested, sometimes the IP Address can also be used. The <b>"Port"</b> indicates the technical "gate" used to access the resources on the web server. Usually omitted if the web server uses the standard ports of the HTTP protocol (80 for HTTP and 443 for HTTPS) to grant access to its resources, otherwise it's mandatory. <b>"PathToResource"</b> represents a physical file location on the Web server; now, it is mostly an abstraction handled by Web servers without any physical reality. <b>"Parameters"</b> is a list of key/value pairs separated with the "&" symbol, which the server can use to do extra work before returning the resource. The <b>"Anchor"</b> is a sort of "bookmark" inside the resource, giving the browser the directions to show the content located at that bookmarked spot.</p>
			<h5>HTTP Messages</h5>
				<p>There is a common phrase which states that <b>"HTTP is just text"</b>. Indeed, HTTP is primarily a text-based protocol and, as defined in <i>HTTP/1.1</i> and earlier, messages are human-readable. Does that mean one can send a randomly formatted text message to a server and obtain a response? Of course not, these messages abide by a strict set of rules which allows the servers to parse a request and provide a response.</p>
				<p>An HTTP request is structured as follows,</p>
					
```
<METHOD> <PATH> <PROTOCOL VERSION>
<HEADERS>
\r\n
<REQUEST BODY>
```

  <p>and responses follow a similar structure,</p>

```
<PROTOCOL> <STATUS CODE> <MESSAGE>
<HEADERS>
\r\n
<MESSAGE BODY>
```
<br>
   <ul>
	   <li><b>METHOD:</b> defines the operation to be performed, like "GET" or "DELETE" a resource.</li>
	   <li><b>PATH:</b> defines where the resource is stored on the web server; the URL of the resource stripped from elements that are obvious from the context, without the protocol (http://), the domain, or the port.</li>
	   <li><b>PROTOCOL VERSION:</b> defines the version of the protocol, HTTP/1.0, HTTP/1.1, etc.</li>
	   <li><b>HEADERS:</b> optional <i>key:value</i> pairs contains additional information about the request and the client.</li>
	   <li><b>CRLF:</b> separates headers from data.</li>
	   <li><b>BODY:</b> is included to transmit data to the server or the client.</li>
	   <p><b>STATUS CODE:</b> indicate the result of an HTTP request.</p>
   </ul>

   <p>Once we're familiar with the fundamental theory behind HTTP and how it moves across the network, it's time to build.</p>
</div>
<br>
<div>
  <h2>Getting Started</h2>
  	<p>Some commands here for easy start.</p>
</div>
<br>
<div>
  <h2>Features</h2>
	  <h3>HTTP Parsing</h3>
	  <h3>HTTP Routing</h3>
</div>
<br>
<div>
  <h2>CRUD Endpoints</h2>
</div>
<br>
<div>
  <h2>Data Layer</h2>
</div>
<br>
<div>
  <h2>Project Structure</h2>
</div>
<br>
<div>
  <h2>Testing</h2>
</div>
<br>
<div>
  <h2>What I Deliberately Skipped</h2>
	  <p>
	    <ul>
	      <li>HTTPS/TLS is not a core concept of HTTP parsing.</li>
	      <li>HTTP/2 and HTTP/3 are extensions of the protocol with different set of rules.</li>
	      <li>Transfer-Encoding: compress, deflate, gzip is rarely used; moreover, it adds complexity without HTTP insight.</li>
	      <li>A real database, since database management is out of scope for this project.</li>
	    </ul>
	  </p>
</div>
<br>
<div>
  <h2>Future Work</h2>
</div>
<br>
<div>
  <h2>Resources</h2>
</div>
