from datetime import datetime, timedelta


class User:
    def __init__(self, id, type, name, phone_number, relation, error):
        self.Id = id
        self.Type = type
        self.Name = name
        self.PhoneNumber = phone_number
        self.Relation = relation
        self.ExpirationTime = str(int((datetime.utcnow() + timedelta(hours=24)).timestamp()))
        self.Error = error
