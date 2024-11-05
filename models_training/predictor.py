# models_training/predictor.py

import sqlite3
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression

DATABASE = 'nfl_data.db'

def load_data(max_week=None, season_year=None):
    conn = sqlite3.connect(DATABASE)
    
    # WHERE-Klausel erstellen
    where_clause = "WHERE g.status = 'Final' AND g.home_score IS NOT NULL AND g.away_score IS NOT NULL"
    if season_year is not None:
        where_clause += f" AND s.year = {season_year}"
    if max_week is not None:
        where_clause += f" AND g.week_number < {max_week}"
    
    # Spiele laden
    query = f"""
        SELECT 
            g.id as game_id,
            g.season_id,
            s.year as season_year,
            g.week_number,
            g.date,
            g.home_team_id,
            g.away_team_id,
            g.home_score,
            g.away_score,
            t_home.name as home_team_name,
            t_away.name as away_team_name,
            t_home.abbreviation as home_team_abbr,
            t_away.abbreviation as away_team_abbr,
            v.indoor as indoor_stadium
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        JOIN teams t_home ON g.home_team_id = t_home.id
        JOIN teams t_away ON g.away_team_id = t_away.id
        JOIN venues v ON g.venue_id = v.id
        {where_clause}
    """
    
    games = pd.read_sql_query(query, conn)
    
    conn.close()
    return games

