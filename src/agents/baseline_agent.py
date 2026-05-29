from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.agents.prompts import build_baseline_prompt, build_last_screenshot_prompt
from src.compression.token_counter import estimate_cost_usd, estimate_tokens
from src.utils.types import AgentDecision, GUIAction, StepRecord, TaskResult, TaskSpec


FAILURE_CATEGORIES = [
    "missing visual detail",
    "bad delta reconstruction",
    "wrong action prediction",
    "stale keyframe",
    "semantic parser error",
    "task ambiguity",
]


@dataclass
class AgentRuntimeConfig:
    mode: str = "full_context"
    keyframe_interval: int = 1
    history_compression: str = "none"
    model: str = "gpt-5.5"
    max_steps: int = 30
    input_cost_per_1m: float = 1.25
    output_cost_per_1m: float = 10.0
    seed: int = 13


def stable_uniform(*parts: object) -> float:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12)


def simulated_latency_ms(input_tokens: int, output_tokens: int, mode: str, task_id: str, step_id: int) -> float:
    jitter = stable_uniform("latency", mode, task_id, step_id) * 40.0
    return 180.0 + (0.085 * input_tokens) + (0.18 * output_tokens) + jitter


def strict_json_output(action: GUIAction, success: bool) -> dict:
    return {
        "reasoning_summary": "Select the next UI action based on the current task state.",
        "action": action.to_dict(),
        "confidence": 0.86 if success else 0.38,
    }


class BaselineAgent:
    def __init__(self, config: AgentRuntimeConfig) -> None:
        self.config = config

    def run_task(self, task: TaskSpec) -> Tuple[TaskResult, List[StepRecord]]:
        started = time.perf_counter()
        actions: List[GUIAction] = []
        step_records: List[StepRecord] = []
        total_input = 0
        total_output = 0
        total_latency = 0.0
        total_calls = 0
        errors = 0
        recovered = 0
        failure_category: Optional[str] = None
        success = True
        step_count = min(len(task.trajectory), len(task.ideal_actions), self.config.max_steps)

        for step_id in range(step_count):
            obs = task.trajectory[step_id]
            ideal_action = task.ideal_actions[step_id]
            model_calls = self._model_calls_for_action(ideal_action)
            prompt = self._build_prompt(task, step_id, actions)
            baseline_tokens = estimate_tokens(
                build_baseline_prompt(
                    task.instruction,
                    obs,
                    task.trajectory[: step_id + 1],
                    actions,
                    "none",
                )
            )
            prompt_tokens = estimate_tokens(prompt) if model_calls else 0
            is_correct, category, was_recovered = self._simulate_correctness(task, step_id, ideal_action)
            if not is_correct:
                errors += 1
                failure_category = category
                if was_recovered:
                    recovered += 1
                else:
                    success = False
            emitted_action = ideal_action if is_correct or was_recovered else GUIAction(type="wait", target="uncertain")
            output_payload = strict_json_output(emitted_action, is_correct or was_recovered)
            output_tokens = estimate_tokens(output_payload) if model_calls else 0
            latency = simulated_latency_ms(prompt_tokens, output_tokens, self.config.mode, task.task_id, step_id)
            if not model_calls:
                latency = 20.0

            actions.append(emitted_action)
            total_input += prompt_tokens
            total_output += output_tokens
            total_latency += latency
            total_calls += model_calls
            compression_ratio = baseline_tokens / max(1, prompt_tokens) if model_calls else float(baseline_tokens)
            step_records.append(
                StepRecord(
                    task_id=task.task_id,
                    mode=self.config.mode,
                    keyframe_interval=self.config.keyframe_interval,
                    step_id=step_id,
                    input_tokens=prompt_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency,
                    model_calls=model_calls,
                    compression_ratio=compression_ratio,
                    success_so_far=success,
                    failure_category=failure_category,
                )
            )
            if not success:
                break

        end_to_end = (time.perf_counter() - started) * 1000.0
        result = TaskResult(
            task_id=task.task_id,
            task_type=task.task_type,
            mode=self.config.mode,
            keyframe_interval=self.config.keyframe_interval,
            history_compression=self.config.history_compression,
            success=success,
            steps=len(step_records),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            model_calls=total_calls,
            avg_latency_ms=total_latency / max(1, len(step_records)),
            end_to_end_time_ms=max(end_to_end, total_latency),
            estimated_cost_usd=estimate_cost_usd(
                total_input,
                total_output,
                self.config.input_cost_per_1m,
                self.config.output_cost_per_1m,
            ),
            compression_ratio=1.0 if self.config.mode == "full_context" else self._avg_ratio(step_records),
            agent_errors=errors,
            recovered_errors=recovered,
            failure_category=None if success else failure_category,
        )
        return result, step_records

    def _build_prompt(self, task: TaskSpec, step_id: int, actions: List[GUIAction]) -> str:
        obs = task.trajectory[step_id]
        if self.config.mode == "last_screenshot":
            return build_last_screenshot_prompt(task.instruction, obs, actions)
        return build_baseline_prompt(
            task.instruction,
            obs,
            task.trajectory[: step_id + 1],
            actions,
            self.config.history_compression,
        )

    def _model_calls_for_action(self, ideal_action: GUIAction) -> int:
        if self.config.mode != "full_context" and ideal_action.type == "wait":
            return 0
        return 1

    def _simulate_correctness(
        self, task: TaskSpec, step_id: int, ideal_action: GUIAction
    ) -> tuple[bool, Optional[str], bool]:
        p_error = self._error_probability(task, step_id, ideal_action)
        draw = stable_uniform(self.config.seed, self.config.mode, task.task_id, step_id, "error")
        if draw >= p_error:
            return True, None, False
        category = self._failure_category(task, step_id)
        recovery_p = 0.82 if self.config.mode == "full_context" else 0.66
        recovered = stable_uniform(self.config.seed, self.config.mode, task.task_id, step_id, "recover") < recovery_p
        return False, category, recovered

    def _error_probability(self, task: TaskSpec, step_id: int, ideal_action: GUIAction) -> float:
        difficulty = float(task.metadata.get("difficulty", 0.5))
        visual = float(task.metadata.get("visual_dependency", 0.5))
        if self.config.mode == "full_context":
            base = 0.018
        elif self.config.mode == "full_dom":
            base = 0.03 + 0.02 * visual
        elif self.config.mode == "summary_history":
            base = 0.05 + 0.03 * difficulty
        elif self.config.mode == "last_screenshot":
            base = 0.075 + 0.035 * difficulty
        else:
            base = 0.04
        if ideal_action.type == "type":
            base += 0.01
        return min(0.45, base)

    def _failure_category(self, task: TaskSpec, step_id: int) -> str:
        index = int(stable_uniform(self.config.seed, self.config.mode, task.task_id, step_id, "category") * 10_000)
        if self.config.mode == "last_screenshot":
            pool = ["missing visual detail", "wrong action prediction", "task ambiguity"]
        elif self.config.mode == "summary_history":
            pool = ["wrong action prediction", "task ambiguity", "missing visual detail"]
        else:
            pool = ["wrong action prediction", "task ambiguity"]
        return pool[index % len(pool)]

    @staticmethod
    def _avg_ratio(records: List[StepRecord]) -> float:
        if not records:
            return 1.0
        return sum(record.compression_ratio for record in records) / len(records)
