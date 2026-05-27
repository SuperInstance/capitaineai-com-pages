"""TemplateEngine — variable substitution and rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Match, Optional


@dataclass
class Template:
    """A named template with content and metadata."""

    name: str
    content: str
    description: str = ""


class TemplateEngine:
    """Lightweight template engine with {{variable}} substitution and filters."""

    # matches {{ name }} or {{ name | filter }}
    _VAR_RE = re.compile(r"\{\{\s*(\w+)(?:\s*\|\s*(\w+))?\s*\}\}")
    # matches {% for item in items %}...{% endfor %}
    _FOR_RE = re.compile(
        r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
        re.DOTALL,
    )
    # matches {% if condition %}...{% endif %}
    _IF_RE = re.compile(
        r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}", re.DOTALL
    )

    def __init__(self) -> None:
        self._templates: Dict[str, Template] = {}
        self._filters: Dict[str, Callable[[str], str]] = {
            "upper": str.upper,
            "lower": str.lower,
            "strip": str.strip,
            "title": str.title,
            "capitalize": str.capitalize,
        }

    # ── template management ──────────────────────────────────
    def register(self, name: str, content: str, description: str = "") -> None:
        self._templates[name] = Template(
            name=name, content=content, description=description
        )

    def get(self, name: str) -> Optional[Template]:
        return self._templates.get(name)

    def list_templates(self) -> List[str]:
        return sorted(self._templates.keys())

    def remove(self, name: str) -> bool:
        if name in self._templates:
            del self._templates[name]
            return True
        return False

    # ── filter management ────────────────────────────────────
    def register_filter(self, name: str, func: Callable[[str], str]) -> None:
        self._filters[name] = func

    # ── rendering ────────────────────────────────────────────
    def render(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a registered template with the given context."""
        tmpl = self._templates.get(template_name)
        if tmpl is None:
            raise KeyError(f"Template not found: {template_name!r}")
        return self.render_string(tmpl.content, context or {})

    def render_string(
        self,
        template_str: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a raw template string with the given context."""
        ctx = context or {}

        # Process {% for %} blocks
        def _replace_for(m: Match[str]) -> str:
            item_var = m.group(1)
            list_var = m.group(2)
            body = m.group(3)
            items = ctx.get(list_var, [])
            parts: List[str] = []
            for item in items:
                sub_ctx = {**ctx, item_var: item}
                parts.append(self._replace_vars(body, sub_ctx))
            return "".join(parts)

        result = self._FOR_RE.sub(_replace_for, template_str)

        # Process {% if %} blocks
        def _replace_if(m: Match[str]) -> str:
            cond_var = m.group(1)
            body = m.group(2)
            value = ctx.get(cond_var)
            if value:
                return self._replace_vars(body, ctx)
            return ""

        result = self._IF_RE.sub(_replace_if, result)

        # Process {{ var }} and {{ var | filter }}
        result = self._replace_vars(result, ctx)
        return result

    def _replace_vars(self, text: str, ctx: Dict[str, Any]) -> str:
        def _sub(m: Match[str]) -> str:
            var = m.group(1)
            filt = m.group(2)
            value = ctx.get(var, "")
            s = str(value)
            if filt and filt in self._filters:
                s = self._filters[filt](s)
            return s

        return self._VAR_RE.sub(_sub, text)

    def __repr__(self) -> str:
        return f"TemplateEngine(templates={len(self._templates)})"
