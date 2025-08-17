class Card():
    def __init__(self, type, name):
        self._type = type
        self._name = name
        self._holder = None  # None if unknown, a player if known, something else if found to be in the solution todo: ADDED

    def __deepcopy__(self, memo):
        # Return the same instance instead of creating a new one
        return self
    

    def get_type(self):
        return self._type
    
    def get_name(self):
        return self._name

    def get_holder(self):
        return self._holder

    def set_holder(self, holder):
        self._holder = holder