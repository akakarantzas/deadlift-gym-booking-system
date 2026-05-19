from models import Booking, BookingStatus, SessionStatus


# ── Queries ───────────────────────────────────────────────────────────────────

def get_user_bookings(db, user_id, active_only=False):
    """Return bookings for a user, newest first."""
    result = [b for b in db.bookings.values() if b.user_id == user_id]
    if active_only:
        result = [b for b in result if b.status == BookingStatus.CONFIRMED]
    return sorted(result, key=lambda b: b.booked_at, reverse=True)


def _has_time_conflict(db, user_id, session, exclude_booking_id=None):
    """True if the user already has a confirmed booking at the same date+time."""
    for b in db.bookings.values():
        if b.user_id != user_id:
            continue
        if b.status == BookingStatus.CANCELLED:
            continue
        if b.booking_id == exclude_booking_id:
            continue
        s = db.sessions.get(b.session_id)
        if s and s.date == session.date and s.time == session.time:
            return True, s
    return False, None


# ── Core operations ───────────────────────────────────────────────────────────

def book_session(db, user, session):
    """
    Reserve a spot for the user in the given session.
    Returns (True, Booking) or (False, error_message).
    """
    if session.status == SessionStatus.CANCELLED:
        return False, "This session has been cancelled."
    if session.is_full:
        return False, "This session is fully booked."
    if user.user_id in session.booked_users:
        return False, "You are already booked into this session."

    conflict, other = _has_time_conflict(db, user.user_id, session)
    if conflict:
        return False, (f"You already have a booking at this time "
                       f"({other.group_type} on {other.date}).")

    bid     = db.new_booking_id()
    booking = Booking(bid, user.user_id, session.session_id)
    db.bookings[bid] = booking
    session.booked_users.append(user.user_id)
    db.save()
    return True, booking


def cancel_booking(db, user, booking_id):
    """
    Cancel a confirmed booking.
    Returns (True, message) or (False, error_message).
    """
    booking = db.bookings.get(booking_id)
    if not booking:
        return False, "Booking not found."
    if booking.user_id != user.user_id:
        return False, "This booking does not belong to you."
    if booking.status == BookingStatus.CANCELLED:
        return False, "This booking is already cancelled."

    booking.status = BookingStatus.CANCELLED
    session = db.sessions.get(booking.session_id)
    if session and user.user_id in session.booked_users:
        session.booked_users.remove(user.user_id)
    db.save()
    return True, f"Booking {booking_id} cancelled successfully."


def reschedule_booking(db, user, old_booking_id, new_session):
    """
    Move an existing booking to a different session.
    The old booking is cancelled only after the new one succeeds.
    Returns (True, new_Booking) or (False, error_message).
    """
    old_booking = db.bookings.get(old_booking_id)
    if not old_booking:
        return False, "Booking not found."
    if old_booking.user_id != user.user_id:
        return False, "This booking does not belong to you."
    if old_booking.status == BookingStatus.CANCELLED:
        return False, "This booking is already cancelled."

    old_session = db.sessions.get(old_booking.session_id)

    # Temporarily remove from old booking so time-conflict check works
    # when rescheduling to a session at the same time slot.
    old_booking.status = BookingStatus.CANCELLED
    if old_session and user.user_id in old_session.booked_users:
        old_session.booked_users.remove(user.user_id)

    ok, result = book_session(db, user, new_session)
    if not ok:
        # Rollback the temporary cancellation
        old_booking.status = BookingStatus.CONFIRMED
        if old_session:
            old_session.booked_users.append(user.user_id)
        return False, result

    db.save()
    return True, result