def calculate_avg_points(team_id, conn, season_year, max_week):
    avg_points = pd.read_sql_query(f"""
        SELECT AVG(CASE WHEN g.home_team_id = {team_id} THEN g.home_score
                        WHEN g.away_team_id = {team_id} THEN g.away_score END) as avg_points
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE (g.home_team_id = {team_id} OR g.away_team_id = {team_id})
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['avg_points'].iloc[0]
    return avg_points

def calculate_avg_allowed_points(team_id, conn, season_year, max_week):
    avg_allowed = pd.read_sql_query(f"""
        SELECT AVG(CASE WHEN g.home_team_id = {team_id} THEN g.away_score
                        WHEN g.away_team_id = {team_id} THEN g.home_score END) as avg_allowed
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE (g.home_team_id = {team_id} OR g.away_team_id = {team_id})
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['avg_allowed'].iloc[0]
    return avg_allowed


def calculate_recent_form(team_id, conn, season_year, max_week, num_games=5):
    recent_games = pd.read_sql_query(f"""
        SELECT 
            CASE 
                WHEN g.home_team_id = {team_id} AND g.home_score > g.away_score THEN 1
                WHEN g.away_team_id = {team_id} AND g.away_score > g.home_score THEN 1
                ELSE 0
            END as win
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE (g.home_team_id = {team_id} OR g.away_team_id = {team_id})
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
        ORDER BY g.date DESC
        LIMIT {num_games}
    """, conn)
    if recent_games.empty:
        return 0
    win_rate = recent_games['win'].mean()
    return win_rate


def calculate_home_win_percentage(team_id, conn, season_year, max_week):
    total_home_games = pd.read_sql_query(f"""
        SELECT COUNT(*) as total FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE g.home_team_id = {team_id}
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['total'].iloc[0]
    
    home_wins = pd.read_sql_query(f"""
        SELECT COUNT(*) as wins FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE g.home_team_id = {team_id}
          AND g.home_score > g.away_score
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['wins'].iloc[0]
    
    if total_home_games == 0:
        return 0
    return home_wins / total_home_games


def calculate_away_win_percentage(team_id, conn, season_year, max_week):
    total_away_games = pd.read_sql_query(f"""
        SELECT COUNT(*) as total FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE g.away_team_id = {team_id}
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['total'].iloc[0]
    
    away_wins = pd.read_sql_query(f"""
        SELECT COUNT(*) as wins FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE g.away_team_id = {team_id}
          AND g.away_score > g.home_score
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)['wins'].iloc[0]
    
    if total_away_games == 0:
        return 0
    return away_wins / total_away_games

def calculate_head_to_head(home_team_id, away_team_id, conn, season_year, max_week):
    h2h_games = pd.read_sql_query(f"""
        SELECT 
            CASE 
                WHEN g.home_team_id = {home_team_id} AND g.home_score > g.away_score THEN 1
                WHEN g.away_team_id = {home_team_id} AND g.away_score > g.home_score THEN 1
                ELSE 0
            END as home_win
        FROM games g
        JOIN seasons s ON g.season_id = s.id
        WHERE ((g.home_team_id = {home_team_id} AND g.away_team_id = {away_team_id}) OR
               (g.home_team_id = {away_team_id} AND g.away_team_id = {home_team_id}))
          AND s.year = {season_year}
          AND g.week_number < {max_week}
          AND g.status = 'Final'
    """, conn)
    if h2h_games.empty:
        return 0.5  # Wenn keine direkten Duelle, dann 50%
    win_rate = h2h_games['home_win'].mean()
    return win_rate

def prepare_features(games, season_year, max_week):
    conn = sqlite3.connect(DATABASE)
    
    # Zielvariable erstellen
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)

    # Zielvariable für Regression (Spread)
    games['point_spread'] = games['home_score'] - games['away_score']
    
    # Durchschnittliche Punkte
    games['home_team_avg_points'] = games['home_team_id'].apply(
        lambda x: calculate_avg_points(x, conn, season_year, max_week)
    )
    games['away_team_avg_points'] = games['away_team_id'].apply(
        lambda x: calculate_avg_points(x, conn, season_year, max_week)
    )
    
    # Zugelassene Punkte
    games['home_team_avg_allowed'] = games['home_team_id'].apply(
        lambda x: calculate_avg_allowed_points(x, conn, season_year, max_week)
    )
    games['away_team_avg_allowed'] = games['away_team_id'].apply(
        lambda x: calculate_avg_allowed_points(x, conn, season_year, max_week)
    )
    
    # Aktuelle Form
    games['home_team_form'] = games['home_team_id'].apply(
        lambda x: calculate_recent_form(x, conn, season_year, max_week)
    )
    games['away_team_form'] = games['away_team_id'].apply(
        lambda x: calculate_recent_form(x, conn, season_year, max_week)
    )
    
    # Heim- und Auswärtsbilanz
    games['home_team_home_win_pct'] = games['home_team_id'].apply(
        lambda x: calculate_home_win_percentage(x, conn, season_year, max_week)
    )
    games['away_team_away_win_pct'] = games['away_team_id'].apply(
        lambda x: calculate_away_win_percentage(x, conn, season_year, max_week)
    )
    
    # Direkte Duelle
    games['head_to_head'] = games.apply(
        lambda row: calculate_head_to_head(row['home_team_id'], row['away_team_id'], conn, season_year, max_week),
        axis=1
    )
    
    # Indoor/Outdoor
    games['indoor_stadium'] = games['indoor_stadium'].astype(int)
    
    # Feature-Erstellung
    features = games[[
        'home_team_avg_points',
        'away_team_avg_points',
        'home_team_avg_allowed',
        'away_team_avg_allowed',
        'home_team_form',
        'away_team_form',
        'home_team_home_win_pct',
        'away_team_away_win_pct',
        'head_to_head',
        'indoor_stadium'
    ]]
    
    target_classification = games['home_win']
    target_regression = games['point_spread']
    
    conn.close()
    return features, target_classification, target_regression


def train_model(features, target_classification, target_regression):
    # Fehlende Werte auffüllen (falls vorhanden)
    features = features.fillna(0)
    
    # Features skalieren
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Aufteilen in Trainings- und Testdaten
    X_train, X_test, y_train_cls, y_test_cls = train_test_split(features_scaled, target_classification, test_size=0.2, random_state=42)
    y_train_reg, y_test_reg = train_test_split(target_regression, test_size=0.2, random_state=42)
    
    # Klassifikationsmodell erstellen und trainieren
    model_cls = LogisticRegression(max_iter=1000)
    model_cls.fit(X_train, y_train_cls)
    
    # Regressionsmodell erstellen und trainieren
    model_reg = LinearRegression()
    model_reg.fit(X_train, y_train_reg)
    
    # Evaluierung
    score_cls = model_cls.score(X_test, y_test_cls)
    score_reg = model_reg.score(X_test, y_test_reg)
    print(f"Model Classification Accuracy: {score_cls:.2f}")
    print(f"Model Regression R^2 Score: {score_reg:.2f}")
    
    # Koeffizienten extrahieren
    feature_names = features.columns
    coefficients_cls = model_cls.coef_[0]
    coefficients_reg = model_reg.coef_
    
    coef_df_cls = pd.DataFrame({'Feature': feature_names, 'Coefficient': coefficients_cls})
    coef_df_reg = pd.DataFrame({'Feature': feature_names, 'Coefficient': coefficients_reg})
    
    # print("Klassifikationsmodell Koeffizienten:")
    # print(coef_df_cls)
    # print("Regressionsmodell Koeffizienten:")
    # print(coef_df_reg)
    
    return model_cls, model_reg, scaler


def predict_game(model_cls, model_reg, scaler, game_id, season_year, max_week=None):
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
        WHERE g.id = {game_id} AND s.year = {season_year}
    """
    game = pd.read_sql_query(query, conn)
    
    if game.empty:
        print(f"Spiel mit ID {game_id} in Saison {season_year} wurde nicht gefunden.")
        conn.close()
        return
    
    game = game.iloc[0]
    home_team_id = game['home_team_id']
    away_team_id = game['away_team_id']
    home_team_name = game['home_team_name']
    away_team_name = game['away_team_name']
    indoor_stadium = int(game['indoor_stadium'])
    week = game['week_number']
    
    # Features berechnen
    home_team_avg_points = calculate_avg_points(home_team_id, conn, season_year, week)
    away_team_avg_points = calculate_avg_points(away_team_id, conn, season_year, week)
    home_team_avg_allowed = calculate_avg_allowed_points(home_team_id, conn, season_year, week)
    away_team_avg_allowed = calculate_avg_allowed_points(away_team_id, conn, season_year, week)
    home_team_form = calculate_recent_form(home_team_id, conn, season_year, week)
    away_team_form = calculate_recent_form(away_team_id, conn, season_year, week)
    home_team_home_win_pct = calculate_home_win_percentage(home_team_id, conn, season_year, week)
    away_team_away_win_pct = calculate_away_win_percentage(away_team_id, conn, season_year, week)
    head_to_head = calculate_head_to_head(home_team_id, away_team_id, conn, season_year, week)
    
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
    
    # Vorhersage des Spreads
    predicted_spread = model_reg.predict(features_scaled)[0]
    
    print(f"Spiel: {home_team_name} vs. {away_team_name}")
    print(f"Vorhergesagter Gewinner: {predicted_winner} mit Wahrscheinlichkeit {predicted_prob:.2%}")
    print(f"Vorhergesagter Spread (Handicap aus Sicht des Heimteams): {predicted_spread:.2f} Punkte")
    
    conn.close()
    return probability


def predict_week_games(model_cls, model_reg, scaler, week, season_year):
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
    
    # Öffne die Datei zum Schreiben
    with open(f"Vorhersagen_Woche_{week}_{season_year}.txt", "w", encoding="utf-8") as file:
        # Für jedes Spiel Vorhersage durchführen
        for index, game in games.iterrows():
            total_games += 1
            home_team_id = game['home_team_id']
            away_team_id = game['away_team_id']
            home_team_name = game['home_team_name']
            away_team_name = game['away_team_name']
            indoor_stadium = int(game['indoor_stadium'])
            
            # Features berechnen
            home_team_avg_points = calculate_avg_points(home_team_id, conn, season_year, week)
            away_team_avg_points = calculate_avg_points(away_team_id, conn, season_year, week)
            home_team_avg_allowed = calculate_avg_allowed_points(home_team_id, conn, season_year, week)
            away_team_avg_allowed = calculate_avg_allowed_points(away_team_id, conn, season_year, week)
            home_team_form = calculate_recent_form(home_team_id, conn, season_year, week)
            away_team_form = calculate_recent_form(away_team_id, conn, season_year, week)
            home_team_home_win_pct = calculate_home_win_percentage(home_team_id, conn, season_year, week)
            away_team_away_win_pct = calculate_away_win_percentage(away_team_id, conn, season_year, week)
            head_to_head = calculate_head_to_head(home_team_id, away_team_id, conn, season_year, week)
            
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
            
            # Vorhersage des Spreads
            predicted_spread = model_reg.predict(features_scaled)[0]
            
            # Ausgabe des Ergebnisses
            result_str = f"Woche {week} - Spiel: {home_team_name} vs. {away_team_name}\n"
            result_str += f"Vorhergesagter Gewinner: {predicted_winner} mit Wahrscheinlichkeit {predicted_prob:.2%}\n"
            result_str += f"Vorhergesagter Spread (Handicap aus Sicht des Heimteams): {predicted_spread:.2f} Punkte\n"
            
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
