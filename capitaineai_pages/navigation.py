"""NavigationBuilder — breadcrumbs and sitemap generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .page import Page


@dataclass
class NavItem:
    """A navigation link."""

    title: str
    slug: str
    url: str = ""
    children: List["NavItem"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "title": self.title,
            "slug": self.slug,
            "url": self.url,
        }
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d


@dataclass
class Crumb:
    """A single breadcrumb entry."""

    title: str
    slug: str
    url: str = ""


class NavigationBuilder:
    """Build navigation structures: breadcrumbs, menus, sitemaps."""

    def __init__(self, base_url: str = "") -> None:
        self.base_url = base_url.rstrip("/")

    # ── breadcrumbs ──────────────────────────────────────────
    def breadcrumbs(
        self,
        page: Page,
        pages_by_slug: Optional[Dict[str, Page]] = None,
    ) -> List[Crumb]:
        """Build a breadcrumb trail from a slug-based hierarchy.

        Slugs like 'docs/getting-started/install' produce three levels.
        """
        slug = page.slug
        parts = slug.split("/") if "/" in slug else [slug]
        crumbs: List[Crumb] = []
        for i, part in enumerate(parts):
            full_slug = "/".join(parts[: i + 1])
            url = f"{self.base_url}/{full_slug}" if self.base_url else f"/{full_slug}"
            title = part.replace("-", " ").replace("_", " ").title()
            # Try to resolve title from provided pages
            if pages_by_slug and full_slug in pages_by_slug:
                resolved = pages_by_slug[full_slug]
                if resolved.title:
                    title = resolved.title
            crumbs.append(Crumb(title=title, slug=full_slug, url=url))
        return crumbs

    def breadcrumbs_to_html(self, crumbs: List[Crumb]) -> str:
        parts: List[str] = []
        for i, c in enumerate(crumbs):
            if i < len(crumbs) - 1:
                parts.append(f'<a href="{c.url}">{c.title}</a>')
            else:
                parts.append(f"<span>{c.title}</span>")
        return " / ".join(parts)

    # ── menu from pages ──────────────────────────────────────
    def build_menu(self, pages: List[Page]) -> List[NavItem]:
        """Build a flat navigation menu from a list of pages."""
        items: List[NavItem] = []
        for p in pages:
            url = f"{self.base_url}/{p.slug}" if self.base_url else f"/{p.slug}"
            items.append(NavItem(title=p.title, slug=p.slug, url=url))
        return items

    def build_tree(self, pages: List[Page]) -> List[NavItem]:
        """Build a hierarchical nav tree from slash-separated slugs.

        E.g. 'docs/intro' and 'docs/advanced' are children of 'docs'.
        """
        root: Dict[str, NavItem] = {}
        for p in pages:
            parts = p.slug.split("/")
            current = root
            for i, part in enumerate(parts):
                if part not in current:
                    full = "/".join(parts[: i + 1])
                    url = (
                        f"{self.base_url}/{full}"
                        if self.base_url
                        else f"/{full}"
                    )
                    nav = NavItem(
                        title=part.replace("-", " ").title(),
                        slug=full,
                        url=url,
                    )
                    current[part] = nav
                if i == len(parts) - 1:
                    # leaf — use the page's real title
                    current[part].title = p.title
                else:
                    if not hasattr(current[part], "_children_map"):
                        current[part]._children_map = {}  # type: ignore[attr-defined]
                    current = current[part]._children_map  # type: ignore[attr-defined]

        def _build(d: Dict[str, NavItem]) -> List[NavItem]:
            items = []
            for nav in d.values():
                child_map = getattr(nav, "_children_map", {})
                nav.children = _build(child_map)
                # clean up internal attr
                if hasattr(nav, "_children_map"):
                    delattr(nav, "_children_map")
                items.append(nav)
            return items

        return _build(root)

    # ── sitemap ──────────────────────────────────────────────
    def sitemap(self, pages: List[Page]) -> str:
        """Generate an XML sitemap from pages."""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        for p in pages:
            loc = f"{self.base_url}/{p.slug}" if self.base_url else f"/{p.slug}"
            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")
            lines.append(f"    <lastmod>{p.updated_at.strftime('%Y-%m-%d')}</lastmod>")
            lines.append("  </url>")
        lines.append("</urlset>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"NavigationBuilder(base_url={self.base_url!r})"
