"""AI Travel Planner — Rich CLI Interface for testing."""
from __future__ import annotations
import warnings

# Silence Pydantic V1 compatibility warning for Python 3.14
warnings.filterwarnings('ignore', message='.*Pydantic V1 functionality.*')

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.traceback import install

install()

from graph import build_graph

# ── Constants ──────────────────────────────────────────────────────────────────
NODE_STYLES = {
    'supervisor': ('🧭', 'bold yellow'),
    'booking_agent': ('🛫', 'bold magenta'),
    'research_agent': ('🔍', 'bold cyan'),
    'booking_tools': ('🔧', 'bold blue'),
    'research_tools': ('🔧', 'bold blue'),
}

COMMANDS = {
    '/help': 'Show available commands',
    '/clear': 'Clear conversation history',
    '/exit': 'Exit the CLI (also: /quit)',
    '/quit': 'Exit the CLI',
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def print_welcome(console: Console) -> None:
    """Print the welcome banner."""
    banner = Text.assemble(
        ('✈️  AI Travel Planner', 'bold white'),
        ('\n', ''),
        ('Powered by ', 'dim'),
        ('Gemini 3.1 Pro', 'bold green'),
        (' · ', 'dim'),
        ('LangGraph', 'bold blue'),
        (' · ', 'dim'),
        ('SerpAPI', 'bold yellow'),
        ('\n\n', ''),
        ('Type ', 'dim'),
        ('/help', 'bold cyan'),
        (' for commands, or just start chatting!', 'dim'),
    )
    console.print(Panel(banner, border_style='bright_blue', padding=(1, 2)))
    console.print()


def print_help(console: Console) -> None:
    """Print available commands."""
    lines = '\n'.join(f'  [bold cyan]{cmd}[/]  —  {desc}' for cmd, desc in COMMANDS.items() if cmd != '/quit')
    console.print(Panel(lines, title='[bold]Commands[/]', border_style='dim', padding=(1, 2)))


def print_node_trace(console: Console, node_name: str) -> None:
    """Print a styled node trace line."""
    icon, style = NODE_STYLES.get(node_name, ('⚙️', 'dim'))
    console.print(f'  {icon} [dim]→[/] [{style}]{node_name}[/]')


def print_tool_result(console: Console, msg: ToolMessage) -> None:
    """Print a condensed tool result."""
    name = msg.name or 'tool'
    # Show just the first 120 chars to keep it brief
    content_preview = (msg.content[:120] + '…') if len(msg.content) > 120 else msg.content
    console.print(f'    [dim]↳ {name}:[/] [dim italic]{content_preview}[/]')


def print_response(console: Console, content: str) -> None:
    """Render the AI response as Markdown inside a panel."""
    md = Markdown(content)
    console.print(Panel(md, title='[bold green]🤖 Agent[/]', border_style='green', padding=(1, 2)))


# ── Main Loop ──────────────────────────────────────────────────────────────────
def main() -> None:
    """Run the interactive CLI loop."""
    console = Console()
    messages: list = []

    print_welcome(console)

    # Build graph
    with console.status('[bold green]Initialising agents…', spinner='dots'):
        graph = build_graph()
    console.print('[green]✓[/] Agents ready!\n')

    while True:
        # ── Input ──────────────────────────────────────────────────────────
        try:
            user_input = console.input('[bold bright_blue]✈️  You ❯ [/]').strip()
        except (KeyboardInterrupt, EOFError):
            console.print('\n[dim]Goodbye! 👋[/]')
            break

        if not user_input:
            continue

        # ── Commands ───────────────────────────────────────────────────────
        if user_input.lower() in ('/exit', '/quit'):
            console.print('[dim]Goodbye! 👋[/]')
            break
        if user_input.lower() == '/clear':
            messages.clear()
            console.print('[yellow]🗑  Conversation cleared.[/]\n')
            continue
        if user_input.lower() == '/help':
            print_help(console)
            continue

        # ── Run Graph ──────────────────────────────────────────────────────
        console.print()
        messages.append(HumanMessage(content=user_input))

        console.print(Rule('[dim]Agent Trace[/]', style='dim'))

        final_ai_content: str | None = None

        try:
            with console.status('[bold green]✨ Thinking…', spinner='dots'):
                for chunk in graph.stream(
                    {'messages': messages, 'itinerary': None},
                    stream_mode='updates',
                ):
                    for node_name, node_output in chunk.items():
                        # Print which node is running
                        console.print_json  # no-op, just to break spinner
                        print_node_trace(console, node_name)

                        if not node_output or not isinstance(node_output, dict):
                            continue

                        # Check for messages in the node output
                        node_messages = node_output.get('messages', [])
                        for msg in node_messages:
                            if isinstance(msg, ToolMessage):
                                print_tool_result(console, msg)
                            elif isinstance(msg, AIMessage) and msg.text:
                                final_ai_content = msg.text
        except Exception:
            console.print_exception(show_locals=False)
            console.print(Rule(style='dim'))
            continue

        console.print(Rule(style='dim'))

        # ── Display Response ───────────────────────────────────────────────
        if final_ai_content:
            print_response(console, final_ai_content)
            messages.append(AIMessage(content=final_ai_content))
        else:
            console.print('[yellow]No response from agent. Try rephrasing.[/]')

        console.print()


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    main()
