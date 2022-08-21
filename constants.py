import os

# For further security and best practice use: os.getenv("DATABASE_URL")
SQLITE_DB_URI = "sqlite:///books.sqlite3"
SESSION_SECRET = "development secret..."

if os.getenv("SESSION_SECRET"):
    SESSION_SECRET = os.getenv("SESSION_SECRET")

