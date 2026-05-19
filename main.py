"""
Deadlift – Gym Booking System
Console application  |  Python 3.8+
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

import admin as admin_svc
import auth as auth_svc
import booking as booking_svc
from database import Database
from display import (
    BOLD, CYAN, DIM, GREEN, RED, RESET, YELLOW,
    filter_sessions, list_sessions, print_header, print_line,
)
from models import BookingStatus, Role, SessionStatus

GUEST_ONLY_MSG = (
    f"  {YELLOW}You must be logged in to book sessions. "
    f"Please register or log in.{RESET}"
)

# ── Globals ───────────────────────────────────────────────────────────────────

db           = Database()
current_user = None   # None  →  Guest session


# ── Input helpers ─────────────────────────────────────────────────────────────

def prompt(label, required=True, secret=False):
    """Read a string from the user, optionally masking it."""
    while True:
        if secret:
            try:
                import getpass
                val = getpass.getpass(f"  {label}: ")
            except Exception:
                val = input(f"  {label}: ")
        else:
            val = input(f"  {label}: ").strip()
        if val or not required:
            return val
        print(f"  {RED}This field cannot be empty.{RESET}")


def prompt_int(label, min_val=1, max_val=None, allow_zero=False):
    """Read an integer, re-prompting until valid."""
    while True:
        raw = input(f"  {label}: ").strip()
        if allow_zero and raw == "0":
            return 0
        if raw.isdigit():
            n = int(raw)
            if min_val <= n and (max_val is None or n <= max_val):
                return n
        bound = f"1–{max_val}" if max_val else f">= {min_val}"
        print(f"  {RED}Please enter a number ({bound}){' or 0 to go back' if allow_zero else ''}.{RESET}")


def confirm(question):
    """Ask a yes/no question. Returns True for 'y'."""
    ans = input(f"  {question} (y/n): ").strip().lower()
    return ans == "y"


def pause():
    input(f"\n  {DIM}Press Enter to continue…{RESET}")


def show_menu(title, options, back_label="Back / Exit"):
    """
    Display a numbered menu and return the user's choice (1-based).
    Returns 0 when the user selects the back/exit option.
    """
    print_header(title)
    for i, label in enumerate(options, 1):
        print(f"  [{i}] {label}")
    print(f"  [0] {back_label}")
    return prompt_int("Your choice", min_val=1, max_val=len(options), allow_zero=True)


# ── Session browsing (accessible to all roles) ────────────────────────────────

def menu_browse_sessions():
    while True:
        choice = show_menu("Browse Sessions", [
            "View All Sessions",
            "Filter by Date",
            "Filter by Group Type",
        ])
        if choice == 0:
            break

        elif choice == 1:
            sessions = filter_sessions(db)
            list_sessions(sessions, "All Sessions", numbered=False)
            pause()

        elif choice == 2:
            date = prompt("Date (YYYY-MM-DD)")
            sessions = filter_sessions(db, date_filter=date)
            list_sessions(sessions, f"Sessions on {date}", numbered=False)
            pause()

        elif choice == 3:
            groups = sorted(set(s.group_type for s in db.sessions.values()))
            if not groups:
                print(f"  {YELLOW}No groups available.{RESET}")
                pause()
                continue
            print_header("Select Group Type")
            for i, g in enumerate(groups, 1):
                print(f"  [{i}] {g}")
            idx = prompt_int("Choose group", min_val=1, max_val=len(groups))
            group = groups[idx - 1]
            sessions = filter_sessions(db, group_filter=group)
            list_sessions(sessions, f"{group} Sessions", numbered=False)
            pause()


# ── Authentication ────────────────────────────────────────────────────────────

def do_login():
    global current_user
    print_header("Login")
    username = prompt("Username")
    password = prompt("Password", secret=True)

    user = auth_svc.login(db, username, password)
    if user:
        current_user = user
        print(f"\n  {GREEN}Welcome back, {user.name}!"
              f"  (Logged in as: {user.role.value}){RESET}")
    else:
        print(f"\n  {RED}Invalid username or password. Please try again.{RESET}")
    pause()


def do_forgot_password():
    print_header("Forgot Password")
    email = prompt("Enter your account email")
    ok, msg = auth_svc.forgot_password(db, email)
    print(f"\n  {GREEN if ok else RED}{msg}{RESET}")
    if not ok:
        pause()
        return

    token        = prompt("Enter the 6-digit reset token")
    new_password = prompt("Enter your new password", secret=True)
    ok, msg      = auth_svc.reset_password(db, token, new_password)
    print(f"\n  {GREEN if ok else RED}{msg}{RESET}")
    pause()


def do_logout():
    global current_user
    print(f"\n  {CYAN}Goodbye, {current_user.name}! See you at the gym.{RESET}")
    current_user = None
    pause()


# ── Session picker (used in book / reschedule flows) ──────────────────────────

def pick_bookable_session(exclude_session_id=None):
    """
    Let the user pick from bookable (active, not full) sessions.
    Returns a Session or None if the user cancels.
    """
    sessions = [
        s for s in filter_sessions(db)
        if s.status == SessionStatus.ACTIVE
        and not s.is_full
        and s.session_id != exclude_session_id
    ]
    if not sessions:
        print(f"  {YELLOW}No bookable sessions available at the moment.{RESET}")
        return None
    list_sessions(sessions, "Available Sessions", numbered=True)
    idx = prompt_int("Select session number (0 to cancel)",
                     min_val=1, max_val=len(sessions), allow_zero=True)
    if idx == 0:
        return None
    return sessions[idx - 1]


# ── Booking flow ──────────────────────────────────────────────────────────────

def do_book_session():
    print_header("Book a Session")
    session = pick_bookable_session()
    if not session:
        pause()
        return

    print(f"\n  You are about to book:")
    print(f"  {BOLD}{session.group_type}{RESET}"
          f"  |  {session.date}  {session.time}"
          f"  |  Trainer: {session.trainer}")

    if not confirm("Confirm booking?"):
        print(f"  {YELLOW}Booking cancelled.{RESET}")
        pause()
        return

    ok, result = booking_svc.book_session(db, current_user, session)
    if ok:
        print(f"\n  {GREEN}Booking confirmed!  Booking ID: {result.booking_id}{RESET}")
    else:
        print(f"\n  {RED}Could not book session: {result}{RESET}")
    pause()


def do_view_booking_history():
    print_header("My Booking History")
    bookings = booking_svc.get_user_bookings(db, current_user.user_id)
    if not bookings:
        print(f"  {YELLOW}You have no bookings yet.{RESET}")
        pause()
        return

    print(f"  {'ID':<8}  {'Session':<8}  {'Group':<12}  {'Date':<12}"
          f"  {'Time':<6}  {'Status':<12}  Booked At")
    print_line()
    for b in bookings:
        s = db.sessions.get(b.session_id)
        if not s:
            continue
        if b.status == BookingStatus.CONFIRMED:
            st = f"{GREEN}CONFIRMED{RESET}"
        else:
            st = f"{RED}CANCELLED{RESET}"
        print(f"  {b.booking_id:<8}  {s.session_id:<8}  {s.group_type:<12}  "
              f"{s.date:<12}  {s.time:<6}  {st:<20}  {b.booked_at}")
    print_line()
    pause()


def _select_active_booking(action_label):
    """Pick one of the user's confirmed bookings. Returns Booking or None."""
    bookings = booking_svc.get_user_bookings(db, current_user.user_id, active_only=True)
    if not bookings:
        print(f"  {YELLOW}You have no active bookings to {action_label}.{RESET}")
        return None

    print(f"  {'#':<4}  {'Booking ID':<10}  {'Group':<12}  {'Date':<12}  {'Time':<6}")
    print_line()
    for i, b in enumerate(bookings, 1):
        s = db.sessions.get(b.session_id)
        if s:
            print(f"  [{i:>2}]  {b.booking_id:<10}  {s.group_type:<12}  "
                  f"{s.date:<12}  {s.time:<6}")
    print_line()

    idx = prompt_int(f"Select booking to {action_label} (0 to go back)",
                     min_val=1, max_val=len(bookings), allow_zero=True)
    if idx == 0:
        return None
    return bookings[idx - 1]


