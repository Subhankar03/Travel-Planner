"""AI Travel Planner — Rich CLI Interface for testing."""

from __future__ import annotations
import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Dialog, Label, RadioList
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.traceback import install

from backend.agent import build_graph
from backend.utils import TravelPlannerLogger

install()


# ── Constants ──────────────────────────────────────────────────────────────────
NODE_STYLES = {
    "supervisor": ("🧭", "bold yellow"),
    "booking_agent": ("🛫", "bold magenta"),
    "research_agent": ("🔍", "bold cyan"),
    "booking_tools": ("🔧", "bold blue"),
    "research_tools": ("🔧", "bold blue"),
}

COMMANDS = {
    "/help": "Show available commands",
    "/examples": "Show example travel prompts",
    "/trace": "Show the agent trace for the last query",
    "/clear": "Clear conversation history",
    "/exit": "Exit the CLI (also: /quit)",
    "/quit": "Exit the CLI",
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def print_welcome(console: Console) -> None:
    """Print the welcome banner."""
    banner = Text.assemble(
        ("✈️  AI Travel Planner", "bold white"),
        ("\n", ""),
        ("Powered by ", "dim"),
        ("Gemini 3.1 Pro", "bold green"),
        (" · ", "dim"),
        ("LangGraph", "bold blue"),
        (" · ", "dim"),
        ("SerpAPI", "bold yellow"),
        ("\n\n", ""),
        ("Type ", "dim"),
        ("/help", "bold cyan"),
        (" for commands, or just start chatting!", "dim"),
    )
    console.print(Panel(banner, border_style="bright_blue", padding=(1, 2)))
    console.print()


def print_help(console: Console) -> None:
    """Print available commands."""
    lines = "\n".join(
        f"  [bold cyan]{cmd}[/]  —  {desc}"
        for cmd, desc in COMMANDS.items()
        if cmd != "/quit"
    )
    console.print(
        Panel(lines, title="[bold]Commands[/]", border_style="dim", padding=(1, 2))
    )


def format_node_trace(node_name: str) -> str:
    """Format a styled node trace line."""
    icon, style = NODE_STYLES.get(node_name, ("⚙️", "dim"))
    return f"  {icon} [dim]→[/] [{style}]{node_name}[/]"


def format_tool_result(msg: ToolMessage) -> str:
    """Format a condensed tool result."""
    name = msg.name or "tool"
    # Show just the first 120 chars to keep it brief
    content_str = str(msg.content)
    content_preview = (
        (content_str[:120] + "…") if len(content_str) > 120 else content_str
    )
    escaped_preview = content_preview.replace("[", r"\[")
    return f"    [dim]↳ {name}:[/] [dim italic]{escaped_preview}[/]"


def print_response(console: Console, content: str) -> None:
    """Render the AI response as Markdown inside a panel."""
    md = Markdown(content)
    console.print(
        Panel(md, title="[bold green]🤖 Agent[/]", border_style="green", padding=(1, 2))
    )


class SlashCommandCompleter(Completer):
    """Complete commands only when input starts with `/` and contains no spaces."""

    def __init__(self, commands: list[str]) -> None:
        self.word_completer = WordCompleter(commands, ignore_case=True, WORD=True)

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor
        # Only trigger if the input starts with '/' and is a single word
        if text_before_cursor.startswith("/") and " " not in text_before_cursor:
            yield from self.word_completer.get_completions(document, complete_event)


# ── Main Loop ──────────────────────────────────────────────────────────────────
def main() -> None:
    """Run the interactive CLI loop."""
    console = Console()
    messages: list = []
    last_trace: list = []

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI Travel Planner CLI")
    parser.add_argument(
        "--full-logs",
        action="store_true",
        help="Log full tool outputs (default is to hide them)",
    )
    args = parser.parse_args()

    # Initialize session logger
    logger = TravelPlannerLogger(hide_tool_outputs=not args.full_logs)

    print_welcome(console)
    console.print(f"[dim]📝 Session log → {logger.log_path}[/]\n")

    # Build graph
    with console.status("[bold green]Initialising agents…", spinner="dots"):
        graph = build_graph()
    console.print("[green]✓[/] Agents ready!\n")

    # Setup auto-completion
    commands = list(COMMANDS.keys())
    completer = SlashCommandCompleter(commands)

    # Custom style for completion menu: very dim/darker gray text, no background for any item
    custom_style = Style.from_dict(
        {
            "completion-menu": "bg:default",
            "completion-menu.completion": "fg:#666666",
            "completion-menu.completion.current": "bold fg:default bg:black",
            "scrollbar.button": "bg:default",
        }
    )

    session = PromptSession(
        completer=completer, style=custom_style, complete_while_typing=True
    )
    prompt_text = FormattedText([("bold ansibrightblue", "✈️  You ❯ ")])

    while True:
        # ── Input ──────────────────────────────────────────────────────────
        try:
            user_input = session.prompt(prompt_text).strip()
        except KeyboardInterrupt, EOFError:
            console.print("\n[dim]Goodbye! 👋[/]")
            logger.close()
            break

        if not user_input:
            continue

        # ── Commands ───────────────────────────────────────────────────────
        if user_input.lower() in ("/exit", "/quit"):
            console.print("[dim]Goodbye! 👋[/]")
            logger.close()
            break
        if user_input.lower() == "/clear":
            messages.clear()
            logger.log_separator("Conversation cleared")
            console.print("[yellow]🗑  Conversation cleared.[/]\n")
            continue
        if user_input.lower() == "/help":
            print_help(console)
            continue
        if user_input.lower() == "/examples":
            examples_path = Path("backend/prompts/prompt_examples.txt")
            if examples_path.exists():
                valid_examples = [
                    line.strip()
                    for line in examples_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                if not valid_examples:
                    console.print("[red]No examples found.[/]")
                    continue

                dialog_style = Style.from_dict(
                    {
                        "dialog": "bg:default",
                        "dialog frame.label": "bg:default fg:white",
                        "dialog.body": "bg:default fg:white",
                        "dialog shadow": "bg:default",
                        "radio-selected": "fg:cyan bold",
                        "radio-checked": "fg:cyan bold",
                    }
                )

                values = [
                    (ex, ex if len(ex) <= 80 else ex[:77] + "...")
                    for ex in valid_examples
                ]
                
                radio_list = RadioList(values)

                # Custom dialog without buttons for direct enter/escape support
                dialog = Dialog(
                    title="Example Prompts",
                    body=HSplit(
                        [
                            Label(text="Use arrow keys to navigate\nEnter to select, Esc to cancel\n"),
                            radio_list,
                        ],
                        width=D(preferred=80),
                    ),
                    with_background=True,
                )

                kb = KeyBindings()

                @kb.add("enter")
                def _(event):
                    event.app.exit(result=radio_list.current_value)

                @kb.add("escape")
                def _(event):
                    event.app.exit(result=None)

                app = Application(
                    layout=Layout(dialog),
                    key_bindings=kb,
                    mouse_support=True,
                    style=dialog_style,
                    full_screen=True,
                )
                selected = app.run()

                if selected:
                    user_input = selected
                    console.print(f"\n[bold cyan]Running example:[/] {selected}")
                else:
                    continue
            else:
                console.print("[red]Examples file not found.[/]")
                continue
        if user_input.lower() == "/trace":
            if last_trace:
                console.print(Rule("[dim]Agent Trace[/]", style="dim"))
                for line in last_trace:
                    console.print(line)
                console.print(Rule(style="dim"))
            else:
                console.print("[yellow]No trace available from the last query.[/]\n")
            continue

        # ── Run Graph ──────────────────────────────────────────────────────
        console.print()
        messages.append(HumanMessage(content=user_input))

        # Log the user's turn
        logger.log_separator("New Turn")
        logger.log_user(user_input)

        final_ai_content: str | None = None
        last_trace.clear()

        # ── Live working display ───────────────────────────────────────────
        # Tracks all task lines emitted by agents during this turn.
        all_tasks: list[tuple[str, str]] = []  # (agent_label, task_text)

        def _build_live_renderable() -> Group:
            """Build the composite renderable: spinner header + task table."""
            spinner = Spinner('dots', text=Text.assemble(
                ('Working', 'bold green'),
            ))
            if not all_tasks:
                return Group(spinner)

            table = Table.grid(padding=(0, 1))
            table.add_column()                                  # task text
            for _, task_text in all_tasks:
                table.add_row(
                    Text.assemble(('  🔍 ', 'bold yellow'), (task_text, 'white')),
                )
            return Group(spinner, table)

        def _build_done_renderable() -> Panel:
            """Build a static summary panel shown after research completes."""
            table = Table.grid(padding=(0, 1))
            table.add_column()
            for _, task_text in all_tasks:
                table.add_row(
                    Text.assemble(('  ✓ ', 'bold green'), (task_text, 'white')),
                )
            return Panel(
                table,
                title='[bold green]✓ Research Complete[/]',
                border_style='green',
                padding=(0, 1),
            )



        try:
            with Live(
                _build_live_renderable(),
                console=console,
                refresh_per_second=12,
                transient=True,   # erased on stop; we print the static panel ourselves
            ) as live:
                for chunk in graph.stream(
                    cast(Any, {"messages": messages}),
                    stream_mode="updates",
                ):
                    for node_name, node_output in chunk.items():
                        live.update(_build_live_renderable())

                        # Log node execution
                        logger.log_node(node_name)

                        # Collect trace internally instead of printing
                        last_trace.append(format_node_trace(node_name))

                        if not node_output or not isinstance(node_output, dict):
                            continue

                        # Check for messages in the node output
                        node_messages = node_output.get("messages", [])
                        for msg in node_messages:
                            if isinstance(msg, ToolMessage):
                                # Log tool output
                                logger.log_tool_output(msg.name or "tool", msg.content)
                                last_trace.append(format_tool_result(msg))
                            elif isinstance(msg, AIMessage):
                                raw_content = getattr(msg, 'content', '') or ''
                                # Normalize: content can be a list of typed blocks
                                # (e.g. [{"type": "text", "text": "..."}]) when the
                                # model generates tool calls alongside text.
                                if isinstance(raw_content, list):
                                    parts = []
                                    for block in raw_content:
                                        if isinstance(block, dict) and block.get('type') == 'text':
                                            parts.append(block.get('text', ''))
                                        elif isinstance(block, str):
                                            parts.append(block)
                                    content_str = '\n'.join(parts)
                                else:
                                    content_str = str(raw_content)
                                if content_str:
                                    logger.log_ai(content_str)
                                    final_ai_content = content_str

                                    # ── Parse agent signal JSON for tasks ──
                                    # The model emits one or more JSON blobs in its
                                    # content; try to extract them.
                                    raw = content_str.strip()
                                    # Handle case where model concatenates multiple
                                    # JSON objects in one content string (seen in logs)
                                    decoder = json.JSONDecoder()
                                    idx = 0
                                    while idx < len(raw):
                                        start = raw.find('{', idx)
                                        if start == -1:
                                            break
                                        try:
                                            signal, end = decoder.raw_decode(raw, start)
                                            if (
                                                isinstance(signal, dict)
                                                and 'agent' in signal
                                                and 'tasks' in signal
                                                and isinstance(signal['tasks'], list)
                                                # Only capture the first/planning signal
                                                # (not the "status: done" one)
                                                and signal.get('status') != 'done'
                                            ):
                                                agent_label = signal['agent'].replace('_', ' ').title()
                                                for task in signal['tasks']:
                                                    all_tasks.append((agent_label, str(task)))
                                                live.update(_build_live_renderable())
                                            idx = end
                                        except (json.JSONDecodeError, ValueError):
                                            idx = start + 1

                                # Log tool calls embedded in the AIMessage (if any)
                                for tc in getattr(msg, "tool_calls", []) or []:
                                    logger.log_tool_call(
                                        tc.get("name", "unknown"),
                                        tc.get("args"),
                                    )

                            # Append the message to our session history right away
                            messages.append(msg)
        except Exception:  # noqa
            console.print_exception(show_locals=False)
            continue

        # ── Print static task summary (persists after spinner is gone) ─────
        if all_tasks:
            console.print(_build_done_renderable())
            console.print()

        # ── Display Response ───────────────────────────────────────────────
        if final_ai_content:
            print_response(console, final_ai_content)
        else:
            console.print("[yellow]No response from agent. Try rephrasing.[/]")

        console.print()


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
