# cli.py
import argparse
from fetchers import games_fetcher, teams_fetcher

def main_cli(args):
    parser = argparse.ArgumentParser(description="NFL Daten Fetcher CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser für den 'fetch' Befehl
    fetch_parser = subparsers.add_parser("fetch", help="Daten abrufen")
    fetch_subparsers = fetch_parser.add_subparsers(dest="fetch_command")

    # Subparser für 'fetch teams'
    teams_parser = fetch_subparsers.add_parser("teams", help="Teamdaten abrufen")
    teams_parser.add_argument("--override", action="store_true", help="Vorhandene Daten überschreiben")
    
    # Subparser for 'fetch games'
    games_parser = fetch_subparsers.add_parser("games", help="Spieldaten abrufen")
    games_parser.add_argument("--year", type=int, required=True, help="Jahr der Saison")
    games_parser.add_argument("--override", action="store_true", help="Vorhandene Daten überschreiben")

    parsed_args = parser.parse_args(args)

    if parsed_args.command == "fetch":
        if parsed_args.fetch_command == "games":
            games_fetcher.fetch_games(parsed_args.year)
        elif parsed_args.fetch_command == "teams":
            teams_fetcher.fetch_teams(parsed_args.override)
        else:
            fetch_parser.print_help()
    else:
        parser.print_help()