def do_cancel_booking():
    print_header("Cancel Booking")
    booking = _select_active_booking("cancel")
    if not booking:
        pause()
        return

    s = db.sessions.get(booking.session_id)
    print(f"\n  Cancel: {booking.booking_id}  "
          f"({s.group_type if s else '?'}  {s.date if s else ''}  {s.time if s else ''})")
    if not confirm("Are you sure?"):
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, msg = booking_svc.cancel_booking(db, current_user, booking.booking_id)
    print(f"\n  {GREEN if ok else RED}{msg}{RESET}")
    pause()


def do_reschedule_booking():
    print_header("Reschedule Booking")
    old_booking = _select_active_booking("reschedule")
    if not old_booking:
        pause()
        return

    old_session = db.sessions.get(old_booking.session_id)
    print(f"\n  Current: {old_session.group_type if old_session else '?'}"
          f"  {old_session.date if old_session else ''}  {old_session.time if old_session else ''}")
    print(f"\n  Pick the NEW session:\n")

    new_session = pick_bookable_session(
        exclude_session_id=old_session.session_id if old_session else None
    )
    if not new_session:
        pause()
        return

    print(f"\n  Reschedule to: {BOLD}{new_session.group_type}{RESET}"
          f"  {new_session.date}  {new_session.time}"
          f"  |  Trainer: {new_session.trainer}")
    if not confirm("Confirm reschedule?"):
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, result = booking_svc.reschedule_booking(
        db, current_user, old_booking.booking_id, new_session
    )
    if ok:
        print(f"\n  {GREEN}Rescheduled!  New booking ID: {result.booking_id}{RESET}")
    else:
        print(f"\n  {RED}Reschedule failed: {result}{RESET}")
    pause()


