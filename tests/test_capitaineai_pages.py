"""Tests for capitaineai_pages package."""

import pytest

from capitaineai_pages import (
    Document,
    NavigationBuilder,
    Page,
    PageVersion,
    SearchEngine,
    TemplateEngine,
)


# ─── Page tests ──────────────────────────────────────────────


class TestPage:
    def test_create_empty(self):
        p = Page()
        assert p.id
        assert p.title == ""
        assert p.content == ""
        assert p.slug == ""

    def test_create_with_title(self):
        p = Page(title="Hello World", content="Body text")
        assert p.slug == "hello-world"
        assert p.version_count == 1

    def test_slugify(self):
        assert Page._slugify("Hello World!") == "hello-world"
        assert Page._slugify("  foo   bar  ") == "foo-bar"
        assert Page._slugify("a--b__c") == "a-b-c"

    def test_update_creates_version(self):
        p = Page(title="Draft", content="v1")
        assert p.version_count == 1
        p.update(content="v2", message="Second edit")
        assert p.content == "v2"
        assert p.version_count == 2

    def test_version_history(self):
        p = Page(title="Doc", content="first")
        p.update(content="second", message="edit 2")
        p.update(content="third", message="edit 3")
        assert p.version_count == 3
        assert p.get_version(1).content == "first"
        assert p.get_version(2).content == "second"
        assert p.get_version(3).content == "third"

    def test_revert(self):
        p = Page(title="Doc", content="original")
        p.update(content="changed")
        v = p.revert_to(1)
        assert v is not None
        assert p.content == "original"
        assert p.version_count == 3  # original + update + revert

    def test_revert_nonexistent(self):
        p = Page(title="Doc", content="x")
        assert p.revert_to(99) is None

    def test_diff(self):
        p = Page(title="Doc", content="aaa")
        p.update(title="New Title", content="bbb")
        d = p.diff(1, 2)
        assert d is not None
        assert d["title"]["from"] == "Doc"
        assert d["title"]["to"] == "New Title"

    def test_diff_no_change(self):
        p = Page(title="Doc", content="same")
        p.update(content="same")
        assert p.diff(1, 2) is None

    def test_metadata_and_tags(self):
        p = Page(title="Test", content="c")
        p.update(metadata={"author": "alice"}, tags=["python", "ai"])
        assert p.metadata["author"] == "alice"
        assert "python" in p.tags

    def test_to_dict_roundtrip(self):
        p = Page(title="Roundtrip", content="content", slug="roundtrip")
        d = p.to_dict()
        assert d["title"] == "Roundtrip"
        p2 = Page.from_dict(d)
        assert p2.title == p.title
        assert p2.content == p.content
        assert p2.slug == p.slug

    def test_repr(self):
        p = Page(title="Test", content="x")
        assert "Test" in repr(p)


# ─── Document tests ─────────────────────────────────────────


class TestDocument:
    def _make_doc(self):
        doc = Document(title="My Book", description="A test book")
        doc.add_page(Page(title="Intro", content="# Introduction\nWelcome."))
        doc.add_page(Page(title="Chapter 1", content="# Widgets\n## Setup\nHere."))
        doc.add_page(Page(title="Chapter 2", content="# Gadgets\nSome info."))
        return doc

    def test_add_remove_pages(self):
        doc = Document(title="Test")
        p1 = Page(title="P1", content="c1")
        p2 = Page(title="P2", content="c2")
        doc.add_page(p1)
        doc.add_page(p2)
        assert doc.page_count == 2
        doc.remove_page(p1.id)
        assert doc.page_count == 1

    def test_get_page(self):
        doc = Document(title="T")
        p = Page(title="FindMe", content="x")
        doc.add_page(p)
        assert doc.get_page(p.id) is p
        assert doc.get_page("nope") is None

    def test_get_page_by_slug(self):
        doc = Document(title="T")
        p = Page(title="My Page", content="x")
        doc.add_page(p)
        assert doc.get_page_by_slug("my-page") is p

    def test_move_page(self):
        doc = Document(title="T")
        p1 = Page(title="First", content="a")
        p2 = Page(title="Second", content="b")
        doc.add_page(p1)
        doc.add_page(p2)
        doc.move_page(p2.id, 0)
        assert doc.pages[0].title == "Second"

    def test_insert_at_position(self):
        doc = Document(title="T")
        p1 = Page(title="A", content="a")
        p2 = Page(title="B", content="b")
        p3 = Page(title="C", content="c")
        doc.add_page(p1)
        doc.add_page(p2)
        doc.add_page(p3, position=1)
        assert doc.pages[1].title == "C"

    def test_generate_toc(self):
        doc = self._make_doc()
        toc = doc.generate_toc()
        assert len(toc) > 3  # pages + sub-headings
        assert toc[0].title == "Intro"
        assert toc[0].level == 1

    def test_toc_to_markdown(self):
        doc = self._make_doc()
        md = doc.toc_to_markdown()
        assert "[Intro]" in md
        assert "[Widgets]" in md

    def test_render(self):
        doc = self._make_doc()
        rendered = doc.render()
        assert "Welcome." in rendered
        assert "---" in rendered

    def test_render_with_headers(self):
        doc = self._make_doc()
        rendered = doc.render_with_headers()
        assert "# Intro" in rendered

    def test_word_char_counts(self):
        doc = Document(title="T")
        doc.add_page(Page(title="P", content="hello world foo"))
        assert doc.word_count == 3
        assert doc.char_count == 15

    def test_to_dict(self):
        doc = self._make_doc()
        d = doc.to_dict()
        assert d["title"] == "My Book"
        assert d["page_count"] == 3


