from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Dict, List, Optional


INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "option"}


class _SimpleDOMParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: List[Dict[str, Any]] = []
        self.root: Dict[str, Any] = {"tag": "document", "attrs": {}, "text": "", "children": []}
        self.stack.append(self.root)

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        node = {"tag": tag, "attrs": dict(attrs), "text": "", "children": []}
        self.stack[-1]["children"].append(node)
        self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            current = self.stack[-1]
            current["text"] = f"{current.get('text', '')} {text}".strip()


def parse_html(html: str) -> Dict[str, Any]:
    parser = _SimpleDOMParser()
    parser.feed(html)
    return parser.root


def extract_visible_text(dom_tree: Optional[Dict[str, Any]]) -> List[str]:
    if not dom_tree:
        return []

    texts: List[str] = []

    def walk(node: Dict[str, Any]) -> None:
        text = " ".join(str(node.get("text", "")).split())
        if text:
            texts.append(text)
        for child in node.get("children", []) or []:
            walk(child)

    walk(dom_tree)
    return texts


def extract_elements(dom_tree: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not dom_tree:
        return []

    elements: List[Dict[str, Any]] = []

    def label_for(node: Dict[str, Any]) -> str:
        attrs = node.get("attrs", {}) or {}
        pieces = [
            attrs.get("aria-label"),
            attrs.get("placeholder"),
            attrs.get("value"),
            node.get("text"),
            attrs.get("name"),
            attrs.get("id"),
        ]
        return " ".join(str(piece).strip() for piece in pieces if piece).strip()

    def walk(node: Dict[str, Any]) -> None:
        tag = str(node.get("tag", ""))
        attrs = node.get("attrs", {}) or {}
        role = attrs.get("role")
        label = label_for(node)
        is_interactive = tag in INTERACTIVE_TAGS or role in {"button", "link", "textbox", "checkbox"}
        if label or is_interactive:
            elements.append(
                {
                    "tag": tag,
                    "role": role,
                    "label": label or tag,
                    "id": attrs.get("id"),
                    "name": attrs.get("name"),
                    "value": attrs.get("value"),
                    "type": attrs.get("type"),
                    "interactive": is_interactive,
                }
            )
        for child in node.get("children", []) or []:
            walk(child)

    walk(dom_tree)
    return elements
