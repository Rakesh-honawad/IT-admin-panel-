import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from browser_use import Agent, BrowserConfig, Browser
from browser_use.agent.views import AgentHistoryList
from agent.logger import AgentLogger

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

def get_browser() -> Browser:
    return Browser(
        config=BrowserConfig(
            headless=False,
            extra_chromium_args=[
                "--window-size=1280,800",
                "--window-position=0,0",
            ],
        )
    )


def get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.0,
    )


async def run_task(task_prompt: str, task_name: str = "task", max_steps: int = 30) -> dict:
    logger = AgentLogger(task_name=task_name)
    browser = get_browser()
    llm = get_llm()

    agent = Agent(
    task=task_prompt,
    llm=llm,
    browser=browser,
    max_actions_per_step=5,
    use_vision=False,
)

    success = False
    final_result = ""

    try:
        history: AgentHistoryList = await agent.run(max_steps=max_steps)

        for i, item in enumerate(history.history):
            action_str = str(item.model_output)[:120] if item.model_output else "—"
            result_str = str(item.result)[:120] if item.result else "—"
            url = item.state.url if item.state else ""

            logger.log_step(
                step_num=i + 1,
                action=action_str,
                result=result_str,
                url=url,
            )

            if item.state and item.state.screenshot:
                import base64
                img_bytes = base64.b64decode(item.state.screenshot)
                logger.log_screenshot(i + 1, img_bytes)

        final_result = history.final_result() or "No final result"
        success = True

    except Exception as e:
        final_result = f"Error: {e}"
        logger.log_step(step_num=len(logger.steps) + 1, action="EXCEPTION", result=str(e))

    finally:
        await browser.close()

    report = logger.finish(final_result=final_result, success=success)
    return report


if __name__ == "__main__":
    test_task = (
        f"Go to {BASE_URL}/users. "
        "Tell me how many users are in the table."
    )
    report = asyncio.run(run_task(test_task, task_name="smoke_test", max_steps=5))
    print(f"\nFinal result: {report['final_result']}")