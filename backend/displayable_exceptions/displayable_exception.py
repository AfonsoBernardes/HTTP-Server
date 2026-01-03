from uuid import uuid4


class DisplayableException(Exception):
    def __init__(self, message: str):
        self.exception_id = uuid4()
        self.message = f"{message}: {self.exception_id}"
        super().__init__(self.message)