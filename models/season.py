# models/season.py
class Season:
    def __init__(self, id, year, start_date, end_date, display_name, type_id, type_name, type_abbreviation):
        self.id = id
        self.year = year
        self.start_date = start_date
        self.end_date = end_date
        self.display_name = display_name
        self.type_id = type_id
        self.type_name = type_name
        self.type_abbreviation = type_abbreviation

    @classmethod
    def from_json(cls, data):
        season_data = data['leagues'][0]['season']
        return cls(
            id=season_data['year'],
            year=season_data['year'],
            start_date=season_data['startDate'],
            end_date=season_data['endDate'],
            display_name=season_data['displayName'],
            type_id=int(season_data['type']['id']),
            type_name=season_data['type']['name'],
            type_abbreviation=season_data['type']['abbreviation']
        )
