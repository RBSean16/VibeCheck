# back.py

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date, timedelta, datetime
from typing import List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import sqlite3
import os
import random
import hashlib
import numpy as np
import requests

# --- FastAPI App Initialization ---
app = FastAPI(title="VibeCheck", version="1.0.0")

# --- Static Directory Setup ---
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Color Constant for Charts ---
PRIMARY_COLOR = "#0d6efd"

# --- DATA LAYER (DatabaseManager) ---
class DatabaseManager:
    @staticmethod
    def get_connection():
        conn = sqlite3.connect("wellness.db")
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
        with DatabaseManager.get_connection() as conn:
            query = """
                SELECT SUBSTR(date, 1, 10) AS activity_date FROM mood_entries WHERE user_id = ?
                UNION
                SELECT date AS activity_date FROM journal_entries WHERE user_id = ?
            """
            rows = conn.cursor().execute(query, (user_id, user_id)).fetchall()
            return [row['activity_date'] for row in rows]

    @staticmethod
    def get_all_journal_entries(user_id: int):
        with DatabaseManager.get_connection() as conn:
            rows = conn.cursor().execute("SELECT id, date, content FROM journal_entries WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def delete_journal_entry(entry_id: int):
        with DatabaseManager.get_connection() as conn:
            conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
            conn.commit()

    @staticmethod
    def get_mood_entries(user_id: int, limit_days: int):
        start_date = (datetime.now() - timedelta(days=limit_days)).isoformat()
        with DatabaseManager.get_connection() as conn:
            rows = conn.cursor().execute(
                "SELECT mood_score, date, notes FROM mood_entries WHERE user_id = ? AND date >= ? ORDER BY date ASC", 
                (user_id, start_date)
            ).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_mood_entries_for_today(user_id: int):
        today_str = datetime.now().date().isoformat()
        with DatabaseManager.get_connection() as conn:
            rows = conn.cursor().execute(
                "SELECT mood_score, date, notes FROM mood_entries WHERE user_id = ? AND date >= ? ORDER BY date ASC", 
                (user_id, today_str)
            ).fetchall()
            return [dict(row) for row in rows]

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
class MoodCheckResponse(BaseModel):
    has_enough_data: bool

# --- API ROUTES ---
@app.post("/api/register", tags=["Authentication"])
def register_user(user_input: UserAuthInput):
    new_user = DatabaseManager.create_user(user_input.name, user_input.password)
    if new_user:
        return {"message": "User created successfully", "user": new_user}
    raise HTTPException(status_code=409, detail="An account with this username already exists.")

@app.post("/api/login", tags=["Authentication"])
def login_user(user_input: UserAuthInput):
    user = DatabaseManager.get_user_by_name(user_input.name)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that username.")
    password_hash = hashlib.sha256(user_input.password.encode()).hexdigest()
    if password_hash == user['password_hash']:
        return {"message": "Login successful", "user_id": user['user_id'], "name": user['name']}
    raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")
    
@app.post("/api/mood-entry", tags=["Mood Tracking"])
def add_mood(entry: MoodInput):
    DatabaseManager.add_mood_entry(entry.user_id, entry.mood_score, entry.notes)
    return {"message": "Mood entry added successfully"}

@app.post("/api/journal-entry", tags=["Journaling"])
def add_journal(entry: JournalInput):
    DatabaseManager.add_journal_entry(entry.user_id, entry.content)
    return {"message": "Journal entry added successfully"}

@app.get("/api/activity-dates/{user_id}", tags=["Journaling"])
def get_activity_dates(user_id: int):
    dates = DatabaseManager.get_activity_dates(user_id)
    return {"dates": dates}

@app.get("/api/journals/{user_id}", tags=["Journaling"])
def get_journals(user_id: int):
    return DatabaseManager.get_all_journal_entries(user_id)

@app.delete("/api/journal/{entry_id}", tags=["Journaling"])
def delete_journal(entry_id: int):
    DatabaseManager.delete_journal_entry(entry_id)
    return {"message": "Journal entry deleted successfully"}

@app.get("/api/wellness-tip", tags=["Insights"])
def get_wellness_tip():
    try:
        response = requests.get("https://zenquotes.io/api/today")
        response.raise_for_status()
        data = response.json()[0]
        return {"quote": data['q'], "author": data['a']}
    except requests.exceptions.RequestException:
        return {"quote": "Could not fetch a tip. Check your internet connection.", "author": "VibeCheck"}

@app.get("/api/recommendation/{user_id}", tags=["Insights"])
def get_recommendation(user_id: int):
    # Expanded lists of hard-coded, randomized responses
    positive_insights = [
        "Your recent mood has been consistently positive. Keep up the great work!", "Seeing lots of positive moods from you lately. Whatever you're doing, it's working!", "It looks like you've been having a great week. Keep embracing that positive energy.", "Your mood log is shining brightly! Thanks for sharing your positive moments.", "A consistent high mood is a great sign of well-being. Keep riding that wave!", "Fantastic! Your recent entries show a very positive trend. Keep it up.", "It's wonderful to see such positive check-ins. You're doing great.", "Your mood trend is pointing straight up! We love to see it.", "You've been in a great headspace recently. Remember what this feels like.", "The data shows a happy and healthy mindset. Keep building on this momentum.", "Keep doing what you're doing! The positivity is clear from your entries.", "Your consistent positive mood is an achievement worth celebrating.", "It's great to see you thriving. Your mood log reflects a period of well-being.", "Your mood entries are overwhelmingly positive. That's a wonderful sign.", "The trend is clear: you've been feeling great. Keep that positive momentum going!"
    ]
    neutral_insights = [
        "Your mood has been fluctuating. Remember to take time for self-care activities.", "Some good days, some not-so-good days. That's a normal part of life's rhythm.", "It seems like a mix of ups and downs recently. A consistent routine can sometimes help stabilize mood.", "Your mood seems balanced but with some variations. Check in with yourself and see what you need today.", "A mixed bag of moods is common. What's one small thing you can do for yourself today?", "Your log shows a blend of different feelings. Remember that all your emotions are valid.", "Navigating both highs and lows is part of the journey. Be patient with yourself.", "It looks like an average week. Consider scheduling a small activity you enjoy to give yourself a boost.", "Your mood is steady but has room for a lift. How about some fresh air or your favorite music?", "A neutral trend can be a good time for reflection. What's one thing that could make tomorrow brighter?", "The data shows a mix of moods. It's okay to have days where you just feel 'okay'.", "Your mood has been steady. Acknowledging these neutral moments is as important as the highs and lows.", "This period of balance could be a good time to build some new, healthy habits.", "Your log shows a stable, neutral trend. This can be a sign of resilience.", "It's okay to just be. Your mood entries show a period of calm and balance."
    ]
    negative_insights = [
        "It seems you've had a tough few days. Consider talking to a friend or engaging in a relaxing hobby.", "Your mood has been trending lower recently. Remember that it's okay not to be okay. Prioritize rest.", "Seeing a pattern of lower moods. A short walk outside can sometimes make a surprising difference.", "It looks like things have been challenging lately. Please be extra kind to yourself.", "Remember that tough times don't last forever. Your favorite comfort movie or a warm drink might help.", "Your recent entries suggest you're going through a rough patch. Your feelings are valid; let yourself feel them.", "When your mood is low, small comforts can help. Consider listening to some calming music or a podcast.", "It's brave of you to keep logging even on difficult days. Acknowledging your feelings is a huge first step.", "It looks like you could use a break. Is there something simple you can do to de-stress, even for 5 minutes?", "Seeing this pattern is a sign to check in with yourself. Remember the support resources in the app if you need them.", "Be gentle with yourself. Storms don't last forever.", "It's okay to feel this way. Acknowledging difficult emotions is a sign of strength.", "This seems like a difficult period. Make sure you're getting enough rest and being kind to your body and mind.", "Remember that even a small step is still a step forward. Don't pressure yourself too much right now.", "Your log shows you're navigating some tough feelings. Reaching out to someone you trust can often lighten the load."
    ]

    # Logic to select and return an insight
    mood_entries = DatabaseManager.get_mood_entries(user_id, limit_days=7)
    
    if len(mood_entries) < 3:
        return {"recommendation": "Keep logging your mood for a few more days to unlock personalized insights!"}

    scores = [entry['mood_score'] for entry in mood_entries]
    avg_score = np.mean(scores)

    # Determine the mood category and select a random message
    if avg_score >= 7:
        suggestion = random.choice(positive_insights)
    elif avg_score >= 4:
        suggestion = random.choice(neutral_insights)
    else:
        suggestion = random.choice(negative_insights)
        
    return {"recommendation": suggestion}

@app.get("/api/today-moods/{user_id}", tags=["Visualizations"])
def get_today_moods(user_id: int):
    return DatabaseManager.get_mood_entries_for_today(user_id)

@app.get("/api/mood-data-check/{user_id}", response_model=MoodCheckResponse, tags=["Visualizations"])
def check_mood_data(user_id: int, timespan: str):
    MINIMUM_DISTINCT_DAYS = 2
    if timespan not in ["7d", "30d"]:
        return {"has_enough_data": False}
    limit = 7 if timespan == "7d" else 30
    mood_entries = DatabaseManager.get_mood_entries(user_id, limit_days=limit)
    if len(mood_entries) < MINIMUM_DISTINCT_DAYS:
        return {"has_enough_data": False}
    df = pd.DataFrame(mood_entries)
    df['date'] = pd.to_datetime(df['date'])
    distinct_days = df['date'].dt.date.nunique()
    has_enough = distinct_days >= MINIMUM_DISTINCT_DAYS
    return {"has_enough_data": has_enough}

@app.get("/api/mood-chart/{user_id}", tags=["Visualizations"])
def get_mood_chart(user_id: int, timespan: str = "30d"):
    limit = 7 if timespan == "7d" else 30
    mood_entries = DatabaseManager.get_mood_entries(user_id, limit_days=limit)
    title = f"Your Daily Average Mood (Last {limit} Days)"
    if not mood_entries:
        raise HTTPException(status_code=404, detail="Not enough mood data for this period.")
    df = pd.DataFrame(mood_entries)
    df['date'] = pd.to_datetime(df['date'])
    plot_df = df.groupby(df['date'].dt.date)['mood_score'].mean().reset_index()
    plot_df['date'] = pd.to_datetime(plot_df['date'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(plot_df['date'], plot_df['mood_score'], marker='o', linestyle='-', color=PRIMARY_COLOR)
    ax.set_title(title, fontsize=16, loc='center')
    ax.set_ylabel("Mood")
    ax.set_yticks([1, 3, 5, 7, 9])
    ax.set_yticklabels(['😠 Angry', '😟 Sad', '😐 Neutral', '😊 Content', '😄 Happy'])
    ax.set_ylim(0, 10)
    ax.grid(True, linestyle='--', alpha=0.6, axis='y')
    
    ax.margins(x=0.05)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    if timespan == "7d":
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))

    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
    
    plt.tight_layout()
    chart_path = f"static/mood_chart_{user_id}.png"
    plt.savefig(chart_path)
    plt.close(fig)
    return FileResponse(chart_path, media_type="image/png")