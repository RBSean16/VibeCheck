# back.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sqlite3
import hashlib

# --- FastAPI App Initialization ---
app = FastAPI(title="VibeCheck", version="1.0.0")

# --- DATA LAYER (DatabaseManager) ---
class DatabaseManager:
    @staticmethod
    def get_connection():
        conn = sqlite3.connect("VC.db")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        with DatabaseManager.get_connection() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL,
                            created_at TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS mood_entries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            mood_score INTEGER,
                            notes TEXT,
                            date TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(user_id))''')
            c.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            content TEXT,
                            date TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(user_id))''')
            conn.commit()

    @staticmethod
    def get_user_by_name(name: str):
        with DatabaseManager.get_connection() as conn:
            return conn.cursor().execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()

    @staticmethod
    def create_user(name: str, password: str) -> Optional[dict]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        created_at = datetime.now().isoformat()
        with DatabaseManager.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, password_hash, created_at) VALUES (?, ?, ?)",
                               (name, password_hash, created_at))
                conn.commit()
                return {"user_id": cursor.lastrowid, "name": name}
            except sqlite3.IntegrityError:
                return None
    
    @staticmethod
    def add_mood_entry(user_id: int, mood_score: int, notes: str):
        with DatabaseManager.get_connection() as conn:
            conn.execute(
                "INSERT INTO mood_entries (user_id, mood_score, notes, date) VALUES (?, ?, ?, ?)",
                (user_id, mood_score, notes, datetime.now().isoformat())
            )
            conn.commit()

    @staticmethod
    def add_journal_entry(user_id: int, content: str):
        with DatabaseManager.get_connection() as conn:
            conn.execute("INSERT INTO journal_entries (user_id, content, date) VALUES (?, ?, ?)",
                         (user_id, content, datetime.now().date().isoformat()))
            conn.commit()

    @staticmethod
    def get_activity_dates(user_id: int):
        """Gets all unique dates that have either a mood or a journal entry."""
        with DatabaseManager.get_connection() as conn:
            query = """
                SELECT SUBSTR(date, 1, 10) AS activity_date FROM mood_entries WHERE user_id = ?
                UNION
                SELECT date AS activity_date FROM journal_entries WHERE user_id = ?
            """
            rows = conn.cursor().execute(query, (user_id, user_id)).fetchall()
            return [row['activity_date'] for row in rows]

# Initialize the database on startup
DatabaseManager.init_db()

# --- Pydantic Models ---
class UserAuthInput(BaseModel):
    name: str
    password: str

class MoodInput(BaseModel):
    user_id: int
    mood_score: int
    notes: Optional[str] = ""

class JournalInput(BaseModel):
    user_id: int
    content: str

# --- API ROUTES ---
@app.post("/api/register", tags=["Authentication"])
def register_user(user_input: UserAuthInput):
    """Creates a new user account."""
    new_user = DatabaseManager.create_user(user_input.name, user_input.password)
    if new_user:
        return {"message": "User created successfully", "user": new_user}
    raise HTTPException(status_code=409, detail="An account with this username already exists.")

@app.post("/api/login", tags=["Authentication"])
def login_user(user_input: UserAuthInput):
    """Authenticates a user and returns their details upon success."""
    user = DatabaseManager.get_user_by_name(user_input.name)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that username.")
    
    password_hash = hashlib.sha256(user_input.password.encode()).hexdigest()
    if password_hash == user['password_hash']:
        return {"message": "Login successful", "user_id": user['user_id'], "name": user['name']}
    
    raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    
@app.post("/api/mood-entry", tags=["Entries"])
def add_mood(entry: MoodInput):
    """Adds a new mood entry for a user."""
    DatabaseManager.add_mood_entry(entry.user_id, entry.mood_score, entry.notes)
    return {"message": "Mood entry added successfully"}

@app.post("/api/journal-entry", tags=["Entries"])
def add_journal(entry: JournalInput):
    """Adds a new journal entry for a user."""
    DatabaseManager.add_journal_entry(entry.user_id, entry.content)
    return {"message": "Journal entry added successfully"}

@app.get("/api/activity-dates/{user_id}", tags=["Entries"])
def get_activity_dates(user_id: int):
    """Retrieves all unique dates with an entry to populate the UI calendar."""
    dates = DatabaseManager.get_activity_dates(user_id)
    return {"dates": dates}