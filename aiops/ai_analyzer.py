import os
import json
from openai import AzureOpenAI
from log_reader import get_cluster_summary, get_pod_logs, get_crashed_pods


client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")


def analyze_cluster_health():
    """Ask AI to analyze cluster health"""
    summary = get_cluster_summary()
    
    prompt = f"""You are a DevOps AI assistant. Analyze this Kubernetes cluster health report 
and provide:
1. Overall health status (HEALTHY / WARNING / CRITICAL)
2. Any issues found
3. Recommended actions

Cluster Report:
{json.dumps(summary, indent=2)}"""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are an expert DevOps/SRE engineer. Be concise and actionable."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content


def analyze_pod_error(pod_name, namespace="skillpulse"):
    """Ask AI to diagnose why a pod is failing"""
    logs = get_pod_logs(pod_name, namespace)
    
    prompt = f"""Analyze these Kubernetes pod logs and tell me:
1. What is the error?
2. Root cause
3. How to fix it (give exact kubectl or yaml commands)

Pod: {pod_name}
Logs:
{logs}"""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are an expert DevOps/SRE engineer. Give specific commands to fix issues."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content


def auto_diagnose():
    """Automatically find and diagnose all problem pods"""
    crashed = get_crashed_pods()
    
    if not crashed:
        return "✅ All pods healthy. No issues found."
    
    report = []
    for pod in crashed:
        diagnosis = analyze_pod_error(pod["name"])
        report.append({
            "pod": pod["name"],
            "status": pod["status"],
            "restarts": pod["restarts"],
            "ai_diagnosis": diagnosis
        })
    
    return report


if __name__ == "__main__":
    print("=== Cluster Health Analysis ===")
    print(analyze_cluster_health())
    print("\n=== Auto Diagnosis ===")
    result = auto_diagnose()
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2))
