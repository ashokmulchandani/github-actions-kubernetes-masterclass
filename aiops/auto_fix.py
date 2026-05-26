import subprocess
import json
from log_reader import get_crashed_pods, get_pod_logs
from ai_analyzer import client, DEPLOYMENT_NAME


def restart_pod(pod_name, namespace="skillpulse"):
    """Restart a crashed pod by deleting it (K8s auto-recreates)"""
    result = subprocess.run(
        ["kubectl", "delete", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return f"Restarted pod: {pod_name}" if result.returncode == 0 else f"Failed: {result.stderr}"


def scale_deployment(deployment, replicas, namespace="skillpulse"):
    """Scale a deployment up or down"""
    result = subprocess.run(
        ["kubectl", "scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace],
        capture_output=True, text=True
    )
    return f"Scaled {deployment} to {replicas} replicas" if result.returncode == 0 else f"Failed: {result.stderr}"


def get_ai_fix_action(pod_name, namespace="skillpulse"):
    """Ask AI what action to take for a broken pod"""
    logs = get_pod_logs(pod_name, namespace)

    prompt = f"""A Kubernetes pod is failing. Based on the logs, respond with ONLY a JSON object.
Choose ONE action:

{{"action": "restart", "pod": "<pod_name>", "reason": "<why>"}}
{{"action": "scale", "deployment": "<name>", "replicas": <number>, "reason": "<why>"}}
{{"action": "none", "reason": "<why no action needed>"}}

Pod: {pod_name}
Logs:
{logs[-2000:]}"""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a DevOps auto-remediation bot. Respond ONLY with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"action": "none", "reason": "Could not parse AI response"}

def auto_remediate_with_approval():
    """Find problems, suggest fixes, wait for human approval"""
    crashed = get_crashed_pods()

    if not crashed:
        print("✅ All pods healthy. Nothing to fix.")
        return []

    actions_taken = []
    for pod in crashed:
        print(f"\n🔍 Analyzing: {pod['name']} (status: {pod['status']}, restarts: {pod['restarts']})")

        fix = get_ai_fix_action(pod["name"])
        print(f"\n🤖 AI suggests: {json.dumps(fix, indent=2)}")

        # HUMAN APPROVAL
        print("\n" + "-" * 40)
        approval = input("👤 Apply this fix? (yes/no/skip): ").strip().lower()

        if approval == "yes":
            if fix["action"] == "restart":
                result = restart_pod(fix["pod"])
                print(f"✅ {result}")
                actions_taken.append({"pod": pod["name"], "action": "restart", "result": result})
            elif fix["action"] == "scale":
                result = scale_deployment(fix["deployment"], fix["replicas"])
                print(f"✅ {result}")
                actions_taken.append({"pod": pod["name"], "action": "scale", "result": result})
        elif approval == "skip":
            print("⏭️ Skipped")
            continue
        else:
            print("❌ Rejected by human")
            actions_taken.append({"pod": pod["name"], "action": "rejected", "reason": "Human rejected"})

    return actions_taken

def auto_remediate():
    """Find problems and auto-fix them"""
    crashed = get_crashed_pods()

    if not crashed:
        print("✅ All pods healthy. Nothing to fix.")
        return []

    actions_taken = []
    for pod in crashed:
        print(f"\n🔍 Analyzing: {pod['name']} (status: {pod['status']}, restarts: {pod['restarts']})")

        fix = get_ai_fix_action(pod["name"])
        print(f"🤖 AI suggests: {fix}")

        if fix["action"] == "restart":
            result = restart_pod(fix["pod"])
            print(f"✅ {result}")
            actions_taken.append({"pod": pod["name"], "action": "restart", "result": result})

        elif fix["action"] == "scale":
            result = scale_deployment(fix["deployment"], fix["replicas"])
            print(f"✅ {result}")
            actions_taken.append({"pod": pod["name"], "action": "scale", "result": result})

        else:
            print(f"⏭️ No action needed: {fix['reason']}")
            actions_taken.append({"pod": pod["name"], "action": "none", "reason": fix["reason"]})

    return actions_taken


if __name__ == "__main__":
    print("🤖 AIOps Auto-Remediation Starting...")
    print("=" * 50)
    mode = input("Choose mode - (1) Auto  (2) Human Approval: ").strip()

    if mode == "1":
        results = auto_remediate()
    else:
        results = auto_remediate_with_approval()

    print("\n" + "=" * 50)
    print(f"📋 Total actions taken: {len(results)}")

