from __future__ import annotations

from typing import List, Optional

from src.agents.baseline_agent import AgentRuntimeConfig, BaselineAgent
from src.agents.prompts import build_baseline_prompt, build_compressed_prompt
from src.compression.delta_encoder import DeltaEncoder
from src.compression.keyframe import KeyframeStore
from src.compression.token_counter import estimate_tokens
from src.utils.types import GUIAction, GUIDelta, TaskSpec


class CompressedAgent(BaselineAgent):
    def __init__(self, config: AgentRuntimeConfig, delta_mode: str) -> None:
        super().__init__(config)
        self.delta_mode = delta_mode

    def run_task(self, task: TaskSpec):
        self._keyframes = KeyframeStore(self.config.keyframe_interval)
        self._encoder = DeltaEncoder(self.delta_mode)
        return super().run_task(task)

    def _build_prompt(self, task: TaskSpec, step_id: int, actions: List[GUIAction]) -> str:
        obs = task.trajectory[step_id]
        self._keyframes.maybe_add(obs)
        latest = self._keyframes.latest
        if latest is None:
            raise RuntimeError("keyframe store did not initialize")
        deltas = self._deltas_since_keyframe(task, latest.step_id, step_id, latest.keyframe_id)
        return build_compressed_prompt(
            task.instruction,
            latest.observation,
            deltas,
            actions,
            self.delta_mode,
            self.config.history_compression,
        )

    def _error_probability(self, task: TaskSpec, step_id: int, ideal_action: GUIAction) -> float:
        difficulty = float(task.metadata.get("difficulty", 0.5))
        visual = float(task.metadata.get("visual_dependency", 0.5))
        age = step_id % max(1, self.config.keyframe_interval)
        age_penalty = 0.006 * age
        history_penalty = {
            "none": 0.0,
            "summary": 0.004,
            "action_only": 0.012,
            "state_summary": 0.008,
        }.get(self.config.history_compression, 0.01)
        if self.delta_mode == "pixel":
            base = 0.105 + 0.055 * difficulty + 0.08 * (1.0 - visual)
        elif self.delta_mode == "semantic":
            base = 0.04 + 0.03 * difficulty + 0.025 * visual
        else:
            base = 0.018 + 0.018 * difficulty + 0.012 * visual
        if ideal_action.type == "type":
            base += 0.008
        return min(0.5, base + age_penalty + history_penalty)

    def _failure_category(self, task: TaskSpec, step_id: int) -> str:
        age = step_id % max(1, self.config.keyframe_interval)
        draw = int(
            self.config.seed
            + step_id
            + len(task.task_id)
            + round(float(task.metadata.get("difficulty", 0.5)) * 100)
        )
        if self.delta_mode == "pixel":
            pool = ["missing visual detail", "bad delta reconstruction", "stale keyframe"]
        elif self.delta_mode == "semantic":
            pool = ["semantic parser error", "bad delta reconstruction", "wrong action prediction"]
        else:
            pool = ["stale keyframe", "bad delta reconstruction", "wrong action prediction"]
        if age >= 8:
            return "stale keyframe"
        return pool[draw % len(pool)]

    def _deltas_since_keyframe(
        self, task: TaskSpec, keyframe_step: int, current_step: int, keyframe_id: Optional[str]
    ) -> List[GUIDelta]:
        deltas: List[GUIDelta] = []
        for idx in range(keyframe_step + 1, current_step + 1):
            deltas.append(
                self._encoder.compute_delta(
                    task.trajectory[idx - 1],
                    task.trajectory[idx],
                    last_keyframe_id=keyframe_id,
                )
            )
        return deltas

    def _model_calls_for_action(self, ideal_action: GUIAction) -> int:
        if ideal_action.type == "wait":
            return 0
        return 1

    def _avg_ratio(self, records):
        if not records:
            return 1.0
        ratios = [record.compression_ratio for record in records if record.model_calls]
        return sum(ratios) / max(1, len(ratios))


class HybridCompressedAgent(CompressedAgent):
    def __init__(self, config: AgentRuntimeConfig) -> None:
        super().__init__(config, delta_mode="hybrid")


def make_agent(
    mode: str,
    keyframe_interval: int,
    history_compression: str,
    model: str,
    max_steps: int,
    input_cost_per_1m: float,
    output_cost_per_1m: float,
    seed: int,
) -> BaselineAgent:
    config = AgentRuntimeConfig(
        mode=mode,
        keyframe_interval=keyframe_interval,
        history_compression=history_compression,
        model=model,
        max_steps=max_steps,
        input_cost_per_1m=input_cost_per_1m,
        output_cost_per_1m=output_cost_per_1m,
        seed=seed,
    )
    if mode == "pixel_delta":
        return CompressedAgent(config, "pixel")
    if mode == "semantic_delta":
        return CompressedAgent(config, "semantic")
    if mode == "hybrid":
        return HybridCompressedAgent(config)
    return BaselineAgent(config)
