import sqlite3
from flask import g
from config import Config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(Config.DATABASE)
    cursor = db.cursor()

    # Doctors Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER NOT NULL
        )
    """)

    # Patients Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT
        )
    """)

    # Appointments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            date TEXT,
            status TEXT DEFAULT 'Pending',
            notes TEXT,
            symptoms TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    # Ensure `symptoms` column exists for existing databases
    cursor.execute("PRAGMA table_info(appointments)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'symptoms' not in cols:
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN symptoms TEXT")
        except Exception:
            pass

    db.commit()
    db.close()