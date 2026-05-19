import os

from models import SessionStatus

# ── ANSI colours ─────────────────────────────────────────────────────────────

def _enable_ansi_windows():
    """Enable VT/ANSI escape codes on Windows 10+."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        handle = kernel32.GetStdHandle(-11)
        mode   = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


if os.name == "nt":
    _enable_ansi_windows()

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

LINE = "─" * 78


# ── Header / section helpers ──────────────────────────────────────────────────

def print_header(title):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  DEADLIFT GYM  |  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def print_line():
    print(f"  {DIM}{LINE}{RESET}")


# ── Session display ───────────────────────────────────────────────────────────

def _status_label(session):
    if session.status == SessionStatus.CANCELLED:
        return f"{RED}[CANCELLED]{RESET}"
    if session.is_full:
        return f"{YELLOW}[FULL]{RESET}"
    return f"{GREEN}[{session.available_slots} slot(s) free]{RESET}"


def print_session_row(session, index=None):
    prefix = f"  [{index:>2}] " if index is not None else "       "
    status = _status_label(session)
    print(
        f"{prefix}{BOLD}{session.group_type:<12}{RESET}"
        f"  {session.session_id:<6}"
        f"  {session.date}  {session.time}"
        f"  {session.duration}min"
        f"  Trainer: {session.trainer:<18}"
        f"  Cap: {session.capacity:<4}"
        f"  {status}"
    )


def list_sessions(sessions, title="Sessions", numbered=False):
    print_header(title)
    if not sessions:
        print(f"  {YELLOW}No sessions found.{RESET}\n")
        return
    print(f"  {'#':<5} {'Type':<12}  {'ID':<6}  {'Date':<12}{'Time':<7}"
          f"  {'Dur':<5}  {'Trainer':<20}  {'Cap':<4}  Status")
    print_line()
    for i, s in enumerate(sessions, 1):
        print_session_row(s, i if numbered else None)
    print_line()


# ── Session filtering ─────────────────────────────────────────────────────────

def filter_sessions(db, date_filter=None, group_filter=None):
    results = list(db.sessions.values())
    if date_filter:
        results = [s for s in results if s.date == date_filter]
    if group_filter:
        results = [s for s in results if s.group_type.lower() == group_filter.lower()]
    results.sort(key=lambda s: (s.date, s.time))
    return results
