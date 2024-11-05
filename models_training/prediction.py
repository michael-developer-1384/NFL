import sqlite3
import pandas as pd
import os
from . import utils

DATABASE = 'nfl_data.db'

def get_season_year_and_week(game_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.year, g.week_number
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE g.id = ?
    """, (game_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        season_year, week_number = result
        return season_year, week_number
    else:
        return None, None

def predict_game(model_cls, scaler, game_id):
    conn = sqlite3.connect(DATABASE)

    # Laden des Spiels anhand der ID
    query = f"""
        SELECT 
            g.id as game_id,
            g.season_id,
            s.year as season_year,
            g.week_number,
            g.home_team_id,
            g.away_team_id,
            t_home.name as home_team_name,
            t_away.name as away_team_name,
            v.indoor as indoor_stadium
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        JOIN teams t_home ON g.home_team_id = t_home.id
        JOIN teams t_away ON g.away_team_id = t_away.id
        JOIN venues v ON g.venue_id = v.id
        WHERE g.id = {game_id}
    """
    game = pd.read_sql_query(query, conn)

    if game.empty:
        print(f"Spiel mit ID {game_id} wurde nicht gefunden.")
        conn.close()
        return

    game = game.iloc[0]
    season_year = game['season_year']
    week = game['week_number']
    home_team_id = game['home_team_id']
    away_team_id = game['away_team_id']
    home_team_name = game['home_team_name']
    away_team_name = game['away_team_name']
    indoor_stadium = int(game['indoor_stadium'])

    # Setze max_week auf die Woche des Spiels, um zukünftige Spiele auszuschließen
    max_week = week

    # Features berechnen
    conn = sqlite3.connect(DATABASE)
    home_team_avg_points = utils.calculate_avg_points(home_team_id, conn, season_year, max_week)
    away_team_avg_points = utils.calculate_avg_points(away_team_id, conn, season_year, max_week)
    home_team_avg_allowed = utils.calculate_avg_allowed_points(home_team_id, conn, season_year, max_week)
    away_team_avg_allowed = utils.calculate_avg_allowed_points(away_team_id, conn, season_year, max_week)
    home_team_form = utils.calculate_recent_form(home_team_id, conn, season_year, max_week)
    away_team_form = utils.calculate_recent_form(away_team_id, conn, season_year, max_week)
    home_team_home_win_pct = utils.calculate_home_win_percentage(home_team_id, conn, season_year, max_week)
    away_team_away_win_pct = utils.calculate_away_win_percentage(away_team_id, conn, season_year, max_week)
    head_to_head = utils.calculate_head_to_head(home_team_id, away_team_id, conn, season_year, max_week)

    # Features vorbereiten
    features = pd.DataFrame({
        'home_team_avg_points': [home_team_avg_points],
        'away_team_avg_points': [away_team_avg_points],
        'home_team_avg_allowed': [home_team_avg_allowed],
        'away_team_avg_allowed': [away_team_avg_allowed],
        'home_team_form': [home_team_form],
        'away_team_form': [away_team_form],
        'home_team_home_win_pct': [home_team_home_win_pct],
        'away_team_away_win_pct': [away_team_away_win_pct],
        'head_to_head': [head_to_head],
        'indoor_stadium': [indoor_stadium]
    })

    # Fehlende Werte auffüllen
    features = features.fillna(0)

    # Features skalieren
    features_scaled = scaler.transform(features)

    # Vorhersage der Gewinnwahrscheinlichkeit
    probability = model_cls.predict_proba(features_scaled)[0][1]
    predicted_winner = home_team_name if probability >= 0.5 else away_team_name
    predicted_prob = probability if probability >= 0.5 else 1 - probability

    print(f"Spiel: {home_team_name} vs. {away_team_name}")
    print(f"Vorhergesagter Gewinner: {predicted_winner} mit Wahrscheinlichkeit {predicted_prob:.2%}")

    conn.close()
    return probability

def predict_week_games(model_cls, scaler, week, season_year):
    conn = sqlite3.connect(DATABASE)

    # Spiele der angegebenen Woche und Saison laden
    query = f"""
        SELECT 
            g.id as game_id,
            g.season_id,
            s.year as season_year,
            g.week_number,
            g.home_team_id,
            g.away_team_id,
            g.date,
            t_home.name as home_team_name,
            t_away.name as away_team_name,
            v.indoor as indoor_stadium,
            g.home_score,
            g.away_score,
            g.status
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        JOIN teams t_home ON g.home_team_id = t_home.id
        JOIN teams t_away ON g.away_team_id = t_away.id
        JOIN venues v ON g.venue_id = v.id
        WHERE g.week_number = {week} AND s.year = {season_year}
    """
    games = pd.read_sql_query(query, conn)

    if games.empty:
        print(f"Keine Spiele für Woche {week} im Jahr {season_year} gefunden.")
        conn.close()
        return

    # Variablen für das Resümee
    total_games = 0
    correct_predictions = 0
    incorrect_predictions = 0

    # Ordner für Vorhersagen erstellen
    output_dir = 'predictions'
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"Vorhersagen_Woche_{week}_{season_year}.txt")

    # Öffne die Datei zum Schreiben
    with open(file_path, "w", encoding="utf-8") as file:
        # Für jedes Spiel Vorhersage durchführen
        for index, game in games.iterrows():
            total_games += 1
            home_team_id = game['home_team_id']
            away_team_id = game['away_team_id']
            home_team_name = game['home_team_name']
            away_team_name = game['away_team_name']
            indoor_stadium = int(game['indoor_stadium'])

            # Setze max_week auf die Woche des Spiels, um zukünftige Spiele auszuschließen
            max_week = week

            # Features berechnen
            home_team_avg_points = utils.calculate_avg_points(home_team_id, conn, season_year, max_week)
            away_team_avg_points = utils.calculate_avg_points(away_team_id, conn, season_year, max_week)
            home_team_avg_allowed = utils.calculate_avg_allowed_points(home_team_id, conn, season_year, max_week)
            away_team_avg_allowed = utils.calculate_avg_allowed_points(away_team_id, conn, season_year, max_week)
            home_team_form = utils.calculate_recent_form(home_team_id, conn, season_year, max_week)
            away_team_form = utils.calculate_recent_form(away_team_id, conn, season_year, max_week)
            home_team_home_win_pct = utils.calculate_home_win_percentage(home_team_id, conn, season_year, max_week)
            away_team_away_win_pct = utils.calculate_away_win_percentage(away_team_id, conn, season_year, max_week)
            head_to_head = utils.calculate_head_to_head(home_team_id, away_team_id, conn, season_year, max_week)

            # Features vorbereiten
            features = pd.DataFrame({
                'home_team_avg_points': [home_team_avg_points],
                'away_team_avg_points': [away_team_avg_points],
                'home_team_avg_allowed': [home_team_avg_allowed],
                'away_team_avg_allowed': [away_team_avg_allowed],
                'home_team_form': [home_team_form],
                'away_team_form': [away_team_form],
                'home_team_home_win_pct': [home_team_home_win_pct],
                'away_team_away_win_pct': [away_team_away_win_pct],
                'head_to_head': [head_to_head],
                'indoor_stadium': [indoor_stadium]
            })

            # Fehlende Werte auffüllen
            features = features.fillna(0)

            # Features skalieren
            features_scaled = scaler.transform(features)

            # Vorhersage der Gewinnwahrscheinlichkeit
            probability = model_cls.predict_proba(features_scaled)[0][1]
            predicted_winner = home_team_name if probability >= 0.5 else away_team_name
            predicted_prob = probability if probability >= 0.5 else 1 - probability

            # Ausgabe des Ergebnisses
            result_str = f"Woche {week} - Spiel: {home_team_name} vs. {away_team_name}\n"
            result_str += f"Vorhergesagter Gewinner: {predicted_winner} mit Wahrscheinlichkeit {predicted_prob:.2%}\n"

            # Vergleich mit tatsächlichem Ergebnis, falls verfügbar
            if game['status'] == 'Final':
                home_score = game['home_score']
                away_score = game['away_score']
                if pd.isna(home_score) or pd.isna(away_score):
                    result_str += "Ergebnis nicht verfügbar.\n"
                else:
                    home_score = int(home_score)
                    away_score = int(away_score)
                    result_str += f"Endstand: {home_team_name} {home_score} - {away_team_name} {away_score}\n"
                    if home_score > away_score:
                        actual_winner = home_team_name
                    elif home_score < away_score:
                        actual_winner = away_team_name
                    else:
                        actual_winner = 'Unentschieden'
                    result_str += f"Tatsächlicher Gewinner: {actual_winner}\n"
                    if predicted_winner == actual_winner:
                        result_str += "Vorhersage war korrekt.\n"
                        correct_predictions += 1
                    else:
                        result_str += "Vorhersage war nicht korrekt.\n"
                        incorrect_predictions += 1
            else:
                result_str += "Spiel hat noch nicht stattgefunden.\n"
                # Für noch nicht stattgefundene Spiele zählen wir die Vorhersage nicht
                total_games -= 1
            result_str += "-" * 50 + "\n"

            # Ausgabe in Konsole
            print(result_str)
            # Schreiben in Datei
            file.write(result_str)

        # Wochenresümee
        if total_games > 0:
            summary = f"Woche {week} Zusammenfassung:\n"
            summary += f"Anzahl der Spiele: {total_games}\n"
            summary += f"Korrekte Vorhersagen: {correct_predictions}\n"
            summary += f"Inkorrekte Vorhersagen: {incorrect_predictions}\n"
            accuracy = correct_predictions / total_games * 100
            summary += f"Genauigkeit der Vorhersagen: {accuracy:.2f}%\n"
            print(summary)
            file.write(summary)
        else:
            print("Keine abgeschlossenen Spiele in dieser Woche zum Auswerten.")
            file.write("Keine abgeschlossenen Spiele in dieser Woche zum Auswerten.\n")
    conn.close()
