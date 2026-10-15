import re

from .parsers import FirmParser, InBuildingParser, MainParser
from .parsers.official_api import OfficialApiParser

PARSER_TYPES = (FirmParser, InBuildingParser, MainParser)


def get_parser_type(url):
    """Return the parser class matching ``url``, or ``None`` when unsupported."""
    for parser in PARSER_TYPES:
        if re.match(parser.url_pattern(), url):
            return parser
    return None


def is_supported_url(url) -> bool:
    """Whether ``url`` has a route implemented by the source project."""
    return get_parser_type(url) is not None


def get_parser(url, chrome_options, parser_options):
    """Parser factory function.

    Args:
        url: 2GIS URLs with items to be collected.
        chrome_options: Chrome options.
        parser_options: Parser options.

    Returns:
        Parser instance.
    """
    parser = get_parser_type(url)
    if parser is None:
        raise ValueError(
            'Неподдерживаемая ссылка 2GIS. Используйте ссылку поиска '
            '(/search/...), карточки организации (/firm/...) или списка '
            'организаций в здании (/inside/...).'
        )
    if parser_options.api_key:
        return OfficialApiParser(url, parser_options)
    return parser(url, chrome_options, parser_options)
