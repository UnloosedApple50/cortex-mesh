"""
CortexMesh — CLI tool (cortexctl).

Complete CLI for administering CortexMesh clusters.
All commands connect to a running controller for cluster operations.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

import httpx
import typer
import uvicorn

from cortexmesh.models import NodeState, Platform, Architecture

app = typer.Typer(
    help="CortexMesh — Universal Multi-Machine Orchestration",
    no_args_is_help=True,
)

# ── Controller command ────────────────────────────────────────────


@app.command()
def controller(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    db: str = typer.Option(
        "sqlite+aiosqlite:///./cortexmesh.db", "--db"
    ),
):
    """Start the CortexMesh Controller."""
    os.environ["DATABASE_URL"] = db
    from cortexmesh.database import init_db

    import asyncio

    asyncio.get_event_loop().run_until_complete(init_db())
    uvicorn.run(
        "cortexmesh.server.api:app", host=host, port=port, reload=False
    )


# ── Agent command ─────────────────────────────────────────────────


@app.command()
def agent(
    controller_url: str = typer.Option(..., "--controller", "-c"),
    enrollment_token: str = typer.Option(..., "--token", "-t"),
    node_name: str = typer.Option(None, "--name"),
):
    """Start the CortexMesh Agent."""
    from cortexmesh.agent.agent import Agent
    import asyncio

    agent_inst = Agent(
        controller_url=controller_url,
        enrollment_token=enrollment_token,
        node_name=node_name,
    )
    asyncio.get_event_loop().run_until_complete(agent_inst.start())


# ── Doctor command ────────────────────────────────────────────────


@app.command()
def doctor():
    """Run diagnostics."""
    from cortexmesh.adapters.platform.detect import detect_all_capabilities

    caps = detect_all_capabilities()
    typer.echo("CortexMesh Diagnostic")
    typer.echo("=" * 40)
    typer.echo(f"Platform: {caps['cpu'].architecture}")
    typer.echo(
        f"CPU: {caps['cpu'].model} ({caps['cpu'].threads} threads)"
    )
    typer.echo(
        f"Memory: {caps['memory'].total_bytes / (1024**3):.1f} GB"
    )
    if caps["gpus"]:
        for gpu in caps["gpus"]:
            typer.echo(
                f"GPU: {gpu.model} ({gpu.vram_bytes / (1024**3) if gpu.vram_bytes else 'unknown'} GB)"
            )
    else:
        typer.echo("GPU: None detected")


# ── Version command ───────────────────────────────────────────────


@app.command()
def version():
    """Show version."""
    typer.echo("CortexMesh v0.1.0")


# ── Helper ────────────────────────────────────────────────────────


def _get_controller(controller: Optional[str]) -> str:
    url = controller or os.environ.get("HERMESMESH_CONTROLLER", "")
    if not url:
        typer.echo(
            "Error: --controller or HERMESMESH_CONTROLLER env var required",
            err=True,
        )
        raise typer.Exit(1)
    return url.rstrip("/")


# ── Status command ────────────────────────────────────────────────


@app.command()
def status(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Show cluster status."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{url}/api/v1/health").json()
            nodes = client.get(f"{url}/api/v1/nodes").json()
            tasks = client.get(f"{url}/api/v1/tasks").json()

        online = sum(1 for n in nodes if n.get("state") == "online")
        running = sum(1 for t in tasks if t.get("state") == "running")
        queued = sum(1 for t in tasks if t.get("state") == "queued")

        typer.echo("CortexMesh Cluster Status")
        typer.echo("=" * 40)
        typer.echo(f"Controller: {url}")
        typer.echo(f"Health: {health.get('status', 'unknown')}")
        typer.echo(f"Version: {health.get('version', 'unknown')}")
        typer.echo(f"Nodes: {len(nodes)} ({online} online)")
        typer.echo(
            f"Tasks: {len(tasks)} ({running} running, {queued} queued)"
        )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Node commands ────────────────────────────────────────────────-

node_app = typer.Typer(help="Node management")
app.add_typer(node_app, name="node")


@node_app.command("list")
def node_list(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List all nodes."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            nodes = client.get(f"{url}/api/v1/nodes").json()
        if not nodes:
            typer.echo("No nodes registered.")
            return
        typer.echo(f"{'NODE_ID':<38} {'HOSTNAME':<20} {'STATE':<12} {'ROLES'}")
        typer.echo("-" * 80)
        for n in nodes:
            roles = ",".join(n.get("roles", []))
            typer.echo(
                f"{n['node_id']:<38} {n['hostname']:<20} {n['state']:<12} {roles}"
            )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@node_app.command("info")
def node_info(
    node_id: str = typer.Argument(..., help="Node ID"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Show detailed node information."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            node = client.get(f"{url}/api/v1/nodes/{node_id}").json()
        typer.echo(json.dumps(node, indent=2, default=str))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            typer.echo(f"Node {node_id} not found", err=True)
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@node_app.command("enable")
def node_enable(
    node_id: str = typer.Argument(..., help="Node ID"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Enable a node (resume task scheduling)."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            client.patch(
                f"{url}/api/v1/nodes/{node_id}",
                json={"compute_enabled": True},
            )
        typer.echo(f"Node {node_id} enabled.")
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@node_app.command("disable")
def node_disable(
    node_id: str = typer.Argument(..., help="Node ID"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Disable a node (pause task scheduling)."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            client.patch(
                f"{url}/api/v1/nodes/{node_id}",
                json={"compute_enabled": False},
            )
        typer.echo(f"Node {node_id} disabled.")
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Task commands ─────────────────────────────────────────────────

task_app = typer.Typer(help="Task management")
app.add_typer(task_app, name="task")


@task_app.command("list")
def task_list(
    state: str = typer.Option(None, "--state", help="Filter by state"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List tasks."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            params = {}
            if state:
                params["state"] = state
            tasks = client.get(f"{url}/api/v1/tasks", params=params).json()
        if not tasks:
            typer.echo("No tasks.")
            return
        typer.echo(
            f"{'TASK_ID':<38} {'TITLE':<30} {'STATE':<12} {'NODE'}"
        )
        typer.echo("-" * 90)
        for t in tasks:
            typer.echo(
                f"{t['task_id']:<38} {t['title']:<30} {t['state']:<12} {t.get('node_id', '-')}"
            )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@task_app.command("submit")
def task_submit(
    task_type: str = typer.Option("chat", "--type"),
    title: str = typer.Option(..., "--title"),
    cpu_threads: int = typer.Option(None, "--cpu"),
    memory_gb: float = typer.Option(None, "--memory"),
    gpu: bool = typer.Option(False, "--gpu/--no-gpu"),
    vram_gb: float = typer.Option(None, "--vram"),
    priority: str = typer.Option("normal", "--priority"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Submit a new task."""
    url = _get_controller(controller)
    requirements = {}
    if cpu_threads:
        requirements["cpu_threads"] = cpu_threads
    if memory_gb:
        requirements["memory_gb"] = memory_gb
    if gpu:
        requirements["gpu_required"] = True
    if vram_gb:
        requirements["vram_gb"] = vram_gb

    payload = {
        "task_type": task_type,
        "title": title,
        "requirements": requirements,
        "priority": priority,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{url}/api/v1/tasks", json=payload)
        data = resp.json()
        typer.echo(f"Task submitted: {data['task_id']}")
        typer.echo(f"  Title: {data['title']}")
        typer.echo(f"  State: {data['state']}")
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@task_app.command("cancel")
def task_cancel(
    task_id: str = typer.Argument(..., help="Task ID"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Cancel a running or queued task."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{url}/api/v1/tasks/{task_id}/cancel")
        data = resp.json()
        typer.echo(data.get("message", "Cancellation requested"))
    except httpx.HTTPStatusError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Model commands ────────────────────────────────────────────────

model_app = typer.Typer(help="Model management")
app.add_typer(model_app, name="model")


@model_app.command("list")
def model_list(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List available models across nodes."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            nodes = client.get(f"{url}/api/v1/nodes").json()
        models = {}
        for node in nodes:
            for provider in node.get("capabilities", {}).get(
                "providers", []
            ):
                for model in provider.get("models", []):
                    if model not in models:
                        models[model] = []
                    models[model].append(node["hostname"])
        if not models:
            typer.echo("No models discovered.")
            return
        typer.echo(f"{'MODEL':<40} {'NODES'}")
        typer.echo("-" * 60)
        for model, nodes in sorted(models.items()):
            typer.echo(f"{model:<40} {', '.join(nodes)}")
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Provider commands ─────────────────────────────────────────────

provider_app = typer.Typer(help="Provider management")
app.add_typer(provider_app, name="provider")


@provider_app.command("list")
def provider_list(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List configured providers."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            providers = client.get(f"{url}/api/v1/providers").json()
        if not providers:
            typer.echo("No providers configured.")
            return
        typer.echo(
            f"{'PROVIDER_ID':<38} {'TYPE':<20} {'NAME':<20} {'AVAILABLE'}"
        )
        typer.echo("-" * 90)
        for p in providers:
            typer.echo(
                f"{p['provider_id']:<38} {p['provider_type']:<20} {p.get('name', '-'):<20} {p.get('is_available', False)}"
            )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


@provider_app.command("test")
def provider_test(
    provider_id: str = typer.Argument(..., help="Provider ID"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Test provider connectivity."""
    url = _get_controller(controller)
    typer.echo(f"Testing provider {provider_id}...")
    typer.echo("Provider test not yet implemented.")


# ── Storage commands ──────────────────────────────────────────────

storage_app = typer.Typer(help="Storage management")
app.add_typer(storage_app, name="storage")


@storage_app.command("list")
def storage_list(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List storage locations."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            locations = client.get(f"{url}/api/v1/storage").json()
        if not locations:
            typer.echo("No storage locations.")
            return
        typer.echo(
            f"{'LOCATION_ID':<38} {'NODE':<20} {'PATH':<25} {'FREE (GB)'}"
        )
        typer.echo("-" * 95)
        for loc in locations:
            free_gb = loc.get("free_bytes", 0) / (1024**3)
            typer.echo(
                f"{loc['location_id']:<38} {loc.get('node_id', '-'):<20} {loc['path']:<25} {free_gb:.1f}"
            )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Profile commands ──────────────────────────────────────────────

profile_app = typer.Typer(help="Profile management")
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def profile_list(
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List profiles."""
    url = _get_controller(controller)
    typer.echo("Profile listing not yet implemented.")


@profile_app.command("apply")
def profile_apply(
    profile_name: str = typer.Argument(..., help="Profile name"),
    node_id: str = typer.Option(None, "--node", help="Apply to specific node"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """Apply a profile."""
    url = _get_controller(controller)
    typer.echo(f"Applying profile '{profile_name}'...")
    typer.echo("Profile apply not yet implemented.")


# ── Event commands ────────────────────────────────────────────────

event_app = typer.Typer(help="Event management")
app.add_typer(event_app, name="event")


@event_app.command("list")
def event_list(
    limit: int = typer.Option(20, "--limit"),
    controller: str = typer.Option(None, "--controller", "-c"),
):
    """List recent events."""
    url = _get_controller(controller)
    try:
        with httpx.Client(timeout=5.0) as client:
            events = client.get(
                f"{url}/api/v1/events", params={"limit": limit}
            ).json()
        if not events:
            typer.echo("No events.")
            return
        typer.echo(f"{'TIMESTAMP':<30} {'TYPE':<25} {'MESSAGE'}")
        typer.echo("-" * 80)
        for e in events:
            ts = e.get("timestamp", "")
            typer.echo(
                f"{ts:<30} {e.get('event_type', ''):<25} {e.get('message', '')}"
            )
    except httpx.ConnectError:
        typer.echo(f"Cannot connect to controller at {url}", err=True)
        raise typer.Exit(1)


# ── Config commands ───────────────────────────────────────────────

config_app = typer.Typer(help="Configuration")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Show current configuration."""
    typer.echo("CortexMesh Configuration")
    typer.echo("=" * 40)
    typer.echo(
        f"Controller URL: {os.environ.get('HERMESMESH_CONTROLLER', 'not set')}"
    )
    typer.echo(
        f"Database URL: {os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///./cortexmesh.db')}"
    )
    typer.echo(f"Config dir: ~/.cortexmesh/")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    typer.echo(f"Setting {key}={value}")
    typer.echo("Config persistence not yet implemented.")
    typer.echo(f"Use export {key}={value} for now.")


# ── Logs command ──────────────────────────────────────────────────


@app.command()
def logs(
    lines_count: int = typer.Option(50, "--lines", "-n"),
):
    """Show recent log lines."""
    typer.echo(f"Showing last {lines_count} log lines...")
    typer.echo("Log viewing not yet implemented.")


if __name__ == "__main__":
    app()
