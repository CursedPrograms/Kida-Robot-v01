import json, os, datetime

class SystemMemory:
    def __init__(self, filepath="system.json"):
        self.filepath = filepath
        self.data = self._load()
        self.increment_boots()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"boot_count": 0, "last_boot": None, "uptime_total": 0, "battery_cycles": 0}

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def increment_boots(self):
        self.data["boot_count"] += 1
        self.data["last_boot"] = str(datetime.datetime.now())
        self.save()

    def add_uptime(self, seconds):
        self.data["uptime_total"] += seconds
        self.save()

    def add_battery_cycle(self):
        self.data["battery_cycles"] += 1
        self.save()
