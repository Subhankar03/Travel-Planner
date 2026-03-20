"""AI Travel Planner — Rich CLI Interface for testing."""
from __future__ import annotations
import warnings

# Silence Pydantic V1 compatibility warning for Python 3.14
warnings.filterwarnings('ignore', message='.*Pydantic V1 functionality.*')

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from logger import TravelPlannerLogger
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.traceback import install
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from collections.abc import Iterable
from typing import Any, cast

install()

from agent import build_graph


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
    '/trace': 'Show the agent trace for the last query',
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


def format_node_trace(node_name: str) -> str:
    """Format a styled node trace line."""
    icon, style = NODE_STYLES.get(node_name, ('⚙️', 'dim'))
    return f'  {icon} [dim]→[/] [{style}]{node_name}[/]'


def format_tool_result(msg: ToolMessage) -> str:
    """Format a condensed tool result."""
    name = msg.name or 'tool'
    # Show just the first 120 chars to keep it brief
    content_str = str(msg.content)
    content_preview = (content_str[:120] + '…') if len(content_str) > 120 else content_str
    escaped_preview = content_preview.replace('[', r'\[')
    return f'    [dim]↳ {name}:[/] [dim italic]{escaped_preview}[/]'


def print_response(console: Console, content: str) -> None:
    """Render the AI response as Markdown inside a panel."""
    md = Markdown(content)
    console.print(Panel(md, title='[bold green]🤖 Agent[/]', border_style='green', padding=(1, 2)))


class SlashCommandCompleter(Completer):
    """Complete commands only when input starts with `/` and contains no spaces."""
    def __init__(self, commands: list[str]) -> None:
        self.word_completer = WordCompleter(commands, ignore_case=True, WORD=True)

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor
        # Only trigger if the input starts with '/' and is a single word
        if text_before_cursor.startswith('/') and ' ' not in text_before_cursor:
            yield from self.word_completer.get_completions(document, complete_event)


# ── Main Loop ──────────────────────────────────────────────────────────────────
def main() -> None:
    """Run the interactive CLI loop."""
    console = Console()
    messages: list = []
    last_trace: list = []

    # Initialise session logger
    logger = TravelPlannerLogger()

    print_welcome(console)
    console.print(f'[dim]📝 Session log → {logger.log_path}[/]\n')

    # Build graph
    with console.status('[bold green]Initialising agents…', spinner='dots'):
        graph = build_graph()
    console.print('[green]✓[/] Agents ready!\n')

    # Setup auto-completion
    commands = list(COMMANDS.keys())
    completer = SlashCommandCompleter(commands)
    
    # Custom style for completion menu: very dim/darker gray text, no background for any item
    custom_style = Style.from_dict({
        'completion-menu': 'bg:default',
        'completion-menu.completion': 'fg:#666666',
        'completion-menu.completion.current': 'bold fg:default bg:black',
        'scrollbar.button': 'bg:default',
    })
    
    session = PromptSession(
        completer=completer,
        style=custom_style,
        complete_while_typing=True
    )
    prompt_text = FormattedText([('bold ansibrightblue', '✈️  You ❯ ')])

    while True:
        # ── Input ──────────────────────────────────────────────────────────
        try:
            user_input = session.prompt(prompt_text).strip()
        except (KeyboardInterrupt, EOFError):
            console.print('\n[dim]Goodbye! 👋[/]')
            logger.close()
            break

        if not user_input:
            continue

        # ── Commands ───────────────────────────────────────────────────────
        if user_input.lower() in ('/exit', '/quit'):
            console.print('[dim]Goodbye! 👋[/]')
            logger.close()
            break
        if user_input.lower() == '/clear':
            messages.clear()
            logger.log_separator('Conversation cleared')
            console.print('[yellow]🗑  Conversation cleared.[/]\n')
            continue
        if user_input.lower() == '/help':
            print_help(console)
            continue
        if user_input.lower() == '/trace':
            if last_trace:
                console.print(Rule('[dim]Agent Trace[/]', style='dim'))
                for line in last_trace:
                    console.print(line)
                console.print(Rule(style='dim'))
            else:
                console.print('[yellow]No trace available from the last query.[/]\n')
            continue

        # ── Run Graph ──────────────────────────────────────────────────────
        console.print()
        messages.append(HumanMessage(content=user_input))

        # Log the user's turn
        logger.log_separator('New Turn')
        logger.log_user(user_input)

        final_ai_content: str | None = None
        last_trace.clear()

        try:
            with console.status('[bold green]✨ Thinking…', spinner='dots') as status:
                for chunk in graph.stream(
                    cast(Any, {'messages': messages, 'itinerary': None}),
                    stream_mode='updates',
                ):
                    for node_name, node_output in chunk.items():
                        # Update status to show what node is running
                        status.update(f'[bold green]✨ Thinking…[/] [dim](Current: {node_name})[/]')

                        # Log node execution
                        logger.log_node(node_name)

                        # Collect trace internally instead of printing
                        last_trace.append(format_node_trace(node_name))

                        if not node_output or not isinstance(node_output, dict):
                            continue

                        # Check for messages in the node output
                        node_messages = node_output.get('messages', [])
                        for msg in node_messages:
                            if isinstance(msg, ToolMessage):
                                # Log tool output
                                logger.log_tool_output(msg.name or 'tool', msg.content)
                                last_trace.append(format_tool_result(msg))
                            elif isinstance(msg, AIMessage):
                                # Log tool calls embedded in the AIMessage (if any)
                                for tc in getattr(msg, 'tool_calls', []) or []:
                                    logger.log_tool_call(
                                        tc.get('name', 'unknown'),
                                        tc.get('args'),
                                    )
                                if msg.text:
                                    final_ai_content = msg.text
        except Exception:
            console.print_exception(show_locals=False)
            continue

        # ── Display Response ───────────────────────────────────────────────
        if final_ai_content:
            logger.log_ai(final_ai_content)
            print_response(console, final_ai_content)
            messages.append(AIMessage(content=final_ai_content))
        else:
            console.print('[yellow]No response from agent. Try rephrasing.[/]')

        console.print()


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    main()
