# capitaineai-com-pages

GitHub Pages source for [capitaine.ai](https://capitaine.ai) — the captain's AI domain in the Cocapn Fleet.

## What's Here

Static site assets plus a Python library for page/document management — content modeling, versioning, templating, navigation, and search.

## Live Site

**[capitaine.ai](https://capitaine.ai)**

## Page Library

```python
from capitaineai_pages import Page, Document, SearchEngine

page = Page(title="Getting Started", content="Welcome!")
page.update(content="Updated guide", message="Revise intro")

doc = Document(title="User Guide")
doc.add_page(page)

engine = SearchEngine()
engine.index_all(doc.pages)
results = engine.search("guide")
```

## Related

- [capitaine-agent](https://github.com/SuperInstance/capitaine-agent) — Captain's AI First Mate
- [capitaine-ai](https://github.com/SuperInstance/capitaine-ai) — Agent crew orchestration
