"""capitaineai-pages — A Python library for page/document management."""

from .page import Page, PageVersion
from .document import Document
from .template import TemplateEngine
from .navigation import NavigationBuilder
from .search import SearchEngine

__version__ = "0.1.0"
__all__ = [
    "Page",
    "PageVersion",
    "Document",
    "TemplateEngine",
    "NavigationBuilder",
    "SearchEngine",
]
