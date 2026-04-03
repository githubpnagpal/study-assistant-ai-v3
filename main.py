"""
AI Study Assistant v2 — Multi-Agent System
Teacher Agent teaches. Tester Agent quizzes. You learn.
"""

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from agents import StudySession, run_teacher, run_tester
from providers import PROVIDERS, get_claude_client, get_groq_client
from tools import list_topics

load_dotenv()
console = Console()


# ─────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────

def select_provider() -> dict:
    table = Table(title="Choose Your AI Provider", border_style="cyan", show_lines=True)
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Model", style="bold white")
    table.add_column("Description", style="dim")
    table.add_column("Cost", style="green")

    for key, p in PROVIDERS.items():
        table.add_row(key, p["name"], p["description"], p["cost"])

    console.print(table)

    while True:
        choice = Prompt.ask("Select provider", choices=list(PROVIDERS.keys()), default="1")
        provider = PROVIDERS[choice]

        if provider["provider"] == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
            console.print("[red]ANTHROPIC_API_KEY not set in .env[/red]")
            continue
        if provider["provider"] == "groq" and not os.getenv("GROQ_API_KEY"):
            console.print("[red]GROQ_API_KEY not set in .env — get a free key at console.groq.com[/red]")
            continue
        return provider


def get_client(provider: dict):
    if provider["provider"] == "claude":
        return get_claude_client()
    return get_groq_client()


def print_welcome(provider: dict):
    console.print(Panel(
        "[bold cyan]AI Study Assistant v2[/bold cyan] — [bold yellow]Multi-Agent Mode[/bold yellow]\n\n"
        "[bold white]Two agents are ready:[/bold white]\n"
        "  [green]Teacher[/green] — explains any AI concept at your level\n"
        "  [magenta]Tester[/magenta]  — quizzes you and tracks your score\n\n"
        f"[dim]Using: {provider['name']}[/dim]\n\n"
        "[bold]Commands:[/bold]\n"
        "  [green]quiz[/green] or [green]quiz <topic>[/green] — start a quiz\n"
        "  [green]learn[/green]                  — go back to learning\n"
        "  [green]score[/green]                  — see your current score\n"
        "  [green]notes[/green]                  — view saved study notes\n"
        "  [green]switch[/green]                 — change AI provider\n"
        "  [green]quit[/green]                   — exit",
        border_style="cyan",
        title="Welcome"
    ))


def print_mode_banner(mode: str, topic: str):
    if mode == "testing":
        console.print(Panel(
            f"[bold magenta]QUIZ MODE[/bold magenta] — Topic: [yellow]{topic}[/yellow]\n"
            "[dim]Answer the questions. Type 'learn' to go back to studying.[/dim]",
            border_style="magenta"
        ))
    else:
        console.print(Panel(
            f"[bold green]LEARN MODE[/bold green] — Topic: [yellow]{topic}[/yellow]\n"
            "[dim]Ask me anything about AI! Type 'quiz' when ready to be tested.[/dim]",
            border_style="green"
        ))


def print_score(session: StudySession):
    console.print(Panel(
        session.get_score_display(),
        title="Your Score",
        border_style="yellow"
    ))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    provider = select_provider()
    client = get_client(provider)
    session = StudySession()

    print_welcome(provider)

    while True:
        # Show prompt based on current mode
        mode_label = "[magenta]Tester>[/magenta]" if session.mode == "testing" else "[green]Teacher>[/green]"
        prompt_label = f"\n[bold]{mode_label}[/bold] [bold white]You[/bold white]"

        try:
            user_input = Prompt.ask(prompt_label).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye! Keep learning![/dim]")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────

        if user_input.lower() in ("quit", "exit", "bye"):
            print_score(session)
            console.print("[dim]Goodbye! Keep learning![/dim]")
            break

        if user_input.lower() == "score":
            print_score(session)
            continue

        if user_input.lower() == "notes":
            console.print(Panel(list_topics(), title="Your Study Topics", border_style="blue"))
            continue

        if user_input.lower() == "switch":
            console.print()
            provider = select_provider()
            client = get_client(provider)
            session = StudySession()
            console.print(f"[green]Switched to {provider['name']}. Session reset.[/green]")
            continue

        if user_input.lower() == "learn":
            session.switch_to_learning()
            print_mode_banner("learning", session.current_topic)
            continue

        if user_input.lower().startswith("quiz"):
            parts = user_input.split(maxsplit=1)
            topic = parts[1] if len(parts) > 1 else session.current_topic
            session.switch_to_testing(topic)
            print_mode_banner("testing", topic)

            # Tester starts with a question immediately
            console.print(f"\n[bold magenta]Tester[/bold magenta] [dim]({provider['name']})[/dim]")
            try:
                run_tester(client, provider, session, "")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            continue

        # ── Route to correct agent ─────────────────────

        if session.mode == "learning":
            # Update current topic from what user is asking about
            session.current_topic = user_input[:50]  # rough topic capture
            console.print(f"\n[bold green]Teacher[/bold green] [dim]({provider['name']})[/dim]")
            try:
                run_teacher(client, provider, session, user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("[dim]Type 'switch' to try a different provider.[/dim]")
                session.teacher_messages.pop()

        elif session.mode == "testing":
            console.print(f"\n[bold magenta]Tester[/bold magenta] [dim]({provider['name']})[/dim]")
            try:
                run_tester(client, provider, session, user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print("[dim]Type 'switch' to try a different provider.[/dim]")


if __name__ == "__main__":
    main()
