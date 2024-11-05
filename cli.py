import argparse
from fetchers import games_fetcher, teams_fetcher
from models_training import training, prediction

def main_cli(args):
    parser = argparse.ArgumentParser(description="NFL Daten Fetcher CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser für den 'fetch' Befehl
    fetch_parser = subparsers.add_parser("fetch", help="Daten abrufen")
    fetch_subparsers = fetch_parser.add_subparsers(dest="fetch_command")

    # Subparser für 'fetch games'
    games_parser = fetch_subparsers.add_parser("games", help="Spieldaten abrufen")
    games_parser.add_argument("--year", type=int, required=True, help="Jahr der Saison")
    games_parser.add_argument("--override", action="store_true", help="Vorhandene Daten überschreiben")

    # Subparser für 'fetch teams'
    teams_parser = fetch_subparsers.add_parser("teams", help="Teamdaten abrufen")
    teams_parser.add_argument("--override", action="store_true", help="Vorhandene Daten überschreiben")

    # Subparser für den 'predict' Befehl
    predict_parser = subparsers.add_parser("predict", help="Spielvorhersage")
    predict_subparsers = predict_parser.add_subparsers(dest="predict_command")

    # Subparser für 'predict game'
    predict_game_parser = predict_subparsers.add_parser("game", help="Vorhersage für ein Spiel")
    predict_game_parser.add_argument("--game_id", type=int, required=True, help="ID des Spiels")

    # Subparser für 'predict week'
    predict_week_parser = predict_subparsers.add_parser("week", help="Vorhersage für eine bestimmte Woche")
    predict_week_parser.add_argument("--week", type=int, required=True, help="Nummer der Woche")
    predict_week_parser.add_argument("--season", type=int, required=True, help="Jahr der Saison")

    parsed_args = parser.parse_args(args)

    if parsed_args.command == "fetch":
        if parsed_args.fetch_command == "games":
            games_fetcher.fetch_games(parsed_args.year, parsed_args.override)
        elif parsed_args.fetch_command == "teams":
            teams_fetcher.fetch_teams(parsed_args.override)
        else:
            fetch_parser.print_help()
    elif parsed_args.command == "predict":
        if parsed_args.predict_command == "game":
            # Modelltraining und Vorhersage für ein Spiel
            print("Lade Daten und trainiere das Modell...")
            # Saisonjahr und Woche anhand der Spiel-ID ermitteln
            season_year, week_number = prediction.get_season_year_and_week(parsed_args.game_id)
            if season_year is None or week_number is None:
                print(f"Konnte das Spiel mit ID {parsed_args.game_id} nicht finden.")
                return
            max_week = week_number  # Spiele dieser Woche und danach vom Training ausschließen
            games = training.load_data(max_week=max_week, season_year=season_year)
            features, target_classification = training.prepare_features(games, season_year, max_week)
            model_cls, scaler = training.train_model(features, target_classification)
            prediction.predict_game(model_cls, scaler, parsed_args.game_id)
        elif parsed_args.predict_command == "week":
            # Modelltraining und Vorhersage für angegebene Woche und Saison
            print("Lade Daten und trainiere das Modell...")
            max_week = parsed_args.week  # Spiele dieser Woche und danach vom Training ausschließen
            season_year = parsed_args.season
            games = training.load_data(max_week=max_week, season_year=season_year)
            features, target_classification = training.prepare_features(games, season_year, max_week)
            model_cls, scaler = training.train_model(features, target_classification)
            prediction.predict_week_games(model_cls, scaler, parsed_args.week, season_year)
        else:
            predict_parser.print_help()
    else:
        parser.print_help()
