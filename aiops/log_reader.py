import subprocess
import json
from datetime import datetime


def get_pod_status(namespace="skillpulse"):
    """Get status of all pods in namespace"""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
        capture_output=True, text=True
    )
    pods = json.loads(result.stdout)
    
    pod_info = []
    for pod in pods.get("items", []):
        name = pod["metadata"]["name"]
        status = pod["status"]["phase"]
        restarts = pod["status"]["containerStatuses"][0]["restartCount"] if pod["status"].get("containerStatuses") else 0
        pod_info.append({"name": name, "status": status, "restarts": restarts})
    
    return pod_info


def get_pod_logs(pod_name, namespace="skillpulse", lines=50):
    """Get recent logs from a specific pod"""
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)],
        capture_output=True, text=True
    )
    return result.stdout


def get_crashed_pods(namespace="skillpulse"):
    """Find pods that are not running or have restarts"""
    pods = get_pod_status(namespace)
    problems = []
    for pod in pods:
        if pod["status"] != "Running" or pod["restarts"] > 0:
            problems.append(pod)
    return problems


def get_cluster_summary(namespace="skillpulse"):
    """Get full cluster health summary"""
    pods = get_pod_status(namespace)
    crashed = get_crashed_pods(namespace)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_pods": len(pods),
        "running": len([p for p in pods if p["status"] == "Running"]),
        "problems": len(crashed),
        "pod_details": pods,
        "problem_pods": crashed
    }
    return summary


if __name__ == "__main__":
    summary = get_cluster_summary()
    print(json.dumps(summary, indent=2))
