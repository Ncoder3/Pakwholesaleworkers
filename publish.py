import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"


def run_publish_workflow():
    # Force UTF-8 encoding across subprocess calls
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    summary = {
        "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "success": False,
        "message": "",
        "error_details": "",
        "commit_hash": None,
    }

    try:
        # 1. Run catalog generator script using sys.executable
        gen_script = PROJECT_ROOT / "scripts" / "generate.py"
        print("Running catalog generator...")

        res_gen = subprocess.run(
            [sys.executable, str(gen_script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        output = res_gen.stdout + (res_gen.stderr or "")

        # Check if generate.py threw a validation error
        if res_gen.returncode != 0 or "VALIDATION PASSED" not in output:
            error_msg = "Validation failed during generation."
            if "VALIDATION FOUND" in output:
                error_msg = (
                    "Validation Error: " + output.split("=================")[-2].strip()
                )

            summary["message"] = "Catalog generation cancelled due to validation errors."
            summary["error_details"] = error_msg
            _save_log(summary)
            return False, summary["message"]

        # 2. Stage changes with Git
        print("Staging git changes...")
        subprocess.run(
            ["git", "add", "."], cwd=PROJECT_ROOT, check=True, env=env
        )

        # 3. Check for actual changes before committing
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        if not status.stdout.strip():
            summary["success"] = True
            summary["message"] = (
                "Catalog regenerated! No new file changes were detected to push."
            )
            _save_log(summary)
            return True, summary["message"]

        # 4. Git Commit with Timestamp
        commit_time = datetime.now().strftime("%b %d, %Y %I:%M %p")
        commit_msg = f"Catalog auto-update from Admin Dashboard ({commit_time})"
        
        print("Creating git commit...")
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=PROJECT_ROOT,
            check=True,
            env=env,
        )

        # Retrieve short commit hash
        hash_res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        commit_hash = hash_res.stdout.strip()
        summary["commit_hash"] = commit_hash

        # 5. Git Push to GitHub
        print("Pushing updates to GitHub...")
        subprocess.run(["git", "push"], cwd=PROJECT_ROOT, check=True, env=env)

        summary["success"] = True
        summary["message"] = (
            f"Successfully published to live site! Commit: [{commit_hash}]"
        )
        _save_log(summary)

        return True, summary["message"]

    except subprocess.CalledProcessError as e:
        err_output = e.stderr if hasattr(e, "stderr") and e.stderr else str(e)
        summary["success"] = False
        summary["message"] = "Publish workflow process failed."
        summary["error_details"] = err_output
        _save_log(summary)
        return False, f"Workflow failed: {err_output}"


def _save_log(log_data):
    """Saves output metadata for dashboard display."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        print(f"Failed to write log file: {e}")


if __name__ == "__main__":
    success, msg = run_publish_workflow()
    print(f"\nResult: {'Success' if success else 'Failed'}\nMessage: {msg}")