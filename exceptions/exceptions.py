from typing import Optional


class BadRequestError(Exception):
    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message


class ProfileNotFoundError(Exception):
    pass
