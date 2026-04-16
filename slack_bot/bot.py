import os
import asyncio
import threading
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

# Import agent pieces
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.loop import run_task
from agent.tasks import task_onboard_user, task_security_lockdown

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)


def parse_command(text: str) -> dict | None:
    """
    Parses /ittask command text into a task dict.

    Supported formats:
      onboard Jane Smith jane.smith@company.com Engineer
      lockdown "Bob Martinez" 2
    """
    parts = text.strip().split()
    if not parts:
        return None

    cmd = parts[0].lower()

    if cmd == "onboard" and len(parts) >= 3:
        # Last part is email, second-to-last could be role (optional)
        # Format: onboard FirstName LastName email@co.com [Role]
        email = parts[-1]
        role = parts[-2] if len(parts) >= 4 and "@" not in parts[-2] else "Engineer"
        name_parts = parts[1:-1] if role == "Engineer" else parts[1:-2]
        name = " ".join(name_parts)
        return {"type": "onboard", "name": name, "email": email, "role": role}

    if cmd == "lockdown" and len(parts) >= 2:
        # Format: lockdown "Bob Martinez" 2
        # Try to extract user_id as last token if it's a number
        if parts[-1].isdigit():
            user_id = int(parts[-1])
            name = " ".join(parts[1:-1])
        else:
            user_id = 0
            name = " ".join(parts[1:])
        return {"type": "lockdown", "name": name, "user_id": user_id}

    return None


def run_agent_in_thread(task_prompt: str, task_name: str, say, channel: str):
    """
    Runs the async agent in a background thread so Slack's
    3-second ack deadline isn't violated.
    """
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report = loop.run_until_complete(
                run_task(task_prompt, task_name=task_name, max_steps=30)
            )
            status = "✅ Success" if report["success"] else "❌ Failed"
            msg = (
                f"{status} — *{task_name}*\n"
                f"Steps: {report['total_steps']} | "
                f"Duration: {report['duration_seconds']}s\n"
                f"Result: {report['final_result']}"
            )
            say(text=msg, channel=channel)
        except Exception as e:
            say(text=f"❌ Agent error: {e}", channel=channel)
        finally:
            loop.close()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


@app.command("/ittask")
def handle_ittask(ack, say, command):
    """
    Handles /ittask slash command.
    Examples:
      /ittask onboard Jane Smith jane.smith@company.com Engineer
      /ittask lockdown Bob Martinez 2
      /ittask help
    """
    ack()  # Must ack within 3 seconds

    text = command.get("text", "").strip()
    channel = command["channel_id"]
    user = command["user_name"]

    if not text or text.lower() == "help":
        say(
            text=(
                "*IT Admin Agent* — available commands:\n"
                "• `/ittask onboard [Full Name] [email] [Role]` — create user + assign license\n"
                "• `/ittask lockdown [Full Name] [user_id]` — revoke sessions + reset MFA\n\n"
                "_Example:_ `/ittask onboard Jane Smith jane@co.com Engineer`"
            ),
            channel=channel,
        )
        return

    parsed = parse_command(text)

    if not parsed:
        say(
            text=f"❓ Couldn't parse `{text}`. Try `/ittask help`.",
            channel=channel,
        )
        return

    if parsed["type"] == "onboard":
        say(
            text=(
                f"🤖 Agent starting... triggered by @{user}\n"
                f"Task: Onboard *{parsed['name']}* (`{parsed['email']}`)"
            ),
            channel=channel,
        )
        prompt = task_onboard_user(
            name=parsed["name"],
            email=parsed["email"],
            role=parsed.get("role", "Engineer"),
        )
        run_agent_in_thread(prompt, "task1_onboard", say, channel)

    elif parsed["type"] == "lockdown":
        say(
            text=(
                f"🤖 Agent starting... triggered by @{user}\n"
                f"Task: Security lockdown for *{parsed['name']}*"
            ),
            channel=channel,
        )
        prompt = task_security_lockdown(
            target_name=parsed["name"],
            target_user_id=parsed["user_id"],
        )
        run_agent_in_thread(prompt, "task2_lockdown", say, channel)


if __name__ == "__main__":
    print("Starting IT Admin Slack Bot...")
    handler = SocketModeHandler(
        app,
        app_token=os.getenv("SLACK_APP_TOKEN"),
    )
    handler.start()