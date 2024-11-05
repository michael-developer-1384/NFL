from .connection import get_connection
from .setup import create_tables

def save_team_and_venue(team, venue, override=False):
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    # Venue speichern
    if venue:
        # Überprüfen, ob Venue bereits existiert
        cursor.execute("SELECT * FROM venues WHERE id = ?", (venue.id,))
        existing_venue = cursor.fetchone()
        if existing_venue and not override:
            print(f"Venue '{venue.fullName}' existiert bereits und wird nicht überschrieben.")
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO venues (id, fullName, city, state, zipCode, grass, indoor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                venue.id,
                venue.fullName,
                venue.city,
                venue.state,
                venue.zipCode,
                venue.grass,
                venue.indoor
            ))
            print(f"Venue '{venue.fullName}' wurde gespeichert.")

    # Team speichern
    # Überprüfen, ob Team bereits existiert
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team.id,))
    existing_team = cursor.fetchone()
    if existing_team and not override:
        print(f"Team '{team.displayName}' existiert bereits und wird nicht überschrieben.")
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO teams (
                id, location, name, abbreviation, displayName, color, alternateColor, isActive, venue_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            team.id,
            team.location,
            team.name,
            team.abbreviation,
            team.displayName,
            team.color,
            team.alternateColor,
            team.isActive,
            team.venue_id
        ))
        print(f"Team '{team.displayName}' wurde gespeichert.")

    conn.commit()
    conn.close()

def save_season(season, override=False):
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if season exists
    cursor.execute("SELECT * FROM seasons WHERE id = ?", (season.id,))
    existing_season = cursor.fetchone()
    if existing_season and not override:
        print(f"Saison '{season.display_name}' existiert bereits und wird nicht überschrieben.")
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO seasons (
                id, year, start_date, end_date, display_name, type_id, type_name, type_abbreviation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            season.id,
            season.year,
            season.start_date,
            season.end_date,
            season.display_name,
            season.type_id,
            season.type_name,
            season.type_abbreviation
        ))
        print(f"Saison '{season.display_name}' wurde gespeichert.")

    conn.commit()
    conn.close()

def save_game(game, override=False):
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if game exists
    cursor.execute("SELECT * FROM games WHERE id = ?", (game.id,))
    existing_game = cursor.fetchone()
    if existing_game and not override:
        print(f"Spiel '{game.id}' existiert bereits und wird nicht überschrieben.")
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO games (
                id, season_id, week_number, date, venue_id, home_team_id, away_team_id,
                home_score, away_score, winner_team_id, status, attendance, broadcast
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game.id,
            game.season_id,
            game.week_number,
            game.date,
            game.venue_id,
            game.home_team_id,
            game.away_team_id,
            game.home_score,
            game.away_score,
            game.winner_team_id,
            game.status,
            game.attendance,
            game.broadcast
        ))
        print(f"Spiel '{game.id}' wurde gespeichert.")

    conn.commit()
    conn.close()
