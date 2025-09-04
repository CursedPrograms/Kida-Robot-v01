import json, os

class UserMemory:
    def __init__(self, filepath="user.json"):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"favorite_greetings": [], "last_user_command": None, "times_petted": 0}

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_greeting(self, greeting):
        if greeting not in self.data["favorite_greetings"]:
            self.data["favorite_greetings"].append(greeting)
        self.save()

    def set_last_command(self, command):
        self.data["last_user_command"] = command
        self.save()

    def pet(self):
        self.data["times_petted"] += 1
        self.save()
