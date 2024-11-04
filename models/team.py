# models/team.py
class Team:
    def __init__(self, id, location, name, abbreviation, displayName, color, alternateColor, isActive, venue_id):
        self.id = id
        self.location = location
        self.name = name
        self.abbreviation = abbreviation
        self.displayName = displayName
        self.color = color
        self.alternateColor = alternateColor
        self.isActive = isActive
        self.venue_id = venue_id  # Foreign Key zu Venue

    @classmethod
    def from_json(cls, data):
        return cls(
            id=int(data.get("id")),
            location=data.get("location"),
            name=data.get("name"),
            abbreviation=data.get("abbreviation"),
            displayName=data.get("displayName"),
            color=data.get("color"),
            alternateColor=data.get("alternateColor"),
            isActive=data.get("isActive"),
            venue_id=int(data.get("venue", {}).get("id")) if data.get("venue") else None
        )
