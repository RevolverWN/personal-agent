"""Personal Agent CLI — main entry point."""

from __future__ import annotations

import sys
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="personal-agent",
    help="Personal AI Agent CLI — chat, manage sessions, configure settings.",
    add_completion=False,
)
console = Console()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "http://localhost:8000"
BASE_URL_ENV_VAR = "PERSONAL_AGENT_BASE_URL"


def get_base_url() -> str:
    """Resolve the API base URL, checking env var first."""
    import os
    return os.environ.get(BASE_URL_ENV_VAR, DEFAULT_BASE_URL)


def get_auth_headers() -> dict[str, str]:
    """Build auth headers. Reads token from env for now."""
    import os
    token = os.environ.get("PERSONAL_AGENT_TOKEN", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def chat(
    message: Optional[str] = typer.Argument(
        default=None,
        help="Message to send. If omitted, enters interactive mode.",
    ),
    model: Optional[str] = typer.Option(
        default=None,
        "--model",
        "-m",
        help="Model to use (e.g. gpt-4o, deepseek-chat).",
    ),
    stream: bool = typer.Option(
        default=False,
        "--stream/--no-stream",
        help="Enable streaming output.",
    ),
    conversation_id: Optional[str] = typer.Option(
        default=None,
        "--conversation-id",
        "-c",
        help="Continue an existing conversation.",
    ),
    base_url: Optional[str] = typer.Option(
        default=None,
        "--base-url",
        "-b",
        help=f"API base URL (default: {DEFAULT_BASE_URL}, env: {BASE_URL_ENV_VAR}).",
    ),
) -> None:
    """
    Chat with the AI agent.

    Single-shot:  personal-agent chat "hello, world"
    Interactive:  personal-agent chat

    Use --stream for streaming responses.
    """
    base = base_url or get_base_url()
    headers = get_auth_headers()

    if message:
        _chat_single(base, headers, message, model, stream, conversation_id)
    else:
        _chat_interactive(base, headers, model, stream)


def _chat_single(
    base_url: str,
    headers: dict,
    message: str,
    model: Optional[str],
    stream: bool,
    conversation_id: Optional[str],
) -> None:
    """Send a single message and print the response."""
    payload: dict = {
        "message": message,
        "stream": stream,
    }
    if model:
        payload["model"] = model
    if conversation_id:
        payload["conversation_id"] = conversation_id

    try:
        with httpx.Client(base_url=base_url, timeout=60.0) as client:
            response = client.post(
                "/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            if stream:
                _print_stream(response)
            else:
                data = response.json()
                _print_markdown(data.get("message", {}).get("content", ""))
    except httpx.ConnectError:
        console.print(
            f"[red]Error:[/red] Cannot connect to {base_url}. "
            "Is the server running? (uvicorn app.main:app)"
        )
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]HTTP {exc.response.status_code}:[/red] {exc.response.text}")
        raise typer.Exit(code=1)


def _chat_interactive(
    base_url: str,
    headers: dict,
    default_model: Optional[str],
    stream: bool,
) -> None:
    """Loop: read line → send → print → repeat. Ctrl-C to exit."""
    console.print(Panel.fit(
        "[bold cyan]Personal Agent CLI[/bold cyan]  —  "
        "Type your message and press Enter.\n"
        "Press [bold]Ctrl+C[/bold] or type [bold]exit[/bold] to quit.",
        border_style="cyan",
    ))

    conversation_id: Optional[str] = None

    while True:
        try:
            message = console.input("\n[bold green]›[/bold green] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if message.strip().lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        if not message.strip():
            continue

        payload: dict = {"message": message, "stream": False}
        if default_model:
            payload["model"] = default_model

        try:
            with httpx.Client(base_url=base_url, timeout=60.0) as client:
                response = client.post(
                    "/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                _print_markdown(content)
                conversation_id = data.get("conversation_id", conversation_id)
        except httpx.ConnectError:
            console.print("[red]Cannot connect to server.[/red]")
            break
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]Error {exc.response.status_code}:[/red] {exc.response.text}")
            continue


def _print_stream(response: httpx.Response) -> None:
    """Consume an SSE stream and print chunks as they arrive."""
    console.print("[cyan]…[/cyan]", end="", flush=True)
    content = ""
    for line in response.iter_lines():
        if not line.startswith("data: "):
            continue
        raw = line[6:].strip()
        if raw == "[DONE]" or raw == "":
            break
        try:
            import json
            payload = json.loads(raw)
            chunk = payload.get("content", "")
            if chunk:
                console.print(chunk, end="", flush=True)
                content += chunk
        except Exception:
            pass
    console.print()


def _print_markdown(text: str) -> None:
    """Render text as a Rich Markdown panel."""
    if not text:
        return
    md = Markdown(text)
    console.print(Panel(md, border_style="green", padding=(0, 1)))


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

sessions_app = typer.Typer(help="Manage conversations.")
app.add_typer(sessions_app, name="sessions")


@sessions_app.command("list")
def sessions_list(
    limit: int = typer.Option(default=20, "--limit", "-n", help="Max results."),
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
) -> None:
    """List all conversations."""
    base = base_url or get_base_url()
    headers = get_auth_headers()

    try:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            response = client.get(
                "/api/v1/chat/conversations",
                params={"limit": limit},
                headers=headers,
            )
            response.raise_for_status()
            conversations = response.json()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to server.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error {exc.response.status_code}:[/red]")
        raise typer.Exit(code=1)

    if not conversations:
        console.print("[dim]No conversations found.[/dim]")
        return

    table = Table(title="Conversations")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Title", style="cyan")
    table.add_column("Messages", justify="right", style="yellow")
    table.add_column("Updated At", style="dim")

    for conv in conversations:
        table.add_row(
            conv.get("id", "")[:36],
            conv.get("title") or "[italic]Untitled[/italic]",
            str(conv.get("message_count", 0)),
            _format_time(conv.get("updated_at")),
        )

    console.print(table)


@sessions_app.command("show")
def sessions_show(
    conversation_id: str = typer.Argument(..., help="Conversation ID to show."),
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
) -> None:
    """Show messages in a conversation."""
    base = base_url or get_base_url()
    headers = get_auth_headers()

    try:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            messages_resp = client.get(
                f"/api/v1/chat/conversations/{conversation_id}/messages",
                headers=headers,
            )
            messages_resp.raise_for_status()
            messages = messages_resp.json()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to server.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError:
        console.print("[red]Conversation not found.[/red]")
        raise typer.Exit(code=1)

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        color = "green" if role == "user" else "cyan" if role == "assistant" else "yellow"
        label = f"[bold {color}]{role.upper()}[/bold {color}]"
        console.print(Panel(content, title=label, border_style=color, padding=(0, 1)))
        console.print()


@sessions_app.command("delete")
def sessions_delete(
    conversation_id: str = typer.Argument(..., help="Conversation ID to delete."),
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
    force: bool = typer.Option(default=False, "--force", "-f", help="Skip confirmation."),
) -> None:
    """Delete a conversation."""
    base = base_url or get_base_url()
    headers = get_auth_headers()

    if not force:
        confirm = console.input(
            f"[yellow]Delete conversation [bold]{conversation_id}[/bold]? [y/N]: [/yellow]"
        )
        if confirm.strip().lower() != "y":
            console.print("[dim]Aborted.[/dim]")
            return

    try:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            response = client.delete(
                f"/api/v1/chat/conversations/{conversation_id}",
                headers=headers,
            )
            response.raise_for_status()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to server.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError:
        console.print("[red]Conversation not found.[/red]")
        raise typer.Exit(code=1)

    console.print("[green]Conversation deleted.[/green]")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

config_app = typer.Typer(help="View and update configuration.")
app.add_typer(config_app, name="config")


@config_app.command("list")
def config_list(
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
) -> None:
    """List available models."""
    _config_list_impl(base_url=base_url)


def _config_list_impl(base_url: Optional[str]) -> None:
    """Shared implementation for listing models."""
    base = base_url or get_base_url()
    headers = get_auth_headers()

    try:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            response = client.get("/api/v1/models", headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError:
        console.print("[red]Cannot connect to server.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error {exc.response.status_code}:[/red]")
        raise typer.Exit(code=1)

    models = data.get("models", [])
    default = data.get("default_model", "")

    table = Table(title=f"Available Models  (default: {default})")
    table.add_column("ID", style="cyan")
    table.add_column("Provider", style="yellow")
    table.add_column("Description", style="dim")
    table.add_column("Vision", justify="center")

    for m in models:
        marker = "✓" if m["id"] == default else ""
        table.add_row(
            f"[bold]{m['id']}[/bold] {marker}",
            m.get("provider", ""),
            m.get("description", ""),
            "✓" if m.get("supports_vision") else "—",
        )

    console.print(table)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key."),
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
) -> None:
    """Get a configuration value (reads from local .env)."""
    import os
    from pathlib import Path

    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                if k.strip() == key:
                    console.print(f"[cyan]{key}[/cyan] = [green]{v.strip()}[/green]")
                    return

    console.print(f"[dim]Key '{key}' not found.[/dim]")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@app.command("models")
def list_models(
    base_url: Optional[str] = typer.Option(default=None, "--base-url", "-b"),
) -> None:
    """List all available models (alias: personal-agent config list)."""
    _config_list_impl(base_url=base_url)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _format_time(iso_str: Optional[str]) -> str:
    """Pretty-print an ISO datetime string."""
    if not iso_str:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str[:16]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Called by `personal-agent` console script (pyproject.toml)."""
    app()


if __name__ == "__main__":
    main()
