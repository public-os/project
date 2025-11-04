import uuid
import sqlite3
from datetime import datetime
import json

# Connect to (or create) a local database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Enable foreign key constraints in SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# --- Create Tables ---

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT,
    plan TEXT DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Devices table (linked to users)
cursor.execute("""
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT,
    type TEXT CHECK (type IN ('desktop', 'chrome_ext')),
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# Sessions table (linked to users and devices)
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    start_ts TIMESTAMP,
    end_ts TIMESTAMP,
    productive BOOLEAN,
    productivity_score REAL CHECK (productivity_score >= 0 AND productivity_score <= 100),
    tags TEXT, -- JSON array or comma-separated tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
""")

# App usage table (linked to sessions)
cursor.execute("""
CREATE TABLE IF NOT EXISTS app_usage (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP,
    category TEXT, -- e.g. 'Work', 'Entertainment'
    activity TEXT, -- e.g. 'chrome.exe', 'code.exe', or a URL
    duration_ms INTEGER,
    productivity_label TEXT CHECK (productivity_label IN ('productive', 'neutral', 'distracting')),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
""")

# Productivity Reports table (linked to users)
cursor.execute("""
CREATE TABLE IF NOT EXISTS productivity_reports (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    focus_minutes INTEGER DEFAULT 0,
    distraction_minutes INTEGER DEFAULT 0,
    productivity_score REAL CHECK (productivity_score >= 0 AND productivity_score <= 100),
    ai_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# Teams table
cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# Team members table
cursor.execute("""
CREATE TABLE IF NOT EXISTS team_members (
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT CHECK (role IN ('owner', 'admin', 'member')) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id),
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

conn.commit()

# --- Example Functions ---

def add_user(email, password_hash=None, full_name=None, plan="free"):
    """Add a new user to the database."""
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, plan, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, email, password_hash, full_name, plan, created_at))
    conn.commit()
    print(f"User {email} added with id {user_id}")
    return user_id


def add_device(user_id, name, device_type):
    """Add a device for a given user."""
    device_id = str(uuid.uuid4())
    last_seen = datetime.now()
    cursor.execute("""
        INSERT INTO devices (id, user_id, name, type, last_seen)
        VALUES (?, ?, ?, ?, ?)
    """, (device_id, user_id, name, device_type, last_seen))
    conn.commit()
    print(f"Device '{name}' added for user {user_id}")
    return device_id


def add_session(user_id, device_id, start_ts, end_ts, productive, productivity_score, tags=None):
    """Add a session entry for a user and device."""
    session_id = str(uuid.uuid4())
    created_at = datetime.now()
    if isinstance(tags, list):
        tags = json.dumps(tags)
    cursor.execute("""
        INSERT INTO sessions (id, user_id, device_id, start_ts, end_ts, productive, productivity_score, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, device_id, start_ts, end_ts, productive, productivity_score, tags, created_at))
    conn.commit()
    print(f"Session {session_id} added for user {user_id}")
    return session_id


def add_app_usage(session_id, timestamp, category, activity, duration_ms, productivity_label):
    """Add an app usage entry linked to a session."""
    usage_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO app_usage (id, session_id, timestamp, category, activity, duration_ms, productivity_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (usage_id, session_id, timestamp, category, activity, duration_ms, productivity_label))
    conn.commit()
    print(f"App usage {usage_id} added for session {session_id}")
    return usage_id


def add_productivity_report(user_id, date, focus_minutes, distraction_minutes, productivity_score, ai_summary=None):
    """Add or update a daily productivity report."""
    report_id = str(uuid.uuid4())
    created_at = datetime.now()
    cursor.execute("""
        INSERT INTO productivity_reports (
            id, user_id, date, focus_minutes, distraction_minutes, productivity_score, ai_summary, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            focus_minutes = excluded.focus_minutes,
            distraction_minutes = excluded.distraction_minutes,
            productivity_score = excluded.productivity_score,
            ai_summary = excluded.ai_summary,
            created_at = excluded.created_at;
    """, (report_id, user_id, date, focus_minutes, distraction_minutes, productivity_score, ai_summary, created_at))
    conn.commit()
    print(f"Productivity report added/updated for {user_id} on {date}")
    return report_id


def add_team(name, owner_id):
    """Create a new team."""
    team_id = str(uuid.uuid4())
    created_at = datetime.now()
    cursor.execute("""
        INSERT INTO teams (id, name, owner_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (team_id, name, owner_id, created_at))
    conn.commit()
    print(f"Team '{name}' created with ID {team_id}")
    return team_id


def add_team_member(team_id, user_id, role="member"):
    """Add a user to a team."""
    joined_at = datetime.now()
    cursor.execute("""
        INSERT INTO team_members (team_id, user_id, role, joined_at)
        VALUES (?, ?, ?, ?)
    """, (team_id, user_id, role, joined_at))
    conn.commit()
    print(f"User {user_id} added to team {team_id} as {role}")
    return (team_id, user_id)


# --- Example Usage ---

# Add a user
user_id = add_user("alice@example.com", "hashed_password_123", "Alice Smith", "premium")

# Add another user
user2_id = add_user("bob@example.com", "hashed_pw_bob", "Bob Brown", "free")

# Add a device for that user
device_id = add_device(user_id, "Alice's MacBook", "desktop")

# Add a session
session_id = add_session(
    user_id=user_id,
    device_id=device_id,
    start_ts=datetime(2025, 11, 4, 9, 0, 0),
    end_ts=datetime(2025, 11, 4, 11, 0, 0),
    productive=True,
    productivity_score=92.5,
    tags=["work", "focus"]
)

# Add some app usage data for that session
add_app_usage(session_id, datetime(2025, 11, 4, 9, 15, 0), "Work", "code.exe", 5400000, "productive")
add_app_usage(session_id, datetime(2025, 11, 4, 10, 45, 0), "Entertainment", "youtube.com", 900000, "distracting")

# Add a productivity report for that day
add_productivity_report(user_id, "2025-11-04", 90, 15, 85.0, "Great focus overall, minimal distractions.")

# Create a team and add members
team_id = add_team("Focus Masters", user_id)
add_team_member(team_id, user_id, role="owner")
add_team_member(team_id, user2_id, role="member")

# --- Display Data ---

print("\nAll users:")
cursor.execute("SELECT * FROM users;")
for row in cursor.fetchall():
    print(row)

print("\nAll devices:")
cursor.execute("SELECT * FROM devices;")
for row in cursor.fetchall():
    print(row)

print("\nAll sessions:")
cursor.execute("SELECT * FROM sessions;")
for row in cursor.fetchall():
    print(row)

print("\nAll app usage:")
cursor.execute("SELECT * FROM app_usage;")
for row in cursor.fetchall():
    print(row)

print("\nAll productivity reports:")
cursor.execute("SELECT * FROM productivity_reports;")
for row in cursor.fetchall():
    print(row)

print("\nAll teams:")
cursor.execute("SELECT * FROM teams;")
for row in cursor.fetchall():
    print(row)

print("\nAll team members:")
cursor.execute("SELECT * FROM team_members;")
for row in cursor.fetchall():
    print(row)

conn.close()