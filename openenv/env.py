from __future__ import annotations

import random
from typing import Any

from pydantic import BaseModel, Field

from .graders import grade_action
from .tasks_wrapper import TaskWrapper


class Observation(BaseModel):
    task_id: str
    difficulty: str
    prompt: str
    expected_schema: dict[str, Any]
    attempt: int = 0
    remaining_attempts: int = 0
    feedback: str = ""


class Action(BaseModel):
    response: str = Field(default="")


class Reward(BaseModel):
    score: float
    correctness: float
    relevance: float
    clarity: float
    progress: float = 0.0
    penalty: float = 0.0


class JobifyEnv:
    def __init__(self, seed: int | None = None, max_attempts: int = 2):
        self._rng = random.Random(seed)
        self._tasks = {task["task_id"]: task for task in TaskWrapper.get_tasks()}
        self.max_attempts = max_attempts
        self.current_task: dict[str, Any] | None = None
        self.last_reward: Reward | None = None
        self.attempt_count = 0
        self.action_history: list[str] = []

    def _build_observation(self, prompt: str, feedback: str = "") -> Observation:
        if self.current_task is None:
            raise RuntimeError("Environment has no active task.")
        return Observation(
            task_id=self.current_task["task_id"],
            difficulty=self.current_task["difficulty"],
            prompt=prompt,
            expected_schema=self.current_task["expected_output"],
            attempt=self.attempt_count,
            remaining_attempts=max(0, self.max_attempts - self.attempt_count),
            feedback=feedback,
        )

    def _set_current_task(self, task_id: str) -> Observation:
        self.current_task = self._tasks[task_id]
        self.last_reward = None
        self.attempt_count = 0
        self.action_history = []
        return self._build_observation(self.current_task["observation"])

    def reset(self) -> Observation:
        task_id = self._rng.choice(list(self._tasks.keys()))
        return self._set_current_task(task_id)

    def load_task(self, task_id: str) -> Observation:
        return self._set_current_task(task_id)

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        if self.current_task is None:
            raise RuntimeError("Environment has no active task. Call reset() first.")

        self.attempt_count += 1
        normalized_response = action.response.strip()
        loop_penalty = 0.0
        if not normalized_response:
            loop_penalty += 0.2
        if self.action_history and normalized_response == self.action_history[-1]:
            loop_penalty += 0.15
        self.action_history.append(normalized_response)

        grading = grade_action(
            task_id=self.current_task["task_id"],
            model_output=action.response,
            expected_output=self.current_task["expected_output"],
            observation_text=self.current_task["observation"],
        )
        total_penalty = min(1.0, grading["penalty"] + loop_penalty)
        base_score = max(0.0, grading["score"] - loop_penalty)
        progress = min(1.0, base_score + (0.1 * max(0, self.attempt_count - 1)))
        reward = Reward(
            score=base_score,
            correctness=grading["correctness"],
            relevance=grading["relevance"],
            clarity=grading["clarity"],
            progress=progress,
            penalty=total_penalty,
        )
        self.last_reward = reward
        reached_quality_bar = base_score >= 0.8
        done = reached_quality_bar or self.attempt_count >= self.max_attempts
        feedback = (
            f"Previous score: {reward.score:.4f}. "
            f"Correctness={reward.correctness:.4f}, Relevance={reward.relevance:.4f}, "
            f"Clarity={reward.clarity:.4f}, Penalty={reward.penalty:.4f}. "
            "Improve formatting, include missing expected fields, and keep JSON exact."
        )
        next_prompt = (
            "Task complete."
            if done
            else f"{self.current_task['observation']}\n\nRevision Feedback:\n{feedback}"
        )
        next_observation = self._build_observation(next_prompt, feedback if not done else "")
        info = {
            "task_id": self.current_task["task_id"],
            "title": self.current_task["title"],
            "metadata": self.current_task["metadata"],
            "penalty": total_penalty,
            "attempt_count": self.attempt_count,
            "reached_quality_bar": reached_quality_bar,
        }
        return next_observation, reward, done, info

    def state(self) -> dict[str, Any]:
        return {
            "current_task": self.current_task,
            "last_reward": None if self.last_reward is None else self.last_reward.model_dump(),
            "available_tasks": list(self._tasks.keys()),
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "action_history": self.action_history,
        }
