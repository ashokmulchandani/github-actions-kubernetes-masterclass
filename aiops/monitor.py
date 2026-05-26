import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from log_reader import get_cluster_summary, get_crashed_pods, get_pod_logs
from ai_analyzer import analyze_pod_error
from auto_fix import auto_remediate, auto_remediate_with_approval
from alerter import send_telegram_alert, alert_pod_crash, alert_fix_applied, alert_cluster_healthy

# Configuration
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))  # seconds
AUTO_FIX_MODE = os.getenv("AUTO_FIX_MODE", "alert_only")  # alert_only | auto | approval
NAMESPACE = os.getenv("NAMESPACE", "skillpulse")


def monitor_once():
    """Run one monitoring check"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] 🔍 Checking cluster health...")

    crashed = get_crashed_pods(NAMESPACE)

    if not crashed:
        print(f"[{timestamp}] ✅ All pods healthy")
        return {"status": "healthy", "problems": 0}

    print(f"[{timestamp}] ⚠️ Found {len(crashed)} problem pod(s)")

    for pod in crashed:
        print(f"  └── {pod['name']}: {pod['status']} (restarts: {pod['restarts']})")

        # Get AI diagnosis
        diagnosis = analyze_pod_error(pod["name"], NAMESPACE)

        # Send Telegram alert
        alert_pod_crash(pod["name"], pod["status"], pod["restarts"], diagnosis)

        # Take action based on mode
        if AUTO_FIX_MODE == "auto":
            print(f"  └── 🤖 Auto-fix mode: attempting fix...")
            results = auto_remediate()
            for r in results:
                alert_fix_applied(r["pod"], r["action"], r.get("result", ""))

        elif AUTO_FIX_MODE == "approval":
            print(f"  └── 👤 Approval mode: waiting for human...")
            from alerter import alert_human_approval_needed
            alert_human_approval_needed(pod["name"], diagnosis)

        else:
            print(f"  └── 📢 Alert-only mode: notification sent")

    return {"status": "problems_found", "problems": len(crashed)}


def run_monitor():
    """Run continuous monitoring loop"""
    print("=" * 50)
    print("🤖 AIOps Continuous Monitor")
    print("=" * 50)
    print(f"  Namespace:      {NAMESPACE}")
    print(f"  Check interval: {CHECK_INTERVAL}s")
    print(f"  Fix mode:       {AUTO_FIX_MODE}")
    print("=" * 50)
    print("Press Ctrl+C to stop\n")

    # Send startup alert
    send_telegram_alert(f"🟢 *AIOps Monitor Started*\n\nNamespace: `{NAMESPACE}`\nMode: {AUTO_FIX_MODE}\nInterval: {CHECK_INTERVAL}s")

    checks = 0
    problems_found = 0

    try:
        while True:
            result = monitor_once()
            checks += 1

            if result["status"] != "healthy":
                problems_found += result["problems"]

            # Send daily health report every 100 checks
            if checks % 100 == 0:
                alert_cluster_healthy()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 50}")
        print("🛑 Monitor stopped")
        print(f"  Total checks: {checks}")
        print(f"  Problems found: {problems_found}")
        print(f"{'=' * 50}")

        send_telegram_alert(f"🔴 *AIOps Monitor Stopped*\n\nTotal checks: {checks}\nProblems found: {problems_found}")


if __name__ == "__main__":
    run_monitor()
