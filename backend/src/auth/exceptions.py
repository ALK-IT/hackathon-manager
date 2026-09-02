class InvalidAccessTokenError(Exception):
    pass


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidActionTokenError(Exception):
    pass


class RateLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
