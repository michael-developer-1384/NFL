# fetchers/teams_fetcher.py
import requests
from db import database
from models.team import Team
from models.venue import Venue

def fetch_teams(override=False):
    api_url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams?lang=en&region=us&limit=32"

    response = requests.get(api_url)
    if response.status_code == 200:
        teams_data = response.json()
        team_refs = [item["$ref"] for item in teams_data["items"]]

        for team_ref in team_refs:
            try:
                # Abrufen der Teamdaten über den $ref-Link
                team_response = requests.get(team_ref)
                if team_response.status_code == 200:
                    team_info = team_response.json()

                    # Team-Objekt erstellen
                    team = Team.from_json(team_info)

                    # Venue-Objekt erstellen, falls vorhanden
                    venue = None
                    if "venue" in team_info and team_info["venue"]:
                        venue_ref = team_info["venue"].get("$ref")
                        if venue_ref:
                            venue_response = requests.get(venue_ref)
                            if venue_response.status_code == 200:
                                venue_info = venue_response.json()
                                venue = Venue.from_json(venue_info)
                            else:
                                print(f"Fehler beim Abrufen der Venue-Daten für Team {team.displayName}")
                        else:
                            print(f"Kein Venue-Link für Team {team.displayName} vorhanden.")

                    # Speichern in der Datenbank
                    database.save_team_and_venue(team, venue, override)
                    print(f"Team '{team.displayName}' wurde erfolgreich gespeichert.")
                else:
                    print(f"Fehler beim Abrufen des Teams: {team_ref}")
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten bei der Verarbeitung von Team {team_ref}: {e}")
    else:
        print(f"Fehler beim Abrufen der Teamliste: {response.status_code}")
