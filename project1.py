import uuid
import sqlite3
from datetime import datetime

# Connect to (or create) a local database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

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

conn.commit()

# Example: Add a user
def add_user(email, password_hash=None, full_name=None, plan="free"):
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, plan, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, email, password_hash, full_name, plan, created_at))
    conn.commit()
    print(f"User {email} added with id {user_id}")

# Example usage
add_user("alice@example.com", "hashed_password_123", "Alice Smith", "premium")

# Show all users
cursor.execute("SELECT * FROM users;")
for row in cursor.fetchall():
    print(row)

conn.close()
