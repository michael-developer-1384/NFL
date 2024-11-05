import sqlite3
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from . import utils

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

def prepare_features(games, season_year, max_week):
    conn = sqlite3.connect(DATABASE)

    # Zielvariable erstellen
    games['home_win'] = (games['home_score'] > games['away_score']).astype(int)

    # Durchschnittliche Punkte
    games['home_team_avg_points'] = games['home_team_id'].apply(
        lambda x: utils.calculate_avg_points(x, conn, season_year, max_week)
    )
    games['away_team_avg_points'] = games['away_team_id'].apply(
        lambda x: utils.calculate_avg_points(x, conn, season_year, max_week)
    )

    # Zugelassene Punkte
    games['home_team_avg_allowed'] = games['home_team_id'].apply(
        lambda x: utils.calculate_avg_allowed_points(x, conn, season_year, max_week)
    )
    games['away_team_avg_allowed'] = games['away_team_id'].apply(
        lambda x: utils.calculate_avg_allowed_points(x, conn, season_year, max_week)
    )

    # Aktuelle Form
    games['home_team_form'] = games['home_team_id'].apply(
        lambda x: utils.calculate_recent_form(x, conn, season_year, max_week)
    )
    games['away_team_form'] = games['away_team_id'].apply(
        lambda x: utils.calculate_recent_form(x, conn, season_year, max_week)
    )

    # Heim- und Auswärtsbilanz
    games['home_team_home_win_pct'] = games['home_team_id'].apply(
        lambda x: utils.calculate_home_win_percentage(x, conn, season_year, max_week)
    )
    games['away_team_away_win_pct'] = games['away_team_id'].apply(
        lambda x: utils.calculate_away_win_percentage(x, conn, season_year, max_week)
    )

    # Direkte Duelle
    games['head_to_head'] = games.apply(
        lambda row: utils.calculate_head_to_head(row['home_team_id'], row['away_team_id'], conn, season_year, max_week),
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

    conn.close()
    return features, target_classification

def train_model(features, target_classification):
    # Fehlende Werte auffüllen (falls vorhanden)
    features = features.fillna(0)

    # Features skalieren
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Aufteilen in Trainings- und Testdaten
    X_train, X_test, y_train_cls, y_test_cls = train_test_split(features_scaled, target_classification, test_size=0.2, random_state=42)

    # Klassifikationsmodell erstellen und trainieren
    model_cls = LogisticRegression(max_iter=1000)
    model_cls.fit(X_train, y_train_cls)

    # Evaluierung
    score_cls = model_cls.score(X_test, y_test_cls)
    print(f"Model Classification Accuracy: {score_cls:.2f}")

    return model_cls, scaler
