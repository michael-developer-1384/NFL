# fetchers/games_fetcher.py
import requests
from db import database

def fetch_games(year):
    api_url = f"https://api.espn.com/v1/sports/football/nfl/games?year={year}"

    response = requests.get(api_url)
    if response.status_code == 200:
        games_data = response.json()
        print(games_data)  # Ausgabe in der Konsole

        # Speichern der Daten in der Datenbank
        database.save_games(games_data)
    else:
        print(f"Fehler beim Abrufen der Daten: {response.status_code}")
