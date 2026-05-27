"""Page model with content, metadata, and versioning."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class PageVersion:
    """A snapshot of a page at a point in time."""

    version: int
    content: str
    title: str
    timestamp: datetime
    author: str = ""
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "content": self.content,
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "message": self.message,
        }


@dataclass
class Page:
    """A single page with content, metadata, and full version history."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    slug: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    _versions: List[PageVersion] = field(default_factory=list, repr=False)
    _current_version: int = 0

    def __post_init__(self) -> None:
        if not self.slug and self.title:
            self.slug = self._slugify(self.title)
        if self.content and not self._versions:
            self._commit(message="Initial version")

    # ── slug helper ──────────────────────────────────────────
    @staticmethod
    def _slugify(text: str) -> str:
        slug = ""
        for ch in text.lower().strip():
            if ch.isalnum() or ch == "-":
                slug += ch
            elif ch in (" ", "_"):
                slug += "-"
        # collapse dashes
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")[:64]

    # ── versioning ───────────────────────────────────────────
    def _commit(self, message: str = "", author: str = "") -> PageVersion:
        self._current_version += 1
        ver = PageVersion(
            version=self._current_version,
            content=self.content,
            title=self.title,
            timestamp=datetime.now(timezone.utc),
            author=author,
            message=message,
        )
        self._versions.append(ver)
        self.updated_at = ver.timestamp
        return ver

    def update(
        self,
        content: Optional[str] = None,
        title: Optional[str] = None,
        message: str = "",
        author: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> PageVersion:
        """Update the page and create a new version."""
        if content is not None:
            self.content = content
        if title is not None:
            self.title = title
            if not self.slug:
                self.slug = self._slugify(title)
        if metadata is not None:
            self.metadata.update(metadata)
        if tags is not None:
            self.tags = list(tags)
        return self._commit(message=message, author=author)

    @property
    def versions(self) -> List[PageVersion]:
        return list(self._versions)

    @property
    def version_count(self) -> int:
        return len(self._versions)

    def get_version(self, version: int) -> Optional[PageVersion]:
        for v in self._versions:
            if v.version == version:
                return v
        return None

    def revert_to(self, version: int, author: str = "") -> Optional[PageVersion]:
        """Revert the page content/title to a previous version."""
        target = self.get_version(version)
        if target is None:
            return None
        self.content = target.content
        self.title = target.title
        return self._commit(
            message=f"Reverted to version {version}", author=author
        )

    def diff(self, v1: int, v2: int) -> Optional[Dict[str, Any]]:
        """Compare two versions. Returns fields that changed."""
        a = self.get_version(v1)
        b = self.get_version(v2)
        if a is None or b is None:
            return None
        changes: Dict[str, Any] = {}
        if a.title != b.title:
            changes["title"] = {"from": a.title, "to": b.title}
        if a.content != b.content:
            changes["content"] = {"from": a.content, "to": b.content}
        return changes or None

    # ── serialization ────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version_count": self.version_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Page":
        page = cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            slug=data.get("slug", ""),
            tags=data.get("tags", []),
        )
        if not page.id:
            page.id = uuid.uuid4().hex[:12]
        return page

    def __repr__(self) -> str:
        return f"Page(id={self.id!r}, title={self.title!r}, v{self.version_count})"
