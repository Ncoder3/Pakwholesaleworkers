# import json
# import os
# from pathlib import Path
# import subprocess
# import sys
# from datetime import datetime

# PROJECT_ROOT = Path(__file__).resolve().parent
# LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"


# def run_publish_workflow():
#     # Force UTF-8 encoding across subprocess calls
#     env = os.environ.copy()
#     env["PYTHONIOENCODING"] = "utf-8"

#     summary = {
#         "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p"),
#         "success": False,
#         "message": "",
#         "error_details": "",
#         "commit_hash": None,
#     }

#     try:
#         # 1. Run catalog generator script using sys.executable
#         gen_script = PROJECT_ROOT / "scripts" / "generate.py"
#         print("Running catalog generator...")

#         res_gen = subprocess.run(
#             [sys.executable, str(gen_script)],
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             env=env,
#         )

#         output = res_gen.stdout + (res_gen.stderr or "")

#         print("========== GENERATOR OUTPUT ==========")
#         print(output)
#         print("========== END GENERATOR OUTPUT ==========")

#         # Check if generate.py threw a validation error
#         if res_gen.returncode != 0 or "VALIDATION PASSED" not in output:
#             error_msg = "Validation failed during generation."
#             if "VALIDATION FOUND" in output:
#                 error_msg = (
#                     "Validation Error: " + output.split("=================")[-2].strip()
#                 )

#             summary["message"] = "Catalog generation cancelled due to validation errors."
#             summary["error_details"] = error_msg
#             _save_log(summary)
#             return False, summary["message"]

#         # 2. Stage changes with Git
#         print("Staging git changes...")
#         subprocess.run(
#             ["git", "add", "."], cwd=PROJECT_ROOT, check=True, env=env
#         )

#         # 3. Check for actual changes before committing
#         status = subprocess.run(
#             ["git", "status", "--porcelain"],
#             cwd=PROJECT_ROOT,
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             env=env,
#         )

#         if not status.stdout.strip():
#             summary["success"] = True
#             summary["message"] = (
#                 "Catalog regenerated! No new file changes were detected to push."
#             )
#             _save_log(summary)
#             return True, summary["message"]

#         # 4. Git Commit with Timestamp
#         commit_time = datetime.now().strftime("%b %d, %Y %I:%M %p")
#         commit_msg = f"Catalog auto-update from Admin Dashboard ({commit_time})"
        
#         print("Creating git commit...")
#         subprocess.run(
#             ["git", "commit", "-m", commit_msg],
#             cwd=PROJECT_ROOT,
#             check=True,
#             env=env,
#         )

#         # Retrieve short commit hash
#         hash_res = subprocess.run(
#             ["git", "rev-parse", "--short", "HEAD"],
#             cwd=PROJECT_ROOT,
#             capture_output=True,
#             text=True,
#             encoding="utf-8",
#             env=env,
#         )
#         commit_hash = hash_res.stdout.strip()
#         summary["commit_hash"] = commit_hash

#         # 5. Git Push to GitHub
#         print("Pushing updates to GitHub...")
#         subprocess.run(["git", "push"], cwd=PROJECT_ROOT, check=True, env=env)

#         summary["success"] = True
#         summary["message"] = (
#             f"Successfully published to live site! Commit: [{commit_hash}]"
#         )
#         _save_log(summary)

#         return True, summary["message"]

#     except subprocess.CalledProcessError as e:
#         err_output = e.stderr if hasattr(e, "stderr") and e.stderr else str(e)
#         summary["success"] = False
#         summary["message"] = "Publish workflow process failed."
#         summary["error_details"] = err_output
#         _save_log(summary)
#         return False, f"Workflow failed: {err_output}"


# def _save_log(log_data):
#     """Saves output metadata for dashboard display."""
#     try:
#         LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
#         with open(LOG_FILE, "w", encoding="utf-8") as f:
#             json.dump(log_data, f, indent=2)
#     except Exception as e:
#         print(f"Failed to write log file: {e}")


# if __name__ == "__main__":
#     success, msg = run_publish_workflow()
#     print(f"\nResult: {'Success' if success else 'Failed'}\nMessage: {msg}")

#above all code was the for excel
#below is for postgree
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import urllib.request
import urllib.error


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"


GITHUB_API_URL = (
    "https://api.github.com/repos/"
    "Ncoder3/Pakwholesaleworkers/dispatches"
)

GITHUB_TOKEN = os.environ.get(
    "GITHUB_TOKEN"
)


def run_publish_workflow():

    summary = {
        "timestamp": datetime.now().strftime(
            "%b %d, %Y %I:%M %p"
        ),
        "success": False,
        "message": "",
        "error_details": "",
        "commit_hash": None,
    }

    try:

        # =====================================================
        # 1. Validate environment
        # =====================================================

        if not GITHUB_TOKEN:

            summary["message"] = (
                "GITHUB_TOKEN is not configured in Railway."
            )

            summary["error_details"] = (
                "Add a GitHub token to Railway Variables."
            )

            _save_log(summary)

            return False, summary["message"]

        # =====================================================
        # 2. Trigger GitHub Actions
        # =====================================================

        print(
            "Triggering GitHub Actions remote publish..."
        )

        payload = json.dumps({
            "event_type": "remote_publish_trigger",
            "client_payload": {
                "source": "railway-admin",
                "timestamp": datetime.now().isoformat(),
            }
        }).encode("utf-8")

        request = urllib.request.Request(
            GITHUB_API_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization":
                    f"Bearer {GITHUB_TOKEN}",

                "Accept":
                    "application/vnd.github+json",

                "X-GitHub-Api-Version":
                    "2022-11-28",

                "Content-Type":
                    "application/json",

                "User-Agent":
                    "AlBaraka-Traders-Railway"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                status_code = response.status

        except urllib.error.HTTPError as e:

            error_body = e.read().decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                f"GitHub API error "
                f"{e.code}: {error_body}"
            )

        if status_code != 204:

            raise RuntimeError(
                f"GitHub returned HTTP {status_code}"
            )

        # =====================================================
        # 3. Success
        # =====================================================

        summary["success"] = True

        summary["message"] = (
            "Publish workflow successfully "
            "triggered on GitHub Actions."
        )

        _save_log(summary)

        print(
            "✓ GitHub Actions publish triggered."
        )

        return True, summary["message"]

    except Exception as e:

        summary["success"] = False

        summary["message"] = (
            "Failed to trigger GitHub Actions."
        )

        summary["error_details"] = str(e)

        _save_log(summary)

        print(
            f"[PUBLISH ERROR] {e}"
        )

        return False, summary["message"]


def _save_log(log_data):

    try:

        LOG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            LOG_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                log_data,
                f,
                indent=2
            )

    except Exception as e:

        print(
            f"Failed to write log file: {e}"
        )


if __name__ == "__main__":

    success, msg = run_publish_workflow()

    print(
        f"\nResult: "
        f"{'Success' if success else 'Failed'}"
    )

    print(
        f"Message: {msg}"
    )