def menu_my_bookings():
    while True:
        choice = show_menu("My Bookings", [
            "View Booking History",
            "Cancel a Booking",
            "Reschedule a Booking",
        ])
        if choice == 0:
            break
        elif choice == 1:
            do_view_booking_history()
        elif choice == 2:
            do_cancel_booking()
        elif choice == 3:
            do_reschedule_booking()


# ── Admin – session management ────────────────────────────────────────────────

def admin_add_session():
    print_header("Add New Session")
    group_type = prompt("Group type (e.g. Pilates, Yoga, CrossFit)")
    trainer    = prompt("Trainer name")
    date       = prompt("Date (YYYY-MM-DD)")
    time       = prompt("Start time (HH:MM)")
    cap_str    = prompt("Capacity")
    dur_str    = prompt("Duration in minutes", required=False) or "60"

    if not cap_str.isdigit() or not dur_str.isdigit():
        print(f"  {RED}Capacity and duration must be whole numbers.{RESET}")
        pause()
        return

    session = admin_svc.add_session(
        db, group_type, trainer, date, time, int(cap_str), int(dur_str)
    )
    print(f"\n  {GREEN}Session {session.session_id} added successfully.{RESET}")
    pause()


def admin_edit_session():
    print_header("Edit Session")
    sessions = list(db.sessions.values())
    sessions.sort(key=lambda s: (s.date, s.time))
    list_sessions(sessions, "All Sessions", numbered=True)

    idx = prompt_int("Select session number (0 to go back)",
                     min_val=1, max_val=len(sessions), allow_zero=True)
    if idx == 0:
        return

    s = sessions[idx - 1]
    print(f"\n  Editing {s.session_id} – {s.group_type}. Leave blank to keep current value.\n")

    fields_meta = [
        ("group_type", "Group type",          str,  None),
        ("trainer",    "Trainer",             str,  None),
        ("date",       "Date (YYYY-MM-DD)",   str,  None),
        ("time",       "Start time (HH:MM)",  str,  None),
        ("capacity",   "Capacity",            int,  None),
        ("duration",   "Duration (min)",      int,  None),
    ]
    updates = {}
    for field, label, cast, _ in fields_meta:
        current = getattr(s, field)
        raw = input(f"  {label} [{current}]: ").strip()
        if not raw:
            continue
        if cast == int and not raw.isdigit():
            print(f"  {YELLOW}Invalid number for '{field}', skipped.{RESET}")
            continue
        updates[field] = cast(raw)

    if not updates:
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, result = admin_svc.edit_session(db, s.session_id, **updates)
    print(f"\n  {GREEN}Session updated.{RESET}" if ok else f"\n  {RED}{result}{RESET}")
    pause()


def admin_remove_session():
    print_header("Remove (Cancel) Session")
    active = [s for s in db.sessions.values() if s.status == SessionStatus.ACTIVE]
    if not active:
        print(f"  {YELLOW}No active sessions to remove.{RESET}")
        pause()
        return

    active.sort(key=lambda s: (s.date, s.time))
    list_sessions(active, "Active Sessions", numbered=True)

    idx = prompt_int("Select session to cancel (0 to go back)",
                     min_val=1, max_val=len(active), allow_zero=True)
    if idx == 0:
        return

    s = active[idx - 1]
    if not confirm(f"Cancel '{s.group_type}' on {s.date} at {s.time}?"):
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, msg = admin_svc.remove_session(db, s.session_id)
    print(f"\n  {GREEN if ok else RED}{msg}{RESET}")
    pause()


