from .connection import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabelle für Venues erstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY,
            fullName TEXT,
            city TEXT,
            state TEXT,
            zipCode TEXT,
            grass BOOLEAN,
            indoor BOOLEAN
        )
    """)

    # Tabelle für Teams erstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            location TEXT,
            name TEXT,
            abbreviation TEXT,
            displayName TEXT,
            color TEXT,
            alternateColor TEXT,
            isActive BOOLEAN,
            venue_id INTEGER,
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        )
    """)

    # Tabelle für Seasons erstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY,
            year INTEGER,
            start_date TEXT,
            end_date TEXT,
            display_name TEXT,
            type_id INTEGER,
            type_name TEXT,
            type_abbreviation TEXT
        )
    """)

    # Tabelle für Games erstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            season_id INTEGER,
            week_number INTEGER,
            date TEXT,
            venue_id INTEGER,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            winner_team_id INTEGER,
            status TEXT,
            attendance INTEGER,
            broadcast TEXT,
            FOREIGN KEY (season_id) REFERENCES seasons(id),
            FOREIGN KEY (venue_id) REFERENCES venues(id),
            FOREIGN KEY (home_team_id) REFERENCES teams(id),
            FOREIGN KEY (away_team_id) REFERENCES teams(id),
            FOREIGN KEY (winner_team_id) REFERENCES teams(id)
        )
    """)

    conn.commit()
    conn.close()
