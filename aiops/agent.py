import os
import json
import subprocess
from typing import TypedDict, Annotated
from dotenv import load_dotenv

load_dotenv()

# LangSmith Tracing - automatically traces all LLM calls
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "Ashok-AIOps-DevOps")

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition


# === State ===
class State(TypedDict):
    messages: Annotated[list, add_messages]


# === DevOps Tools ===
@tool
def get_pods(namespace: str = "skillpulse") -> str:
    """Get status of all pods in a Kubernetes namespace"""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "wide"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def get_pod_logs(pod_name: str, namespace: str = "skillpulse", lines: int = 30) -> str:
    """Get recent logs from a specific pod"""
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def restart_pod(pod_name: str, namespace: str = "skillpulse") -> str:
    """Restart a pod by deleting it (Kubernetes auto-recreates)"""
    result = subprocess.run(
        ["kubectl", "delete", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def scale_deployment(deployment: str, replicas: int, namespace: str = "skillpulse") -> str:
    """Scale a deployment to specified number of replicas"""
    result = subprocess.run(
        ["kubectl", "scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def get_services(namespace: str = "skillpulse") -> str:
    """Get all services in a namespace"""
    result = subprocess.run(
        ["kubectl", "get", "svc", "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def get_node_status() -> str:
    """Get status of all Kubernetes nodes"""
    result = subprocess.run(
        ["kubectl", "get", "nodes", "-o", "wide"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def describe_pod(pod_name: str, namespace: str = "skillpulse") -> str:
    """Get detailed description of a pod (events, conditions, etc.)"""
    result = subprocess.run(
        ["kubectl", "describe", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@tool
def get_docker_images() -> str:
    """List all Docker images on the system"""
    result = subprocess.run(
        ["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


# === Build Agent ===
tools = [get_pods, get_pod_logs, restart_pod, scale_deployment,
         get_services, get_node_status, describe_pod, get_docker_images]

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3)
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    system_message = {
        "role": "system",
        "content": """You are an expert DevOps/SRE AI agent managing a Kubernetes cluster.
You have access to kubectl and docker tools.

Your responsibilities:
1. Monitor pod health and diagnose issues
2. Analyze logs to find root causes
3. Suggest or execute fixes (restart pods, scale deployments)
4. Provide clear explanations of what you find

Always check pod status first before taking any action.
Be cautious with destructive actions (restart, scale down)."""
    }
    messages = [system_message] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}


# === Build Graph ===
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()


# === Interactive Chat ===
def main():
    print("=" * 50)
    print("🤖 AIOps Agent - DevOps AI Assistant")
    print("=" * 50)
    print("Commands: 'quit' to exit, 'status' for quick health check")
    print("=" * 50)

    while True:
        user_input = input("\n📝 You: ").strip()

        if user_input.lower() == "quit":
            print("👋 Goodbye!")
            break

        if user_input.lower() == "status":
            user_input = "Check the health of all pods in the skillpulse namespace. Report any issues."

        response = graph.invoke({"messages": [{"role": "user", "content": user_input}]})
        ai_message = response["messages"][-1].content
        print(f"\n🤖 Agent: {ai_message}")


if __name__ == "__main__":
    main()
