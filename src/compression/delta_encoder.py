from __future__ import annotations

from typing import Optional

from src.compression.semantic_diff import (
    changed_values,
    focused_element,
    infer_available_actions,
    semantic_new_removed,
    summarize_screen,
)
from src.utils.screenshot import image_changed_bbox
from src.utils.types import ChangedRegion, GUIDelta, GUIObservation


class DeltaEncoder:
    def __init__(self, mode: str = "semantic") -> None:
        if mode not in {"pixel", "semantic", "hybrid"}:
            raise ValueError(f"unsupported delta mode: {mode}")
        self.mode = mode

    def compute_delta(
        self,
        prev_obs: GUIObservation,
        curr_obs: GUIObservation,
        last_keyframe_id: Optional[str] = None,
    ) -> GUIDelta:
        regions: list[ChangedRegion] = []
        if self.mode in {"pixel", "hybrid"}:
            bbox = image_changed_bbox(prev_obs.screenshot_path, curr_obs.screenshot_path)
            if bbox:
                regions.append(
                    ChangedRegion(
                        bbox=bbox,
                        change_type="layout_shift",
                        description="Pixels changed between consecutive GUI observations.",
                    )
                )

        new_elements: list[str] = []
        removed_elements: list[str] = []
        changed_elements = []
        focused = None
        available_actions: list[str] = []
        screen_summary = ""
        if self.mode in {"semantic", "hybrid"}:
            new_elements, removed_elements = semantic_new_removed(prev_obs, curr_obs)
            changed_elements = changed_values(prev_obs, curr_obs)
            focused = focused_element(curr_obs)
            available_actions = infer_available_actions(curr_obs)
            screen_summary = summarize_screen(curr_obs)

        url_changed = None
        if prev_obs.url != curr_obs.url:
            url_changed = {"old": prev_obs.url, "new": curr_obs.url}

        return GUIDelta(
            last_keyframe_id=last_keyframe_id,
            step_from=prev_obs.step_id,
            step_to=curr_obs.step_id,
            changed_regions=regions,
            screen_summary=screen_summary,
            new_elements=new_elements,
            removed_elements=removed_elements,
            changed_elements=changed_elements,
            focused_element=focused,
            available_actions=available_actions,
            url_changed=url_changed,
        )
