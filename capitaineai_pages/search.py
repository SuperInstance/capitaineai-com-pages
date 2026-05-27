"""SearchEngine — lightweight full-text search over pages."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from math import log
from typing import Any, Dict, List, Optional, Tuple

from .page import Page


@dataclass
class SearchResult:
    """A single search result with relevance scoring."""

    page_id: str
    page_title: str
    score: float
    snippet: str = ""
    matches: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id,
            "page_title": self.page_title,
            "score": round(self.score, 4),
            "snippet": self.snippet,
            "matches": self.matches,
        }


class SearchEngine:
    """Full-text search engine with TF-IDF scoring over a collection of pages."""

    _WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)

    def __init__(self) -> None:
        self._pages: Dict[str, Page] = {}
        # inverted index: term -> {page_id: count}
        self._index: Dict[str, Dict[str, int]] = {}
        self._doc_lengths: Dict[str, int] = {}

    # ── indexing ─────────────────────────────────────────────
    def index(self, page: Page) -> None:
        """Index a single page (replaces if already indexed)."""
        self._pages[page.id] = page
        self._build_index(page)

    def index_all(self, pages: List[Page]) -> None:
        """Index multiple pages at once."""
        for p in pages:
            self.index(p)

    def remove(self, page_id: str) -> bool:
        """Remove a page from the index."""
        if page_id not in self._pages:
            return False
        # remove from inverted index
        for term in list(self._index.keys()):
            if page_id in self._index[term]:
                del self._index[term][page_id]
                if not self._index[term]:
                    del self._index[term]
        del self._pages[page_id]
        self._doc_lengths.pop(page_id, None)
        return True

    def _build_index(self, page: Page) -> None:
        """Build inverted index entries for a page."""
        text = f"{page.title} {page.content}".lower()
        words = self._WORD_RE.findall(text)
        self._doc_lengths[page.id] = len(words)

        counts = Counter(words)
        for term, count in counts.items():
            if term not in self._index:
                self._index[term] = {}
            self._index[term][page.id] = count

    # ── searching ────────────────────────────────────────────
    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """Search pages using TF-IDF scoring. Returns results sorted by score."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        scores: Dict[str, float] = {}
        matched_terms: Dict[str, List[str]] = {}

        n_docs = len(self._pages)
        if n_docs == 0:
            return []

        for term in query_terms:
            if term not in self._index:
                continue
            # IDF
            doc_freq = len(self._index[term])
            idf = log(n_docs / doc_freq) + 1.0
            for page_id, tf in self._index[term].items():
                doc_len = self._doc_lengths.get(page_id, 1)
                tfidf = (tf / doc_len) * idf
                scores[page_id] = scores.get(page_id, 0.0) + tfidf
                matched_terms.setdefault(page_id, []).append(term)

        results: List[SearchResult] = []
        for page_id, score in scores.items():
            if score < min_score:
                continue
            page = self._pages[page_id]
            snippet = self._extract_snippet(page, query_terms)
            results.append(
                SearchResult(
                    page_id=page.id,
                    page_title=page.title,
                    score=score,
                    snippet=snippet,
                    matches=list(set(matched_terms.get(page_id, []))),
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _tokenize(self, text: str) -> List[str]:
        return self._WORD_RE.findall(text.lower())

    def _extract_snippet(
        self, page: Page, terms: List[str], context_chars: int = 60
    ) -> str:
        """Extract a short snippet around the first match."""
        text = page.content
        lower = text.lower()
        for term in terms:
            pos = lower.find(term)
            if pos >= 0:
                start = max(0, pos - context_chars)
                end = min(len(text), pos + len(term) + context_chars)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet
        return text[:100] + ("..." if len(text) > 100 else "")

    # ── info ─────────────────────────────────────────────────
    @property
    def indexed_count(self) -> int:
        return len(self._pages)

    @property
    def vocabulary_size(self) -> int:
        return len(self._index)

    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """Suggest terms matching a prefix."""
        prefix = prefix.lower()
        matches = [t for t in self._index if t.startswith(prefix)]
        matches.sort(key=lambda t: sum(self._index[t].values()), reverse=True)
        return matches[:limit]

    def __repr__(self) -> str:
        return f"SearchEngine(pages={self.indexed_count}, vocab={self.vocabulary_size})"
