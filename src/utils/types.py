from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class GUIObservation:
    step_id: int
    screenshot_path: Optional[str] = None
    dom_tree: Optional[Dict[str, Any]] = None
    accessibility_tree: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None
    url: Optional[str] = None
    active_window: Optional[str] = None
    focused_element: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangedRegion:
    bbox: List[int]
    change_type: str
    description: str


@dataclass
class ChangedElement:
    element: str
    old: Optional[str]
    new: Optional[str]


@dataclass
class GUIDelta:
    last_keyframe_id: Optional[str]
    step_from: int
    step_to: int
    changed_regions: List[ChangedRegion] = field(default_factory=list)
    screen_summary: str = ""
    new_elements: List[str] = field(default_factory=list)
    removed_elements: List[str] = field(default_factory=list)
    changed_elements: List[ChangedElement] = field(default_factory=list)
    focused_element: Optional[str] = None
    available_actions: List[str] = field(default_factory=list)
    url_changed: Optional[Dict[str, Optional[str]]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GUIAction:
    type: str
    target: Optional[str] = None
    text: Optional[str] = None
    coordinates: Optional[Sequence[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentDecision:
    reasoning_summary: str
    action: GUIAction
    confidence: float
    prompt_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action"] = self.action.to_dict()
        return data


@dataclass
class TaskSpec:
    task_id: str
    task_type: str
    instruction: str
    start_url: str
    success_condition: str
    trajectory: List[GUIObservation]
    ideal_actions: List[GUIAction]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepRecord:
    task_id: str
    mode: str
    keyframe_interval: int
    step_id: int
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model_calls: int
    compression_ratio: float
    success_so_far: bool
    failure_category: Optional[str] = None


@dataclass
class TaskResult:
    task_id: str
    task_type: str
    mode: str
    keyframe_interval: int
    history_compression: str
    success: bool
    steps: int
    total_input_tokens: int
    total_output_tokens: int
    model_calls: int
    avg_latency_ms: float
    end_to_end_time_ms: float
    estimated_cost_usd: float
    compression_ratio: float
    agent_errors: int
    recovered_errors: int
    failure_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
