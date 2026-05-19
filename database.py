import json
import os

from models import Booking, BookingStatus, Role, Session, SessionStatus, User

DATA_FILE = os.path.join(os.path.dirname(__file__), "gym_data.json")


class Database:
    def __init__(self):
        self.users    = {}   # user_id    -> User
        self.sessions = {}   # session_id -> Session
        self.bookings = {}   # booking_id -> Booking

        self._user_ctr    = 1
        self._session_ctr = 1
        self._booking_ctr = 1

        if os.path.exists(DATA_FILE):
            self.load()
        else:
            self._seed()
            self.save()

    #  ID generators

    def new_user_id(self):
        uid = f"U{self._user_ctr:03d}"
        self._user_ctr += 1
        return uid

    def new_session_id(self):
        sid = f"S{self._session_ctr:03d}"
        self._session_ctr += 1
        return sid

    def new_booking_id(self):
        bid = f"B{self._booking_ctr:03d}"
        self._booking_ctr += 1
        return bid

    #  Persistence 

    def save(self):
        data = {
            "counters": {
                "user":    self._user_ctr,
                "session": self._session_ctr,
                "booking": self._booking_ctr,
            },
            "users":    {k: v.to_dict() for k, v in self.users.items()},
            "sessions": {k: v.to_dict() for k, v in self.sessions.items()},
            "bookings": {k: v.to_dict() for k, v in self.bookings.items()},
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        c = data.get("counters", {})
        self._user_ctr    = c.get("user",    1)
        self._session_ctr = c.get("session", 1)
        self._booking_ctr = c.get("booking", 1)

        self.users    = {k: User.from_dict(v)    for k, v in data.get("users",    {}).items()}
        self.sessions = {k: Session.from_dict(v) for k, v in data.get("sessions", {}).items()}
        self.bookings = {k: Booking.from_dict(v) for k, v in data.get("bookings", {}).items()}

    #  Seed data 

    def _seed(self):
        # Admin account
        self.users["U001"] = User("U001", "admin", "admin123",
                                  "Administrator", "admin@deadlift.gr", Role.ADMIN)
        # Regular members
        members = [
            ("U002", "john_d",   "pass123", "John Doe",             "john@email.com"),
            ("U003", "e_hoxha",   "pass123", "Erina Hoxha",           "e.hoxha@email.com"),
            ("U004", "e_vagianou", "pass123", "Evgenia Vagianou",   "e.vagianou@email.com"),
            ("U005", "a_markopoulos",  "pass123", "Angelos Markopoulos",     "a.markopoulos@email.com"),
        ]
        for uid, uname, pw, name, email in members:
            self.users[uid] = User(uid, uname, pw, name, email, Role.USER)
        self._user_ctr = 6

        # Sessions  (dates relative to current project start: April 2026)
        sessions_data = [
            ("S001", "Pilates",  "Coach Elena", "2026-04-08", "09:00", 10, 60),
            ("S002", "Yoga",     "Coach Maria", "2026-04-08", "11:00", 15, 60),
            ("S003", "CrossFit", "Coach Alex",  "2026-04-09", "10:00",  8, 45),
            ("S004", "Pilates",  "Coach Elena", "2026-04-09", "17:00", 10, 60),
            ("S005", "Yoga",     "Coach Maria", "2026-04-10", "09:00", 15, 60),
            ("S006", "Spinning", "Coach Nikos", "2026-04-10", "18:00", 12, 45),
            ("S007", "Pilates",  "Coach Elena", "2026-04-11", "09:00", 10, 60),
            ("S008", "CrossFit", "Coach Alex",  "2026-04-11", "17:00",  8, 45),
            ("S009", "Yoga",     "Coach Maria", "2026-04-12", "11:00", 15, 60),
            ("S010", "Spinning", "Coach Nikos", "2026-04-12", "18:00", 12, 45),
        ]
        for sid, gtype, trainer, date, time, cap, dur in sessions_data:
            self.sessions[sid] = Session(sid, gtype, trainer, date, time, cap, dur)
        self._session_ctr = 11

        # One cancelled session
        self.sessions["S003"].status = SessionStatus.CANCELLED

        # One fully booked session (S006 – Spinning, capacity 12)
        for i in range(12):
            self.sessions["S006"].booked_users.append(f"EXT{i:02d}")

        # Pre-existing bookings for john_d (U002)
        for sid in ["S001", "S002"]:
            bid = self.new_booking_id()
            self.bookings[bid] = Booking(bid, "U002", sid, "2026-04-07 08:00")
            self.sessions[sid].booked_users.append("U002")

        # Pre-existing booking for mary_s (U003)
        bid = self.new_booking_id()
        self.bookings[bid] = Booking(bid, "U003", "S004", "2026-04-07 09:00")
        self.sessions["S004"].booked_users.append("U003")
