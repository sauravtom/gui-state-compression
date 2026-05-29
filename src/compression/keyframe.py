from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from src.utils.types import GUIObservation


@dataclass
class Keyframe:
    keyframe_id: str
    step_id: int
    observation: GUIObservation


class KeyframeStore:
    def __init__(self, interval: int) -> None:
        if interval < 1:
            raise ValueError("keyframe interval must be >= 1")
        self.interval = interval
        self._frames: Dict[str, Keyframe] = {}
        self._latest: Optional[Keyframe] = None

    def maybe_add(self, observation: GUIObservation) -> Optional[Keyframe]:
        if observation.step_id % self.interval == 0 or self._latest is None:
            keyframe = Keyframe(
                keyframe_id=f"kf_{observation.step_id:04d}",
                step_id=observation.step_id,
                observation=observation,
            )
            self._frames[keyframe.keyframe_id] = keyframe
            self._latest = keyframe
            return keyframe
        return None

    @property
    def latest(self) -> Optional[Keyframe]:
        return self._latest

    def get(self, keyframe_id: str) -> Keyframe:
        return self._frames[keyframe_id]
