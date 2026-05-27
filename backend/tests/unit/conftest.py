class FakeSocket:
    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def recv(self, bufsize: int):
        return next(self._chunks, b"")

    def send(self, data: bytes):
        pass