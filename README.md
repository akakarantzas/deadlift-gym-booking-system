# Deadlift - Gym Booking System

Deadlift is a Python console application for managing gym class bookings. Members can browse sessions, book classes, cancel bookings, and reschedule. Admins can manage sessions, users, and booking records.

<p align="center">
  <img src="./src/deadlift_logo.png" alt="Terrasset Hero Banner" width="100%">
</p>

## Features

- Browse and filter gym sessions
- Log in as admin, user, or guest
- Book, cancel, and reschedule sessions
- Manage users and sessions as an admin
- Save data locally in `gym_data.json`

## Requirements

- Python 3.8+

## Run

```bash
python main.py
```

## Demo Accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `john_d` | `hunter99` | User |
| `e_hoxha` | `pass123` | User |
| `e_vagianou` | `pass123` | User |
| `a_markopoulos` | `pass123` | User |

## Project Structure

```text
main.py        # Menus and application flow
models.py      # User, Session, and Booking classes
database.py    # JSON loading, saving, and seed data
auth.py        # Login, guest access, and password reset
booking.py     # Booking, cancellation, and rescheduling
admin.py       # Admin session and user management
display.py     # Terminal output and session filtering
gym_data.json  # Saved application data
```

## Notes

This project uses plain-text passwords because it was built as a course-level console application, not a production system. A real deployment would require password hashing, input validation, and a proper database.
