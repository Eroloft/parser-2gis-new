class ParserException(Exception):
    pass


class ParserAccessBlocked(ParserException):
    """2GIS denied access or displayed an interactive challenge."""


__all__ = [
    'ParserException',
    'ParserAccessBlocked',
]
