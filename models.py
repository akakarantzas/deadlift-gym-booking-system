from datetime import datetime
from enum import Enum


class Role(Enum):
    GUEST = "guest"
    USER  = "user"
    ADMIN = "admin"


class SessionStatus(Enum):
    ACTIVE    = "active"
    CANCELLED = "cancelled"


class BookingStatus(Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


# ── User ──────────────────────────────────────────────────────────────────────

class User:
    def __init__(self, user_id, username, password, name, email, role=Role.USER,
                 reset_token=None, reset_token_expiry=None):
        self.user_id             = user_id
        self.username            = username
        self.password            = password   # plain-text (student project scope)
        self.name                = name
        self.email               = email
        self.role                = role
        self.reset_token         = reset_token
        self.reset_token_expiry  = reset_token_expiry

    def to_dict(self):
        return {
            "user_id":             self.user_id,
            "username":            self.username,
            "password":            self.password,
            "name":                self.name,
            "email":               self.email,
            "role":                self.role.value,
            "reset_token":         self.reset_token,
            "reset_token_expiry":  self.reset_token_expiry,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            d["user_id"], d["username"], d["password"],
            d["name"], d["email"], Role(d["role"]),
            d.get("reset_token", None),
            d.get("reset_token_expiry", None),
        )

    def __str__(self):
        return f"{self.name} (@{self.username}) [{self.role.value}]"


# ── Session ───────────────────────────────────────────────────────────────────

class Session:
    def __init__(self, session_id, group_type, trainer, date, time,
                 capacity, duration=60):
        self.session_id  = session_id
        self.group_type  = group_type   # e.g. "Pilates", "Yoga"
        self.trainer     = trainer
        self.date        = date         # "YYYY-MM-DD"
        self.time        = time         # "HH:MM"
        self.capacity    = capacity
        self.duration    = duration     # minutes
        self.status      = SessionStatus.ACTIVE
        self.booked_users = []          # list of user_ids

    @property
    def available_slots(self):
        return self.capacity - len(self.booked_users)

    @property
    def is_full(self):
        return len(self.booked_users) >= self.capacity

    def to_dict(self):
        return {
            "session_id":   self.session_id,
            "group_type":   self.group_type,
            "trainer":      self.trainer,
            "date":         self.date,
            "time":         self.time,
            "capacity":     self.capacity,
            "duration":     self.duration,
            "status":       self.status.value,
            "booked_users": self.booked_users,
        }

    @classmethod
    def from_dict(cls, d):
        s = cls(
            d["session_id"], d["group_type"], d["trainer"],
            d["date"], d["time"], d["capacity"], d.get("duration", 60)
        )
        s.status       = SessionStatus(d["status"])
        s.booked_users = d["booked_users"]
        return s


# ── Booking ───────────────────────────────────────────────────────────────────

class Booking:
    def __init__(self, booking_id, user_id, session_id, booked_at=None):
        self.booking_id = booking_id
        self.user_id    = user_id
        self.session_id = session_id
        self.booked_at  = booked_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.status     = BookingStatus.CONFIRMED

    def to_dict(self):
        return {
            "booking_id": self.booking_id,
            "user_id":    self.user_id,
            "session_id": self.session_id,
            "booked_at":  self.booked_at,
            "status":     self.status.value,
        }

    @classmethod
    def from_dict(cls, d):
        b        = cls(d["booking_id"], d["user_id"], d["session_id"], d["booked_at"])
        b.status = BookingStatus(d["status"])
        return b
