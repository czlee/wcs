"""Scoresheet parsers for various competition result sources.

Vendored from ~/who-woulda-won/core/parsers/__init__.py. The registry mechanism
is copied unchanged; the only omission is `get_supported_url_formats` (user-facing
help text, not needed for extraction).
"""

from .base import ScoresheetParser

# Parser registry - import parsers here to register them
_parsers: list[type[ScoresheetParser]] = []


def register_parser(parser_class: type[ScoresheetParser]) -> type[ScoresheetParser]:
    """Decorator to register a parser class."""
    _parsers.append(parser_class)
    return parser_class


def get_all_parsers() -> list[type[ScoresheetParser]]:
    """Return all registered parser classes."""
    return _parsers.copy()


def detect_parser(source: str) -> ScoresheetParser | None:
    """Auto-detect and return an appropriate parser instance for the given source."""
    for parser_class in _parsers:
        parser = parser_class()
        if parser.can_parse(source):
            return parser
    return None


def detect_parser_by_content(content: bytes, filename: str) -> ScoresheetParser | None:
    """Auto-detect a parser by inspecting file content.

    Used for file uploads where there is no URL to match against.
    """
    for parser_class in _parsers:
        parser = parser_class()
        if parser.can_parse_content(content, filename):
            return parser
    return None
