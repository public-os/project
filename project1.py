import uuid
import sqlite3
from datetime import datetime

# Connect to (or create) a local database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Enable foreign key constraints in SQLite
cursor.execute("PRAGMA foreign_keys = ON;")

# Create the users table
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

# Create the devices table (linked to users)
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

conn.commit()

# --- Example functions ---

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

# --- Example usage ---

# Add a user
user_id = add_user("alice@example.com", "hashed_password_123", "Alice Smith", "premium")

# Add a device for that user
add_device(user_id, "Alice's MacBook", "desktop")

# Show all users
print("\nAll users:")
cursor.execute("SELECT * FROM users;")
for row in cursor.fetchall():
    print(row)

# Show all devices
print("\nAll devices:")
cursor.execute("SELECT * FROM devices;")
for row in cursor.fetchall():
    print(row)

conn.close()
