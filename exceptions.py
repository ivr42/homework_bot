"""Exceoptions for homework bot."""
from typing import Any


class BotError(Exception):
    """Base class for other exceptions."""

    pass


class ResponseKeyError(BotError):
    """Raises when found a key error in API response.

    Attributes:
        keys (Any): error keys
        message (str): explanation of the error
    """

    def __init__(self, keys: Any, message: str) -> None:
        """Class constructor."""
        self.keys = keys
        if isinstance(keys, (list, set, tuple)):
            self.message = f"{message}: {', '.join([key for key in keys])}"
        elif isinstance(keys, dict):
            self.message = f"{message}: "
            f"{', '.join([key for key in keys.keys()])}"
        else:
            self.message = f"{message}: {keys}"

        super().__init__(self.message)
