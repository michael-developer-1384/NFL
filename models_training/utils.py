import pandas as pd

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
