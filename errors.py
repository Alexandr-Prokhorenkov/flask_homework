class HttpError(Exception):

    def __init__(self, message: str | list | dict, status_code: int):
        self.message = message
        self.status_code = status_code
