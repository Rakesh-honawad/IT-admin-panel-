import asyncio
import sys
import os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agent.loop import run_task
from agent.tasks import task_security_lockdown


async def main():
    print("=" * 50)
    print("TASK 2: Security Lockdown")
    print("=" * 50)

    # Bob Martinez exists from seed data
    prompt = task_security_lockdown(
        target_name="Bob Martinez",
        target_user_id=2,
    )

    print("\nRunning agent...\n")

    report = await run_task(
        prompt,
        task_name="task2_lockdown",
        max_steps=20
    )

    print("\n=== RESULT ===")
    print(f"Final: {report['final_result']}")
    print(f"Steps: {report['total_steps']}")
    print(f"Duration: {report['duration_seconds']}s")


if __name__ == "__main__":
    asyncio.run(main())