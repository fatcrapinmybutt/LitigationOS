"""
Typer CLI for LitigationOS Daemon.
Commands: start, stop, status, install, uninstall, config, skills, tasks.
"""
import json
import os
import sys
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    # Graceful fallback if typer/rich not installed
    typer = None
    Console = None
    Table = None


def _ensure_deps():
    if typer is None:
        print("ERROR: 'typer' and 'rich' packages required.")
        print("Install: pip install typer[all] rich")
        sys.exit(1)


_ensure_deps()

app = typer.Typer(
    name="litigationos-daemon",
    help="LitigationOS Daemon — 24/7 litigation intelligence service",
    no_args_is_help=True,
)
console = Console()


@app.command()
def start(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config YAML path"),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
):
    """Start the LitigationOS daemon."""
    from .ipc import IPCClient
    client = IPCClient()
    if client.ping():
        console.print("[yellow]Daemon is already running.[/yellow]")
        return

    if foreground:
        console.print("[green]Starting daemon in foreground...[/green]")
        from .core import DaemonCore
        daemon = DaemonCore(config_path=config)
        daemon.run()
    else:
        console.print("[green]Starting daemon as background service...[/green]")
        # On Windows, use pythonw to run detached
        script = os.path.join(os.path.dirname(__file__), "core.py")
        cmd = [sys.executable, script]
        if config:
            cmd.extend(["--config", config])

        import subprocess
        subprocess.Popen(
            cmd,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        console.print("[green]✓ Daemon started.[/green]")


@app.command()
def stop():
    """Stop the running daemon."""
    from .ipc import IPCClient
    client = IPCClient()
    resp = client.call("shutdown")
    if resp.success:
        console.print("[green]✓ Daemon stopped.[/green]")
    else:
        console.print(f"[red]Failed to stop daemon: {resp.error}[/red]")


@app.command()
def status():
    """Show daemon status and health."""
    from .ipc import IPCClient
    client = IPCClient()

    if not client.ping():
        console.print("[red]Daemon is not running.[/red]")
        return

    health = client.status()
    if isinstance(health, dict) and "error" in health:
        console.print(f"[red]{health['error']}[/red]")
        return

    # Status table
    table = Table(title="LitigationOS Daemon Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    if isinstance(health, dict):
        for key, val in health.items():
            if not isinstance(val, (list, dict)):
                table.add_row(str(key), str(val))

    console.print(table)


@app.command()
def config(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Config file path"),
    validate: bool = typer.Option(False, "--validate", help="Validate config"),
    generate: bool = typer.Option(False, "--generate", help="Generate default config"),
):
    """Manage daemon configuration."""
    from .config import generate_default_config, load_config, validate_config

    if generate:
        out = generate_default_config(path)
        console.print(f"[green]✓ Default config generated: {out}[/green]")
        return

    if validate:
        valid, errors = validate_config(path)
        if valid:
            console.print("[green]✓ Configuration is valid.[/green]")
        else:
            console.print("[red]Configuration errors:[/red]")
            for err in errors:
                console.print(f"  [red]• {err}[/red]")
        return

    # Show current config
    cfg = load_config(path)
    console.print_json(cfg.model_dump_json(indent=2))


@app.command()
def skills(
    scan: bool = typer.Option(False, "--scan", help="Rescan skill directories"),
    tier: Optional[str] = typer.Option(None, "--tier", help="Filter by tier"),
):
    """List registered skills."""
    from .config import load_config
    from .skill_registry import SkillRegistry

    cfg = load_config()
    registry = SkillRegistry(cfg.db_path)

    if scan:
        found = registry.scan()
        console.print(f"[green]✓ Scanned {len(found)} skills.[/green]")

    all_skills = registry.list_all(tier=tier)

    table = Table(title=f"Skills ({len(all_skills)})")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Tier")
    table.add_column("Uses", justify="right")
    table.add_column("Success %", justify="right")

    for s in all_skills:
        table.add_row(
            s.name, s.version, s.tier.value,
            str(s.usage_count),
            f"{s.success_rate * 100:.0f}%",
        )

    console.print(table)


@app.command()
def tasks(
    limit: int = typer.Option(20, "--limit", "-n", help="Max tasks to show"),
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List tasks in the queue."""
    from .config import load_config
    from .task_queue import TaskQueue

    cfg = load_config()
    queue = TaskQueue(cfg.db_path)

    depth = queue.depth()
    console.print(f"\n[bold]Queue Depth:[/bold] {json.dumps(depth, indent=2)}\n")

    metrics = queue.get_metrics(hours=24)
    if metrics:
        table = Table(title="24h Metrics")
        table.add_column("Metric")
        table.add_column("Count", justify="right")
        table.add_column("Avg Value", justify="right")
        for k, v in metrics.items():
            table.add_row(k, str(v["count"]), f"{v['avg']:.2f}")
        console.print(table)


@app.command()
def install():
    """Install daemon as Windows service (requires admin)."""
    console.print("[yellow]Windows service installation requires NSSM or similar.[/yellow]")
    console.print("Download NSSM from https://nssm.cc/download")
    console.print(f"Then run: nssm install LitigationOSDaemon {sys.executable} -m 00_SYSTEM.daemon.core")


@app.command()
def uninstall():
    """Remove Windows service."""
    console.print("[yellow]Run: nssm remove LitigationOSDaemon confirm[/yellow]")


def main():
    app()


if __name__ == "__main__":
    main()
