class Room():
    def __init__(self, location: tuple[int], name: str):
        self._location = location
        self._name = name
    
    def get_name(self):
        return self._name
    
    def set_name(self, name):
        self._name = name
    
    def get_location(self):
        return self._location