# ─── TemplateEngine tests ───────────────────────────────────


class TestTemplateEngine:
    def test_simple_variable(self):
        engine = TemplateEngine()
        result = engine.render_string("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_multiple_variables(self):
        engine = TemplateEngine()
        result = engine.render_string(
            "{{ greeting }} {{ name }}", {"greeting": "Hi", "name": "Alice"}
        )
        assert result == "Hi Alice"

    def test_missing_variable_empty(self):
        engine = TemplateEngine()
        result = engine.render_string("Hello {{ name }}!", {})
        assert result == "Hello !"

    def test_filter_upper(self):
        engine = TemplateEngine()
        result = engine.render_string("{{ name | upper }}", {"name": "alice"})
        assert result == "ALICE"

    def test_filter_lower(self):
        engine = TemplateEngine()
        result = engine.render_string("{{ name | lower }}", {"name": "BOB"})
        assert result == "bob"

    def test_filter_title(self):
        engine = TemplateEngine()
        result = engine.render_string("{{ name | title }}", {"name": "hello world"})
        assert result == "Hello World"

    def test_for_loop(self):
        engine = TemplateEngine()
        tmpl = "{% for item in items %}{{ item }}, {% endfor %}"
        result = engine.render_string(tmpl, {"items": ["a", "b", "c"]})
        assert result == "a, b, c, "

    def test_if_condition_true(self):
        engine = TemplateEngine()
        tmpl = "{% if show %}visible{% endif %}"
        result = engine.render_string(tmpl, {"show": True})
        assert result == "visible"

    def test_if_condition_false(self):
        engine = TemplateEngine()
        tmpl = "{% if show %}visible{% endif %}"
        result = engine.render_string(tmpl, {"show": False})
        assert result == ""

    def test_register_and_render(self):
        engine = TemplateEngine()
        engine.register("greet", "Hello {{ name }}!")
        result = engine.render("greet", {"name": "World"})
        assert result == "Hello World!"

    def test_template_not_found(self):
        engine = TemplateEngine()
        with pytest.raises(KeyError):
            engine.render("missing")

    def test_list_templates(self):
        engine = TemplateEngine()
        engine.register("a", "A")
        engine.register("b", "B")
        assert engine.list_templates() == ["a", "b"]

    def test_remove_template(self):
        engine = TemplateEngine()
        engine.register("x", "X")
        assert engine.remove("x") is True
        assert engine.remove("x") is False

    def test_custom_filter(self):
        engine = TemplateEngine()
        engine.register_filter("reverse", lambda s: s[::-1])
        result = engine.render_string("{{ name | reverse }}", {"name": "abc"})
        assert result == "cba"


# ─── NavigationBuilder tests ────────────────────────────────


class TestNavigationBuilder:
    def test_breadcrumbs_simple(self):
        nav = NavigationBuilder(base_url="https://example.com")
        p = Page(title="Install", content="x", slug="docs/getting-started/install")
        crumbs = nav.breadcrumbs(p)
        assert len(crumbs) == 3
        assert crumbs[0].title == "Docs"
        assert crumbs[-1].title == "Install"
        assert crumbs[-1].url == "https://example.com/docs/getting-started/install"

    def test_breadcrumbs_no_slug_hierarchy(self):
        nav = NavigationBuilder()
        p = Page(title="About", content="x", slug="about")
        crumbs = nav.breadcrumbs(p)
        assert len(crumbs) == 1
        assert crumbs[0].title == "About"

    def test_breadcrumbs_html(self):
        nav = NavigationBuilder(base_url="https://site.com")
        p = Page(title="Install", content="x", slug="docs/install")
        crumbs = nav.breadcrumbs(p)
        html = nav.breadcrumbs_to_html(crumbs)
        assert "<a href=" in html
        assert "<span>" in html

    def test_build_menu(self):
        nav = NavigationBuilder(base_url="https://site.com")
        pages = [
            Page(title="Home", content="h", slug="home"),
            Page(title="About", content="a", slug="about"),
        ]
        menu = nav.build_menu(pages)
        assert len(menu) == 2
        assert menu[0].url == "https://site.com/home"

    def test_build_tree(self):
        nav = NavigationBuilder()
        pages = [
            Page(title="Intro", content="x", slug="docs/intro"),
            Page(title="Advanced", content="x", slug="docs/advanced"),
            Page(title="Home", content="x", slug="home"),
        ]
        tree = nav.build_tree(pages)
        assert len(tree) == 2  # docs + home
        docs = next(t for t in tree if t.slug == "docs")
        assert len(docs.children) == 2

    def test_sitemap(self):
        nav = NavigationBuilder(base_url="https://site.com")
        pages = [
            Page(title="Home", content="h", slug="home"),
            Page(title="About", content="a", slug="about"),
        ]
        xml = nav.sitemap(pages)
        assert '<?xml version' in xml
        assert "<loc>https://site.com/home</loc>" in xml
        assert "<urlset" in xml


# ─── SearchEngine tests ─────────────────────────────────────


class TestSearchEngine:
    def _make_engine(self):
        engine = SearchEngine()
        engine.index_all([
            Page(title="Python Basics", content="Learn Python programming fundamentals"),
            Page(title="JavaScript Guide", content="Modern JavaScript and web development"),
            Page(title="Python Advanced", content="Decorators, generators, and async Python"),
            Page(title="Machine Learning", content="Introduction to ML with Python"),
        ])
        return engine

    def test_basic_search(self):
        engine = self._make_engine()
        results = engine.search("Python")
        assert len(results) >= 2
        assert all("python" in r.matches for r in results)

    def test_search_ranking(self):
        engine = self._make_engine()
        results = engine.search("Python")
        # "Python Basics" and "Python Advanced" should rank higher than ML
        titles = [r.page_title for r in results]
        assert "Python Basics" in titles
        assert "Python Advanced" in titles

    def test_search_no_results(self):
        engine = self._make_engine()
        results = engine.search("quantum")
        assert len(results) == 0

    def test_search_limit(self):
        engine = self._make_engine()
        results = engine.search("Python", limit=1)
        assert len(results) <= 1

    def test_snippet(self):
        engine = self._make_engine()
        results = engine.search("fundamentals")
        assert len(results) == 1
        assert "fundamentals" in results[0].snippet

    def test_index_and_remove(self):
        engine = SearchEngine()
        p = Page(title="Test", content="unique keyword xyz")
        engine.index(p)
        assert engine.indexed_count == 1
        results = engine.search("xyz")
        assert len(results) == 1

        engine.remove(p.id)
        assert engine.indexed_count == 0
        results = engine.search("xyz")
        assert len(results) == 0

    def test_suggest(self):
        engine = self._make_engine()
        suggestions = engine.suggest("py")
        assert "python" in suggestions

    def test_vocabulary_size(self):
        engine = self._make_engine()
        assert engine.vocabulary_size > 0

    def test_result_to_dict(self):
        engine = self._make_engine()
        results = engine.search("Python")
        d = results[0].to_dict()
        assert "page_id" in d
        assert "score" in d
        assert isinstance(d["score"], float)


# ─── Integration tests ──────────────────────────────────────


class TestIntegration:
    def test_full_workflow(self):
        # Create pages
        p1 = Page(title="Getting Started", content="# Quick Start\nInstall the package.")
        p2 = Page(title="Configuration", content="# Config\nSet up your config file.")
        p3 = Page(title="Deployment", content="# Deploy\nPush to production.")

        # Build document
        doc = Document(title="User Guide", description="Complete guide")
        doc.add_page(p1)
        doc.add_page(p2)
        doc.add_page(p3)
        assert doc.page_count == 3

        # TOC
        toc = doc.generate_toc()
        assert any(t.title == "Quick Start" for t in toc)

        # Navigation
        nav = NavigationBuilder(base_url="https://docs.example.com")
        tree = nav.build_tree(doc.pages)
        assert len(tree) == 3

        # Search
        engine = SearchEngine()
        engine.index_all(doc.pages)
        results = engine.search("production")
        assert len(results) == 1
        assert results[0].page_title == "Deployment"

        # Template
        tmpl = TemplateEngine()
        tmpl.register("page", "# {{ title }}\n\n{{ content }}")
        rendered = tmpl.render("page", {"title": p1.title, "content": p1.content})
        assert "Getting Started" in rendered

    def test_page_versioning_workflow(self):
        p = Page(title="Changelog", content="v0.1")
        p.update(content="v0.1 - Initial release", message="details")
        p.update(content="v0.2 - Added search", message="new feature")
        assert p.version_count == 3

        diff = p.diff(1, 3)
        assert diff is not None

        p.revert_to(1)
        assert p.content == "v0.1"
