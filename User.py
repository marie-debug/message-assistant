import json
from datetime import datetime, timedelta


class User:
    def __init__(self, id, type, name, phone_number, relation, error):
        self.Id = id
        self.Type = type
        self.Name = name
        self.PhoneNumber = phone_number
        self.Relation = relation
        self.ExpirationTime = str(int((datetime.utcnow() + timedelta(hours=24)).timestamp()))
        self.Error = str(error)

    def __repr__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
