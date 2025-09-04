import json, os

class PersonalityMemory:
    def __init__(self, filepath="personality.json"):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {
            "mood": "neutral",
            "mood_triggers": {
                "low_battery": "grumpy",
                "petting": "happy",
                "long_idle": "bored"
            }
        }

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def set_mood(self, mood):
        self.data["mood"] = mood
        self.save()

    def get_mood(self):
        return self.data["mood"]

    def react_to_trigger(self, trigger):
        if trigger in self.data["mood_triggers"]:
            self.data["mood"] = self.data["mood_triggers"][trigger]
            self.save()
