from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import APIConnectionError, AuthenticationError, OpenAI

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
        base_url=os.getenv("API_BASE_URL", "https://router.huggingface.co/v1"),
    )


def _print_env_help() -> None:
    print("Required environment variables:")
    print("  HF_TOKEN=<your_huggingface_token>")
    print("Optional environment variables:")
    print("  API_BASE_URL=https://router.huggingface.co/v1")
    print("  MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct")
    print("  LOCAL_IMAGE_NAME=<optional local docker image name>")


def run_inference() -> float:
    client = _build_client()
    env = JobifyEnv(seed=7, max_attempts=2)
    total_reward = 0.0
    task_ids = ["skill_extraction", "job_matching", "resume_optimization"]
    model_name = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
    print(f"START model={model_name} tasks={len(task_ids)}")

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

            print(
                f"STEP task={task_id} attempt={info['attempt_count']} "
                f"reward={reward.score:.4f} done={done}"
            )

        total_reward += final_reward
        print(
            f"STEP task={task_id} final_reward={final_reward:.4f} "
            f"attempt_rewards={[round(score, 4) for score in attempt_rewards]}"
        )

    final_score = total_reward / len(task_ids)
    print(f"END baseline_score={final_score:.4f}")
    return final_score


if __name__ == "__main__":
    try:
        run_inference()
    except RuntimeError as exc:
        print(f"Configuration error: {exc}")
        _print_env_help()
        raise SystemExit(1)
    except AuthenticationError:
        print("Authentication error: HF_TOKEN was rejected by the provider.")
        print("Check that your Hugging Face token is valid and has inference access.")
        _print_env_help()
        raise SystemExit(1)
    except APIConnectionError:
        print("Connection error: unable to reach the configured inference provider.")
        print("Check your internet connection, firewall, proxy, or the API_BASE_URL value.")
        print(f"Current API_BASE_URL: {os.getenv('API_BASE_URL', 'https://router.huggingface.co/v1')}")
        _print_env_help()
        raise SystemExit(1)
