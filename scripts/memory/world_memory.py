import json, os

class WorldMemory:
    def __init__(self, filepath="world.json"):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"obstacle_map": [], "safe_zones": [], "charging_station": {"x": 0, "y": 0}}

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def add_obstacle(self, x, y, obj_type):
        self.data["obstacle_map"].append({"x": x, "y": y, "type": obj_type})
        self.save()

    def add_safe_zone(self, zone_name):
        if zone_name not in self.data["safe_zones"]:
            self.data["safe_zones"].append(zone_name)
        self.save()

    def set_charging_station(self, x, y):
        self.data["charging_station"] = {"x": x, "y": y}
        self.save()
