from models import Role, Session, SessionStatus, User


# ── Session management ────────────────────────────────────────────────────────

def add_session(db, group_type, trainer, date, time, capacity, duration=60):
    """Create and store a new session. Returns the Session object."""
    sid     = db.new_session_id()
    session = Session(sid, group_type, trainer, date, time, capacity, duration)
    db.sessions[sid] = session
    db.save()
    return session


def edit_session(db, session_id, **fields):
    """
    Update allowed fields of an existing session.
    Returns (True, session) or (False, error_message).
    """
    session = db.sessions.get(session_id)
    if not session:
        return False, f"Session '{session_id}' not found."

    allowed = {"group_type", "trainer", "date", "time", "capacity", "duration"}
    for key, val in fields.items():
        if key in allowed:
            setattr(session, key, val)

    db.save()
    return True, session


def remove_session(db, session_id):
    """
    Mark a session as cancelled (soft delete).
    Returns (True, message) or (False, error_message).
    """
    session = db.sessions.get(session_id)
    if not session:
        return False, f"Session '{session_id}' not found."
    if session.status == SessionStatus.CANCELLED:
        return False, "Session is already cancelled."

    session.status = SessionStatus.CANCELLED
    db.save()
    return True, f"Session {session_id} ({session.group_type}) has been cancelled."


# ── User management ───────────────────────────────────────────────────────────

def add_user(db, username, password, name, email, role=Role.USER):
    """
    Create a new user account.
    Returns (True, User) or (False, error_message).
    """
    if any(u.username == username for u in db.users.values()):
        return False, f"Username '{username}' is already taken."

    uid  = db.new_user_id()
    user = User(uid, username, password, name, email, role)
    db.users[uid] = user
    db.save()
    return True, user


def edit_user(db, user_id, **fields):
    """
    Update allowed fields of an existing user.
    Returns (True, user) or (False, error_message).
    """
    user = db.users.get(user_id)
    if not user:
        return False, f"User '{user_id}' not found."

    allowed = {"username", "password", "name", "email", "role"}
    for key, val in fields.items():
        if key in allowed:
            setattr(user, key, val)

    db.save()
    return True, user


def delete_user(db, user_id):
    """
    Permanently remove a user account.
    Returns (True, message) or (False, error_message).
    """
    if user_id not in db.users:
        return False, f"User '{user_id}' not found."

    username = db.users[user_id].username
    del db.users[user_id]
    db.save()
    return True, f"User '{username}' deleted successfully."
