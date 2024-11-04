# models/venue.py
class Venue:
    def __init__(self, id, fullName, city, state, zipCode, grass, indoor):
        self.id = id
        self.fullName = fullName
        self.city = city
        self.state = state
        self.zipCode = zipCode
        self.grass = grass
        self.indoor = indoor

    @classmethod
    def from_json(cls, data):
        if not data:
            return None
        address = data.get("address", {})
        return cls(
            id=int(data.get("id")),
            fullName=data.get("fullName"),
            city=address.get("city"),
            state=address.get("state"),
            zipCode=address.get("zipCode"),
            grass=data.get("grass"),
            indoor=data.get("indoor")
        )
