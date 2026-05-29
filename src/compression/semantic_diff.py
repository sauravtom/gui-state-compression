from __future__ import annotations

from typing import Iterable, List, Optional, Set

from src.utils.accessibility_parser import flatten_accessibility_tree, focused_node_name
from src.utils.dom_parser import extract_elements, extract_visible_text
from src.utils.types import ChangedElement, GUIObservation


def _norm(value: Optional[str]) -> str:
    return " ".join(str(value or "").split()).strip()


def observation_text_set(obs: GUIObservation) -> Set[str]:
    texts = set(_norm(text) for text in extract_visible_text(obs.dom_tree))
    if obs.ocr_text:
        texts.update(_norm(line) for line in obs.ocr_text.splitlines())
    texts.update(_norm(node.get("name")) for node in flatten_accessibility_tree(obs.accessibility_tree))
    return {text for text in texts if text}


def element_labels(obs: GUIObservation) -> Set[str]:
    labels = set()
    for element in extract_elements(obs.dom_tree):
        label = _norm(element.get("label"))
        if label:
            labels.add(label)
    for node in flatten_accessibility_tree(obs.accessibility_tree):
        label = _norm(node.get("name") or node.get("role"))
        if label:
            labels.add(label)
    return labels


def element_values(obs: GUIObservation) -> dict[str, str]:
    values: dict[str, str] = {}
    for element in extract_elements(obs.dom_tree):
        label = _norm(element.get("label"))
        value = _norm(element.get("value"))
        if label and value:
            values[label] = value
    for node in flatten_accessibility_tree(obs.accessibility_tree):
        label = _norm(node.get("name") or node.get("role"))
        value = _norm(node.get("value"))
        if label and value:
            values[label] = value
    return values


def summarize_screen(obs: GUIObservation) -> str:
    texts = list(observation_text_set(obs))
    url_part = f" at {obs.url}" if obs.url else ""
    if not texts:
        return f"GUI state step {obs.step_id}{url_part}."
    sample = "; ".join(sorted(texts)[:4])
    return f"GUI state step {obs.step_id}{url_part}: {sample}"


def infer_available_actions(obs: GUIObservation) -> List[str]:
    actions: List[str] = []
    for element in extract_elements(obs.dom_tree):
        if not element.get("interactive"):
            continue
        label = _norm(element.get("label"))
        tag = element.get("tag")
        role = element.get("role")
        typ = element.get("type")
        if tag in {"input", "textarea"} or role == "textbox" or typ in {"text", "search", "email"}:
            actions.append(f"type into {label}")
        elif tag == "select":
            actions.append(f"select {label}")
        else:
            actions.append(f"click {label}")
    for node in flatten_accessibility_tree(obs.accessibility_tree):
        role = _norm(node.get("role"))
        name = _norm(node.get("name"))
        if role in {"button", "link"} and name:
            actions.append(f"click {name}")
        elif role in {"textbox", "searchbox"} and name:
            actions.append(f"type into {name}")
    deduped = []
    for action in actions:
        if action not in deduped:
            deduped.append(action)
    return deduped[:12]


def changed_values(prev: GUIObservation, curr: GUIObservation) -> List[ChangedElement]:
    prev_values = element_values(prev)
    curr_values = element_values(curr)
    changes: List[ChangedElement] = []
    for label in sorted(set(prev_values) | set(curr_values)):
        old = prev_values.get(label)
        new = curr_values.get(label)
        if old != new:
            changes.append(ChangedElement(element=label, old=old, new=new))
    return changes


def semantic_new_removed(prev: GUIObservation, curr: GUIObservation) -> tuple[List[str], List[str]]:
    prev_elements = element_labels(prev) | observation_text_set(prev)
    curr_elements = element_labels(curr) | observation_text_set(curr)
    new_elements = sorted(curr_elements - prev_elements)
    removed_elements = sorted(prev_elements - curr_elements)
    return new_elements[:40], removed_elements[:40]


def focused_element(obs: GUIObservation) -> Optional[str]:
    return obs.focused_element or focused_node_name(obs.accessibility_tree)
