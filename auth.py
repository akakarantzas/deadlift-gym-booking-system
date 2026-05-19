import secrets
from datetime import datetime, timedelta

from models import Role, User


def login(db, username, password):
    """Return the matching User, or None if credentials are invalid."""
    for user in db.users.values():
        if user.username == username and user.password == password:
            return user
    return None


def require_role(user, *roles):
    """Return True if the user has one of the given roles."""
    return user is not None and user.role in roles


def is_admin(user):
    return require_role(user, Role.ADMIN)


def is_registered(user):
    return require_role(user, Role.USER, Role.ADMIN)


def is_guest(user):
    return require_role(user, Role.GUEST)


def guest_login():
    """Return a Guest User object (not stored in db) for browse-only access."""
    return User("GUEST", "guest", "", "Guest", "", Role.GUEST)


def forgot_password(db, email):
    """
    Find user by email, generate a 6-digit token with a 1-hour expiry.
    Prints the token to console (simulates email delivery).
    Returns (True, message) or (False, error_message).
    """
    user = next((u for u in db.users.values() if u.email == email), None)
    if not user:
        return False, "No account found with that email address."

    token  = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")

    user.reset_token        = token
    user.reset_token_expiry = expiry
    db.save()

    print(f"\n  Reset token for {email}: {token}")
    return True, "A reset token has been generated. Check the console output above."


def reset_password(db, token, new_password):
    """
    Find user by reset_token, verify it has not expired, set the new password,
    and clear the token fields.
    Returns (True, message) or (False, error_message).
    """
    user = next(
        (u for u in db.users.values() if u.reset_token == token),
        None,
    )
    if not user:
        return False, "Invalid reset token."

    if datetime.now() > datetime.strptime(user.reset_token_expiry, "%Y-%m-%d %H:%M"):
        return False, "Reset token has expired. Please request a new one."

    user.password            = new_password
    user.reset_token         = None
    user.reset_token_expiry  = None
    db.save()

    return True, "Password reset successfully. You can now log in."
