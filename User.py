import copy
import json
from datetime import datetime, timedelta


class User:
    def __init__(self, id, name, phone_number, relation, error, conversation, age):
        self.Id = id
        self.Name = name
        self.PhoneNumber = phone_number
        self.Relation = relation
        self.ExpirationTime = str(int((datetime.utcnow() + timedelta(hours=24)).timestamp()))
        self.Conversation = conversation
        self.Error = str(error)
        self.Age = age

    def __repr__(self):
        return json.dumps(self, skipkeys=True, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __str__(self):
        # c = copy.deepcopy(self)
        # c.Conversations = ["conversation length is: {}".format(len(self.Conversation))]
        return json.dumps(self, skipkeys=True, default=lambda o: o.__dict__, sort_keys=True, indent=4)
