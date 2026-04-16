import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path


class AgentLogger:
    """
    Logs every agent step: prompt, action, result, screenshot path.
    Writes a JSON run report to logs/<run_id>/report.json
    """

    def __init__(self, task_name: str):
        self.task_name = task_name
        self.run_id = f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.run_dir = Path("logs") / self.run_id
        self.screenshots_dir = self.run_dir / "screenshots"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.steps = []
        self.start_time = time.time()

        print(f"\n[Logger] Run started: {self.run_id}")
        print(f"[Logger] Logs → {self.run_dir}\n")

    def log_step(self, step_num: int, action: str, result: str = "", url: str = ""):
        """Call after each agent action."""
        step = {
            "step": step_num,
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "action": action,
            "result": result,
            "screenshot": None,
        }
        self.steps.append(step)
        print(f"  [Step {step_num:02d}] {action[:80]}")
        return step

    def log_screenshot(self, step_num: int, image_bytes: bytes):
        """Save a screenshot for a given step."""
        filename = f"step_{step_num:02d}.png"
        path = self.screenshots_dir / filename
        path.write_bytes(image_bytes)

        # Update the matching step record
        for step in self.steps:
            if step["step"] == step_num:
                step["screenshot"] = str(path)
                break

        print(f"  [Step {step_num:02d}] Screenshot saved → {path}")
        return str(path)

    def finish(self, final_result: str = "", success: bool = True):
        """Write the full JSON report."""
        duration = round(time.time() - self.start_time, 2)
        report = {
            "run_id": self.run_id,
            "task": self.task_name,
            "success": success,
            "duration_seconds": duration,
            "total_steps": len(self.steps),
            "final_result": final_result,
            "steps": self.steps,
        }
        report_path = self.run_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2))

        print(f"\n[Logger] Run complete in {duration}s")
        print(f"[Logger] Report → {report_path}")
        print(f"[Logger] Screenshots → {self.screenshots_dir}")
        return report