from __future__ import annotations

from typing import Any, Dict, List, Optional


def flatten_accessibility_tree(tree: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not tree:
        return []

    nodes: List[Dict[str, Any]] = []

    def walk(node: Dict[str, Any]) -> None:
        role = node.get("role") or node.get("type")
        name = node.get("name") or node.get("label") or node.get("text")
        value = node.get("value")
        if role or name or value:
            nodes.append(
                {
                    "role": role,
                    "name": name,
                    "value": value,
                    "focused": bool(node.get("focused", False)),
                    "disabled": bool(node.get("disabled", False)),
                }
            )
        for child in node.get("children", []) or []:
            if isinstance(child, dict):
                walk(child)

    walk(tree)
    return nodes


def focused_node_name(tree: Optional[Dict[str, Any]]) -> Optional[str]:
    for node in flatten_accessibility_tree(tree):
        if node.get("focused"):
            return node.get("name") or node.get("role")
    return None