def menu_manage_sessions():
    while True:
        choice = show_menu("Manage Sessions", [
            "Add Session",
            "Edit Session",
            "Remove (Cancel) Session",
        ])
        if choice == 0:
            break
        elif choice == 1:
            admin_add_session()
        elif choice == 2:
            admin_edit_session()
        elif choice == 3:
            admin_remove_session()


# ── Admin – user management ───────────────────────────────────────────────────

def admin_list_users():
    print_header("All Users")
    users = list(db.users.values())
    print(f"  {'ID':<8}  {'Username':<15}  {'Name':<25}  {'Email':<30}  Role")
    print_line()
    for u in users:
        print(f"  {u.user_id:<8}  {u.username:<15}  {u.name:<25}  {u.email:<30}  {u.role.value}")
    print_line()
    pause()


def admin_add_user():
    print_header("Add User")
    username = prompt("Username")
    password = prompt("Password")
    name     = prompt("Full name")
    email    = prompt("Email")

    print(f"  Roles: [1] user  [2] admin")
    role_idx = prompt_int("Role", min_val=1, max_val=2)
    role = Role.USER if role_idx == 1 else Role.ADMIN

    ok, result = admin_svc.add_user(db, username, password, name, email, role)
    if ok:
        print(f"\n  {GREEN}User {result.user_id} ({result.username}) added.{RESET}")
    else:
        print(f"\n  {RED}{result}{RESET}")
    pause()


def admin_edit_user():
    print_header("Edit User")
    users = list(db.users.values())
    print(f"  {'#':<4}  {'ID':<8}  {'Username':<15}  {'Name':<25}  Role")
    print_line()
    for i, u in enumerate(users, 1):
        print(f"  [{i:>2}]  {u.user_id:<8}  {u.username:<15}  {u.name:<25}  {u.role.value}")
    print_line()

    idx = prompt_int("Select user to edit (0 to go back)",
                     min_val=1, max_val=len(users), allow_zero=True)
    if idx == 0:
        return

    u = users[idx - 1]
    print(f"\n  Editing {u.username}. Leave blank to keep current value.\n")

    updates = {}
    for field, label in [("name", "Full name"), ("email", "Email"), ("password", "Password")]:
        raw = input(f"  {label} [{getattr(u, field)}]: ").strip()
        if raw:
            updates[field] = raw

    if not updates:
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, result = admin_svc.edit_user(db, u.user_id, **updates)
    print(f"\n  {GREEN}User updated.{RESET}" if ok else f"\n  {RED}{result}{RESET}")
    pause()


def admin_delete_user():
    print_header("Delete User")
    # Prevent admin from deleting their own account
    others = [u for u in db.users.values() if u.user_id != current_user.user_id]
    if not others:
        print(f"  {YELLOW}No other users to delete.{RESET}")
        pause()
        return

    print(f"  {'#':<4}  {'ID':<8}  {'Username':<15}  {'Name':<25}  Role")
    print_line()
    for i, u in enumerate(others, 1):
        print(f"  [{i:>2}]  {u.user_id:<8}  {u.username:<15}  {u.name:<25}  {u.role.value}")
    print_line()

    idx = prompt_int("Select user to delete (0 to go back)",
                     min_val=1, max_val=len(others), allow_zero=True)
    if idx == 0:
        return

    u = others[idx - 1]
    if not confirm(f"Permanently delete '{u.username}' ({u.name})?"):
        print(f"  {YELLOW}No changes made.{RESET}")
        pause()
        return

    ok, msg = admin_svc.delete_user(db, u.user_id)
    print(f"\n  {GREEN if ok else RED}{msg}{RESET}")
    pause()


def menu_manage_users():
    while True:
        choice = show_menu("Manage Users", [
            "View All Users",
            "Add User",
            "Edit User",
            "Delete User",
        ])
        if choice == 0:
            break
        elif choice == 1:
            admin_list_users()
        elif choice == 2:
            admin_add_user()
        elif choice == 3:
            admin_edit_user()
        elif choice == 4:
            admin_delete_user()


