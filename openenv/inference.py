from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from openenv.env import Action, JobifyEnv


SYSTEM_PROMPT = (
    "You are completing Jobify hiring evaluation tasks. "
    "Return concise JSON only. "
    "Do not wrap the answer in markdown fences. "
    "Use the exact field names requested in the prompt. "
    "Revise your answer when feedback is provided."
)


def _build_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("HF_TOKEN", "").strip()
    if not api_key:
        raise RuntimeError("HF_TOKEN is not set in the environment or .env file.")
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://router.huggingface.co/v1"),
    )


def run_inference() -> float:
    client = _build_client()
    env = JobifyEnv(seed=7, max_attempts=2)
    total_reward = 0.0
    task_ids = ["skill_extraction", "job_matching", "resume_optimization"]
    model_name = os.getenv("OPENAI_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

    for task_id in task_ids:
        observation = env.load_task(task_id)
        done = False
        final_reward = 0.0
        attempt_rewards: list[float] = []
        response_text = ""

        while not done:
            completion = client.chat.completions.create(
                model=model_name,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": observation.prompt},
                ],
            )
            response_text = completion.choices[0].message.content or ""
            observation, reward, done, info = env.step(Action(response=response_text))
            attempt_rewards.append(reward.score)
            final_reward = reward.score

        total_reward += final_reward
        print(f"Task: {task_id}")
        print(response_text.strip())
        print(f"Attempt Rewards: {[round(score, 4) for score in attempt_rewards]}")
        print(f"Final Reward: {final_reward:.4f}")
        print(f"Info: {info}")
        print("-" * 60)

    final_score = total_reward / len(task_ids)
    print(f"Baseline Score: {final_score:.4f}")
    return final_score


if __name__ == "__main__":
    run_inference()
