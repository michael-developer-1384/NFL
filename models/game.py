# models/game.py
class Game:
    def __init__(self, id, season_id, week_number, date, venue_id, home_team_id, away_team_id, home_score, away_score, winner_team_id, status, attendance, broadcast):
        self.id = id
        self.season_id = season_id
        self.week_number = week_number
        self.date = date
        self.venue_id = venue_id
        self.home_team_id = home_team_id
        self.away_team_id = away_team_id
        self.home_score = home_score
        self.away_score = away_score
        self.winner_team_id = winner_team_id
        self.status = status
        self.attendance = attendance
        self.broadcast = broadcast

    @classmethod
    def from_json(cls, data, season_id):
        competition = data['competitions'][0]
        date = data['date']
        week_number = data['week']['number']
        venue_id = competition['venue']['id']
        attendance = competition.get('attendance')
        broadcast = competition.get('broadcast', '')

        # Get competitors
        competitors = competition['competitors']
        home_competitor = next(c for c in competitors if c['homeAway'] == 'home')
        away_competitor = next(c for c in competitors if c['homeAway'] == 'away')

        # Scores
        home_score = int(home_competitor['score'])
        away_score = int(away_competitor['score'])

        # Winner
        winner_competitor = next((c for c in competitors if c.get('winner')), None)
        winner_team_id = int(winner_competitor['team']['id']) if winner_competitor else None

        # Status
        status = competition['status']['type']['description']

        return cls(
            id=int(data['id']),
            season_id=season_id,
            week_number=week_number,
            date=date,
            venue_id=int(venue_id),
            home_team_id=int(home_competitor['team']['id']),
            away_team_id=int(away_competitor['team']['id']),
            home_score=home_score,
            away_score=away_score,
            winner_team_id=winner_team_id,
            status=status,
            attendance=attendance,
            broadcast=broadcast
        )