def admin_view_all_bookings():
    print_header("All Bookings")
    bookings = list(db.bookings.values())
    if not bookings:
        print(f"  {YELLOW}No bookings in the system yet.{RESET}")
        pause()
        return

    bookings.sort(key=lambda b: b.booked_at, reverse=True)
    print(f"  {'Booking':<10}  {'User':<14}  {'Session':<8}  {'Group':<12}"
          f"  {'Date':<12}  {'Time':<6}  Status")
    print_line()
    for b in bookings:
        u = db.users.get(b.user_id)
        s = db.sessions.get(b.session_id)
        uname = u.username if u else b.user_id
        if b.status == BookingStatus.CONFIRMED:
            st = f"{GREEN}CONFIRMED{RESET}"
        else:
            st = f"{RED}CANCELLED{RESET}"
        if s:
            print(f"  {b.booking_id:<10}  {uname:<14}  {s.session_id:<8}"
                  f"  {s.group_type:<12}  {s.date:<12}  {s.time:<6}  {st}")
    print_line()
    pause()


# ── Top-level menus ───────────────────────────────────────────────────────────

def menu_guest():
    choice = show_menu("Guest Menu", [
        "Browse Sessions",
        "Login",
        "Forgot Password",
        "Continue as Guest",
    ], back_label="Exit")
    return choice   # caller handles routing


def menu_guest_user():
    choice = show_menu("Guest Menu", [
        "Browse Sessions",
    ], back_label="Exit")
    return choice


def menu_user():
    choice = show_menu(f"User Menu  ({current_user.name})", [
        "Browse Sessions",
        "Book a Session",
        "My Bookings",
        "Logout",
    ], back_label="Exit")
    return choice


def menu_admin():
    choice = show_menu(f"Admin Panel  ({current_user.name})", [
        "Browse Sessions",
        "Manage Sessions",
        "Manage Users",
        "View All Bookings",
        "Logout",
    ], back_label="Exit")
    return choice


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    global current_user
    print(f"\n{BOLD}{CYAN}"
          f"  ██████╗ ███████╗ █████╗ ██████╗ ██╗     ██╗███████╗████████╗\n"
          f"  ██╔══██╗██╔════╝██╔══██╗██╔══██╗██║     ██║██╔════╝╚══██╔══╝\n"
          f"  ██║  ██║█████╗  ███████║██║  ██║██║     ██║█████╗     ██║   \n"
          f"  ██║  ██║██╔══╝  ██╔══██║██║  ██║██║     ██║██╔══╝     ██║   \n"
          f"  ██████╔╝███████╗██║  ██║██████╔╝███████╗██║██║        ██║   \n"
          f"  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝   \n"
          f"{RESET}")
    print(f"  {DIM}Gym Booking System  |  The American College of Greece{RESET}")
    print(f"  {DIM}Lifted by: Apostolos Kakarantzas, Erina Hoxha, Angelos Markopoulos{RESET}\n")

    while True:
        # ── Not logged in ──────────────────────────────────────────────────
        if current_user is None:
            choice = menu_guest()
            if choice == 0:
                print(f"\n  {CYAN}Thank you for visiting Deadlift. Goodbye!{RESET}\n")
                sys.exit(0)
            elif choice == 1:
                menu_browse_sessions()
            elif choice == 2:
                do_login()
            elif choice == 3:
                do_forgot_password()
            elif choice == 4:
                current_user = auth_svc.guest_login()

        # ── Logged-in Guest (browse only) ───────────────────────────────────
        elif current_user.role == Role.GUEST:
            choice = menu_guest_user()
            if choice == 0:
                print(f"\n  {CYAN}Thank you for visiting Deadlift. Goodbye!{RESET}\n")
                sys.exit(0)
            elif choice == 1:
                menu_browse_sessions()

        # ── Admin ──────────────────────────────────────────────────────────
        elif current_user.role == Role.ADMIN:
            choice = menu_admin()
            if choice == 0:
                print(f"\n  {CYAN}Thank you for visiting Deadlift. Goodbye!{RESET}\n")
                sys.exit(0)
            elif choice == 1:
                menu_browse_sessions()
            elif choice == 2:
                menu_manage_sessions()
            elif choice == 3:
                menu_manage_users()
            elif choice == 4:
                admin_view_all_bookings()
            elif choice == 5:
                do_logout()

        # ── Registered User ────────────────────────────────────────────────
        else:
            choice = menu_user()
            if choice == 0:
                print(f"\n  {CYAN}Thank you for visiting Deadlift. Goodbye!{RESET}\n")
                sys.exit(0)
            elif choice == 1:
                menu_browse_sessions()
            elif choice == 2:
                do_book_session()
            elif choice == 3:
                menu_my_bookings()
            elif choice == 4:
                do_logout()


if __name__ == "__main__":
    main()
