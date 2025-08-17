from game_elements.action import Action
from game_elements.game_state import GameState

class CluedoPlayer():
    def __init__(self, index, name):
        self.name = name
        self._location = (0,0)
        self._room = None  # todo ADDED
        self._cards = set()
        self.cards_i_showed = set()
        self.cards_rejected_for_me = set()
        self.cards_no_one_could_reject_for_me = set()
        self.cards_i_asked = set()
        self.cards_i_was_asked = set()
        self._index = index
        self.active_suggestion = False
        self.is_in_game = True

    def init_knowledge(self, num_players):  # todo ADDED 13.9
        pass

    def reset_knowledge(self):  # todo ADDED 13.9
        pass
    
    # Getter and Setter for position
    def get_location(self):
        return self._location

    def set_location(self, location):
        self._location = location

    def get_room(self):  # todo ADDED
        return self._room

    def set_room(self, room):  # todo ADDED
        self._room = room

    # Getter and Setter for cards
    def get_cards(self):
        return self._cards

    def add_cards(self, cards):
        for card in cards:
            self._cards.add(card)

    # Getter and Setter for position
    def get_index(self):
        return self._index

    """
    Returns the chosen move:
    1. A string - "move" / "suggestion" / "accusation"
    2. A dict of {Weapon: , Suspect: , Room_index: }, or null (if "move" was chosen)
    """
    def play_turn(self, state: GameState):
        pass

    def reject(self, state: GameState):
        pass

    def handle_suggestion_response(self, state: GameState):
        pass

    def handle_accusation_response(self, state: GameState): 
        pass