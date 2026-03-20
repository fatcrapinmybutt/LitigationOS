"""CLI entry point using Typer.

Provides command-line access to LitigationOS features including
case management, filing operations, and database utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from litigationos import __version__

app = typer.Typer(
    name="litigationos",
    help="LitigationOS — Pro se litigation management for Michigan courts.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version():
    """Show the current version."""
    console.print(f"LitigationOS v{__version__}")


@app.command()
def init(
    data_dir: Optional[Path] = typer.Option(
        None, "--data-dir", "-d", help="Data directory path"
    ),
):
    """Initialize the database and data directory."""
    from litigationos.app import create_app

    application = create_app(data_dir)
    console.print(f"[green][OK][/green] Database initialized at {application.db.db_path}")


@app.command()
def cases():
    """List all cases."""
    from litigationos.app import create_app

    application = create_app()
    rows = application.db.fetchall("SELECT id, case_number, title, status FROM cases ORDER BY id")

    table = Table(title="Cases")
    table.add_column("ID", style="dim")
    table.add_column("Case Number")
    table.add_column("Title")
    table.add_column("Status")

    for row in rows:
        table.add_row(str(row["id"]), row["case_number"] or "", row["title"], row["status"])

    console.print(table)


@app.command()
def deadlines():
    """Show upcoming deadlines."""
    from litigationos.app import create_app

    application = create_app()
    rows = application.db.fetchall(
        "SELECT d.*, c.title as case_title FROM deadlines d "
        "JOIN cases c ON d.case_id = c.id "
        "WHERE d.status = 'pending' ORDER BY d.due_date ASC LIMIT 20"
    )

    table = Table(title="Upcoming Deadlines")
    table.add_column("Due Date", style="bold")
    table.add_column("Case")
    table.add_column("Deadline")
    table.add_column("Priority")

    for row in rows:
        table.add_row(row["due_date"], row["case_title"], row["title"], row["priority"])

    console.print(table)


@app.command()
def gui():
    """Launch the graphical interface."""
    from litigationos.app import create_app

    application = create_app()
    application.run_gui()


if __name__ == "__main__":
    app()
