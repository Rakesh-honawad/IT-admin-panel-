import asyncio
import sys
import os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agent.loop import run_task
from agent.tasks import task_onboard_user


async def main():
    print("=" * 50)
    print("TASK 1: Conditional User Onboarding")
    print("=" * 50)

    prompt = task_onboard_user(
        name="Jane Smith",
        email="jane.smith@company.com",
        role="Engineer",
        product="GitHub Enterprise",
    )

    print("\nRunning agent...\n")

    report = await run_task(
        prompt,
        task_name="task1_onboard",
        max_steps=30
    )

    print("\n=== RESULT ===")
    print(f"Final: {report['final_result']}")
    print(f"Steps: {report['total_steps']}")
    print(f"Duration: {report['duration_seconds']}s")


if __name__ == "__main__":
    asyncio.run(main())