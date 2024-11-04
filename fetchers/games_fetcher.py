# fetchers/games_fetcher.py
import requests
from db import database
from models.season import Season
from models.game import Game

def fetch_games(year, override=False):
    api_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}"

    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        # Saison extrahieren und speichern
        season = Season.from_json(data)
        database.save_season(season, override)

        # Spiele extrahieren und speichern
        events = data.get('events', [])
        for event in events:
            try:
                game = Game.from_json(event, season.id)
                database.save_game(game, override)
                print(f"Spiel '{game.id}' wurde gespeichert.")
            except Exception as e:
                print(f"Fehler beim Verarbeiten des Spiels {event.get('id')}: {e}")
    else:
        print(f"Fehler beim Abrufen der Spiele: {response.status_code}")
