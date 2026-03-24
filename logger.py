"""Observability logger for the AI Travel Planner CLI.

Log files are daily — one file per calendar day, named by date:

    logs/travel_planner_2026-03-19.log

Multiple CLI sessions on the same day all append to the same file,
each delimited by clear session-start / session-end banners:

    ────── Session Started @ 2026-03-19 22:50:10 ──────
    [2026-03-19 22:50:12] USER       : I want to fly to Paris next week …
    [2026-03-19 22:50:13] NODE       : supervisor
    [2026-03-19 22:50:14] TOOL CALL  : search_flights({"origin":"DEL","destination":"CDG"})
    [2026-03-19 22:50:16] TOOL OUTPUT: search_flights → [{"flight":"AI101","price":620}]
    [2026-03-19 22:50:17] AI         : Here are some great flight options …
    ────── Session Ended  @ 2026-03-19 22:51:03 ──────

Logs older than 7 days are automatically deleted on each session start via
`purge_old_logs()`, which can also be called independently.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).parent / 'logs'
_DATE_FMT = '%Y-%m-%d %H:%M:%S'
_FILE_NAME_FMT = 'travel_planner_%Y-%m-%d.log'
_LOG_RETENTION_DAYS = 7

# Tag column width — "TOOL OUTPUT" is the widest at 11 chars
_TAG_WIDTH = 11


# ── Helpers ────────────────────────────────────────────────────────────────────
def _now() -> str:
    """Return the current local timestamp as a formatted string."""
    return datetime.now().strftime(_DATE_FMT)


def _tag(label: str) -> str:
    """Left-justify a label to a fixed width for aligned columns."""
    return label.ljust(_TAG_WIDTH)


def _serialize(obj: Any) -> str:
    """Best-effort serialisation of arbitrary objects to a compact string."""
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError):
        return str(obj)


def _session_banner(label: str) -> str:
    """Build a compact session-boundary banner line.

    Example output:
        ────── Session Started @ 2026-03-19 22:50:10 ──────
    """
    text = f' {label} '
    dash_count = max(0, (54 - len(text)) // 2)
    dashes = '─' * dash_count
    return f'{dashes}{text}{dashes}'


# ── Purge Utility ──────────────────────────────────────────────────────────────
def purge_old_logs(log_dir: Path = _LOG_DIR, retention_days: int = _LOG_RETENTION_DAYS) -> list[Path]:
    """Delete log files older than `retention_days` from `log_dir`.

    Only files matching the daily naming pattern
    ``travel_planner_YYYY-MM-DD.log`` are considered, so other files in the
    directory are left untouched.

    Args:
        log_dir: Directory to scan for log files. Defaults to the project
            ``logs/`` folder.
        retention_days: Files strictly older than this many days are removed.
            Defaults to 7.

    Returns:
        A list of ``Path`` objects for every file that was deleted.
    """
    if not log_dir.exists():
        return []

    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted: list[Path] = []

    for log_file in log_dir.glob('travel_planner_*.log'):
        # Parse the date from the filename (travel_planner_YYYY-MM-DD.log)
        try:
            date_str = log_file.stem.replace('travel_planner_', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            continue  # Skip files that don't match the expected pattern

        if file_date < cutoff:
            try:
                log_file.unlink()
                deleted.append(log_file)
            except OSError:
                pass  # Best-effort — don't crash the app over a stale log

    return deleted


# ── Logger Class ───────────────────────────────────────────────────────────────
class TravelPlannerLogger:
    """Daily file logger for the Travel Planner CLI.

    All sessions on the same calendar day share one log file. Sessions are
    separated by clear start/end banners so individual runs are easy to find.

    Usage::

        logger = TravelPlannerLogger()
        logger.log_user('I want to visit Tokyo.')
        logger.log_tool_call('search_flights', {'origin': 'DEL', 'destination': 'TYO'})
        logger.log_tool_output('search_flights', [{'flight': 'AI301', 'price': 450}])
        logger.log_ai('Here are some great flight options for Tokyo …')
        logger.close()
    """

    def __init__(self, auto_purge: bool = True) -> None:
        """Initialise a new logger session.

        Args:
            auto_purge: If ``True`` (default), logs older than
                ``_LOG_RETENTION_DAYS`` are deleted on startup.
        """
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Purge stale logs before opening today's file
        if auto_purge:
            purge_old_logs()

        # Daily file: travel_planner_YYYY-MM-DD.log (append mode)
        today_filename = datetime.now().strftime(_FILE_NAME_FMT)
        self._log_path = _LOG_DIR / today_filename

        # Use stdlib logging so output is safely buffered and flushed
        # Give the logger a unique name so each session gets its own handler
        session_id = datetime.now().strftime('%H%M%S%f')
        self._logger = logging.getLogger(f'travel_planner.{session_id}')
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False  # Never bubble up to the root logger

        handler = logging.FileHandler(self._log_path, mode='a', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self._logger.addHandler(handler)
        self._handler = handler

        self._write_session_start()

    # ── Internal ───────────────────────────────────────────────────────────────
    def _write_session_start(self) -> None:
        """Write a session-start banner to the log file."""
        # Only add a separator newline if today's log already has content
        if self._log_path.exists() and self._log_path.stat().st_size > 0:
            self._logger.info('')
        self._logger.info(_session_banner('Session Started'))

    def _entry(self, tag: str, message: str) -> None:
        """Write a single timestamped log entry."""
        self._logger.info(f'[{_now()}] {_tag(tag)}: {message}')

    # ── Public API ─────────────────────────────────────────────────────────────
    def log_user(self, content: str) -> None:
        """Log a message sent by the user."""
        self._entry('USER', content)

    def log_ai(self, content: str) -> None:
        """Log a final AI response (collapsed to a single line)."""
        single_line = ' '.join(content.split())
        self._entry('AI', single_line)

    def log_tool_call(self, tool_name: str, args: dict[str, Any] | None = None) -> None:
        """Log an outgoing tool invocation with its arguments."""
        args_str = _serialize(args or {})
        self._entry('TOOL CALL', f'{tool_name}({args_str})')

    def log_tool_output(self, tool_name: str, output: Any) -> None:
        """Log the raw output returned by a tool."""
        output_str = _serialize(output)
        self._entry('TOOL OUTPUT', f'{tool_name} → {output_str}')

    def log_node(self, node_name: str) -> None:
        """Log which graph node is currently executing."""
        self._entry('NODE', node_name)

    def log_separator(self, label: str = '') -> None:
        """Write a visual turn separator (e.g. between conversation turns)."""
        if label:
            line = f'  ── {label} ' + '─' * max(0, 68 - len(label))
        else:
            line = '─' * 80
        self._logger.info(line)

    def close(self) -> None:
        """Write a session-end banner and flush/close the file handler."""
        self._logger.info(_session_banner('Session Ended'))
        self._logger.info('')
        self._handler.flush()
        self._handler.close()
        self._logger.removeHandler(self._handler)

    @property
    def log_path(self) -> Path:
        """Return the absolute path of today's log file."""
        return self._log_path
