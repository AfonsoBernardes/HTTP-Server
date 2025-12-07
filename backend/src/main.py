def run_server():
    # Let's restrict requests to GET, POST, PUT and DELETE.
    # Find out what the structure of a request is like and start parsing line by line.
        # Depending on the request, return a proper response; let's do a "200 OK" or a "400 Bad Request" for now.

    print("Hello from http-server!")


if __name__ == "__main__":
    run_server()
