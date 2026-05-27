# capitaineai-pages

A Python library for page/document management — content modeling, versioning, templating, navigation, and search.

## Installation

```bash
pip install capitaineai-pages
```

## Quick Start

```python
from capitaineai_pages import Page, Document, TemplateEngine, NavigationBuilder, SearchEngine

# Create pages with versioning
page = Page(title="Getting Started", content="Welcome to the guide!")
page.update(content="Updated guide with more detail", message="Revise intro")

# Assemble into a document
doc = Document(title="User Guide")
doc.add_page(page)
print(doc.toc_to_markdown())

# Full-text search
engine = SearchEngine()
engine.index_all(doc.pages)
results = engine.search("guide")

# Template rendering
tmpl = TemplateEngine()
tmpl.register("page", "# {{ title | title }}\n\n{{ content }}")
print(tmpl.render("page", {"title": "hello world", "content": "Body text"}))

# Navigation & sitemap
nav = NavigationBuilder(base_url="https://example.com")
print(nav.sitemap(doc.pages))
```

## Modules

- **`page`** — `Page` class with content, metadata, tags, slug generation, and full version history (commit, revert, diff)
- **`document`** — `Document` assembling pages with TOC generation, rendering, and word/char counts
- **`template`** — `TemplateEngine` with `{{ variable }}` substitution, filters (`upper`, `lower`, `title`), `{% for %}` loops, `{% if %}` conditionals, and custom filters
- **`navigation`** — `NavigationBuilder` with breadcrumbs, menu, hierarchical tree, and XML sitemap
- **`search`** — `SearchEngine` with TF-IDF scoring, snippets, and term suggestions

## Requirements

- Python 3.8+
- No external dependencies (pytest for testing only)

## Development

```bash
python3 -m pytest tests/ -q
```
