"""Document — assembles Pages into a structured document with TOC."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .page import Page


@dataclass
class TOCEntry:
    """A single entry in the table of contents."""

    title: str
    slug: str
    level: int = 1
    page_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "level": self.level,
            "page_id": self.page_id,
        }


@dataclass
class Document:
    """A collection of ordered pages forming a document with metadata and TOC."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    description: str = ""
    author: str = ""
    pages: List[Page] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── page management ──────────────────────────────────────
    def add_page(self, page: Page, position: Optional[int] = None) -> None:
        """Add a page at an optional position (default: end)."""
        if position is None:
            self.pages.append(page)
        else:
            self.pages.insert(position, page)
        self._touch()

    def remove_page(self, page_id: str) -> bool:
        before = len(self.pages)
        self.pages = [p for p in self.pages if p.id != page_id]
        removed = len(self.pages) < before
        if removed:
            self._touch()
        return removed

    def get_page(self, page_id: str) -> Optional[Page]:
        for p in self.pages:
            if p.id == page_id:
                return p
        return None

    def get_page_by_slug(self, slug: str) -> Optional[Page]:
        for p in self.pages:
            if p.slug == slug:
                return p
        return None

    def move_page(self, page_id: str, new_position: int) -> bool:
        page = self.get_page(page_id)
        if page is None:
            return False
        self.pages = [p for p in self.pages if p.id != page_id]
        self.pages.insert(new_position, page)
        self._touch()
        return True

    # ── TOC ──────────────────────────────────────────────────
    def generate_toc(self, max_level: int = 3) -> List[TOCEntry]:
        """Generate a table of contents from page content headings.

        Scans each page's content for markdown-style headings (# Title).
        """
        entries: List[TOCEntry] = []
        for page in self.pages:
            entries.append(
                TOCEntry(
                    title=page.title,
                    slug=page.slug or Page._slugify(page.title),
                    level=1,
                    page_id=page.id,
                )
            )
            for line in page.content.splitlines():
                if not line.startswith("#"):
                    continue
                stripped = line.lstrip("#")
                level = len(line) - len(stripped)
                if 1 <= level <= max_level:
                    heading = stripped.strip()
                    if heading:
                        entries.append(
                            TOCEntry(
                                title=heading,
                                slug=Page._slugify(heading),
                                level=level,
                                page_id=page.id,
                            )
                        )
        return entries

    def toc_to_markdown(self, max_level: int = 3) -> str:
        """Render the TOC as a markdown string."""
        entries = self.generate_toc(max_level)
        lines: List[str] = []
        for e in entries:
            indent = "  " * (e.level - 1)
            lines.append(f"{indent}- [{e.title}](#{e.slug})")
        return "\n".join(lines)

    # ── rendering ────────────────────────────────────────────
    def render(self, separator: str = "\n\n---\n\n") -> str:
        """Render the full document as concatenated page contents."""
        return separator.join(p.content for p in self.pages)

    def render_with_headers(self) -> str:
        """Render each page with its title as a heading."""
        parts: List[str] = []
        for p in self.pages:
            parts.append(f"# {p.title}\n\n{p.content}")
        return "\n\n---\n\n".join(parts)

    # ── word / char counts ───────────────────────────────────
    @property
    def word_count(self) -> int:
        return sum(len(p.content.split()) for p in self.pages)

    @property
    def char_count(self) -> int:
        return sum(len(p.content) for p in self.pages)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    # ── helpers ──────────────────────────────────────────────
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "pages": [p.to_dict() for p in self.pages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "word_count": self.word_count,
            "page_count": self.page_count,
        }

    def __repr__(self) -> str:
        return f"Document(id={self.id!r}, title={self.title!r}, pages={self.page_count})"
