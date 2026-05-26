import os
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_alert(message):
    """Send alert message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured. Printing alert locally:")
        print(message)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    return response.status_code == 200


def alert_pod_crash(pod_name, status, restarts, ai_diagnosis):
    """Send alert when pod crashes"""
    message = f"""🚨 *POD CRASH DETECTED*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Pod: `{pod_name}`
📊 Status: {status}
🔄 Restarts: {restarts}

🤖 *AI Diagnosis:*
{ai_diagnosis}
"""
    return send_telegram_alert(message)


def alert_fix_applied(pod_name, action, result):
    """Send alert when auto-fix is applied"""
    message = f"""✅ *AUTO-FIX APPLIED*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Pod: `{pod_name}`
🔧 Action: {action}
📋 Result: {result}
"""
    return send_telegram_alert(message)


def alert_cluster_healthy():
    """Send daily health report"""
    message = f"""💚 *CLUSTER HEALTHY*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ All pods running normally
📊 No issues detected
"""
    return send_telegram_alert(message)


def alert_human_approval_needed(pod_name, suggested_fix):
    """Alert human that approval is needed"""
    message = f"""👤 *APPROVAL NEEDED*

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📦 Pod: `{pod_name}`
🤖 AI suggests: {suggested_fix}

Please SSH into server and approve/reject.
"""
    return send_telegram_alert(message)


if __name__ == "__main__":
    alert_cluster_healthy()
    print("Test alert sent!")
