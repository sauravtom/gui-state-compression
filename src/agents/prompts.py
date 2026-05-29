from __future__ import annotations

import json
from typing import Iterable, List

from src.utils.types import GUIAction, GUIDelta, GUIObservation


ACTION_SCHEMA = {
    "reasoning_summary": "short non-sensitive rationale",
    "action": {
        "type": "click | type | scroll | wait | finish",
        "target": "human-readable target or null",
        "text": "text to type or null",
        "coordinates": [0, 0],
    },
    "confidence": 0.0,
}


def observation_payload(obs: GUIObservation, include_screenshot: bool = True) -> dict:
    data = obs.to_dict()
    if not include_screenshot:
        data.pop("screenshot_path", None)
    return data


def compress_action_history(actions: List[GUIAction], mode: str) -> object:
    if mode == "none":
        return [action.to_dict() for action in actions]
    if mode == "action_only":
        return [action.type for action in actions]
    if mode == "summary":
        if not actions:
            return "No previous actions."
        return "; ".join(
            f"{idx + 1}. {action.type} {action.target or ''} {action.text or ''}".strip()
            for idx, action in enumerate(actions[-8:])
        )
    if mode == "state_summary":
        if not actions:
            return "No progress yet."
        last = actions[-1]
        return f"Completed {len(actions)} actions. Last action was {last.type} on {last.target or 'current UI'}."
    raise ValueError(f"unsupported history compression: {mode}")


def build_baseline_prompt(
    task_instruction: str,
    current_observation: GUIObservation,
    observation_history: Iterable[GUIObservation],
    action_history: List[GUIAction],
    history_compression: str = "none",
) -> str:
    payload = {
        "role": "computer_use_agent",
        "mode": "full_context_baseline",
        "instruction": task_instruction,
        "current_screenshot": current_observation.screenshot_path,
        "current_observation": observation_payload(current_observation),
        "full_observation_history": [observation_payload(obs) for obs in observation_history],
        "history": compress_action_history(action_history, history_compression),
        "response_format": ACTION_SCHEMA,
    }
    return (
        "You are controlling a computer. Here is the current screenshot, full GUI "
        "history, action history, and task. Choose the next action as strict JSON.\n"
        + json.dumps(payload, sort_keys=True, default=str)
    )


def build_last_screenshot_prompt(
    task_instruction: str,
    current_observation: GUIObservation,
    action_history: List[GUIAction],
) -> str:
    payload = {
        "role": "computer_use_agent",
        "mode": "last_screenshot_only",
        "instruction": task_instruction,
        "current_screenshot": current_observation.screenshot_path,
        "url": current_observation.url,
        "history": compress_action_history(action_history, "action_only"),
        "response_format": ACTION_SCHEMA,
    }
    return json.dumps(payload, sort_keys=True, default=str)


def build_compressed_prompt(
    task_instruction: str,
    keyframe: GUIObservation,
    deltas: List[GUIDelta],
    action_history: List[GUIAction],
    delta_mode: str,
    history_compression: str,
) -> str:
    payload = {
        "role": "computer_use_agent",
        "mode": f"{delta_mode}_compressed",
        "instruction": task_instruction,
        "previous_keyframe": observation_payload(keyframe),
        "deltas_since_keyframe": [delta.to_dict() for delta in deltas],
        "compressed_history": compress_action_history(action_history, history_compression),
        "response_format": ACTION_SCHEMA,
    }
    return (
        "You are controlling a computer. You have a previous keyframe and the "
        "following GUI deltas. Reconstruct the current state mentally and choose "
        "the next action as strict JSON.\n"
        + json.dumps(payload, sort_keys=True, default=str)
    )
