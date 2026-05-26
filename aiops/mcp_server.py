import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DevOps Tools")


@mcp.tool()
def get_pods(namespace: str = "skillpulse") -> str:
    """Get status of all pods in a Kubernetes namespace"""
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", namespace, "-o", "wide"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = "skillpulse", lines: int = 30) -> str:
    """Get recent logs from a specific pod"""
    result = subprocess.run(
        ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def restart_pod(pod_name: str, namespace: str = "skillpulse") -> str:
    """Restart a pod by deleting it (Kubernetes auto-recreates)"""
    result = subprocess.run(
        ["kubectl", "delete", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def scale_deployment(deployment: str, replicas: int, namespace: str = "skillpulse") -> str:
    """Scale a deployment to specified number of replicas"""
    result = subprocess.run(
        ["kubectl", "scale", f"deployment/{deployment}", f"--replicas={replicas}", "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def get_services(namespace: str = "skillpulse") -> str:
    """Get all services in a namespace"""
    result = subprocess.run(
        ["kubectl", "get", "svc", "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def describe_pod(pod_name: str, namespace: str = "skillpulse") -> str:
    """Get detailed description of a pod including events and conditions"""
    result = subprocess.run(
        ["kubectl", "describe", "pod", pod_name, "-n", namespace],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def get_cluster_info() -> str:
    """Get overall cluster information"""
    result = subprocess.run(
        ["kubectl", "cluster-info"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


@mcp.tool()
def docker_images() -> str:
    """List all Docker images on the system"""
    result = subprocess.run(
        ["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"


if __name__ == "__main__":
    mcp.run()
