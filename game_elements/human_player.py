from game_elements.cluedo_player import CluedoPlayer
from game_elements.game_state import GameState
import random

class HumanPlayer(CluedoPlayer):
    def __init__(self, index, name):
        super().__init__(index=index, name=name)
    
    """
    Returns the chosen move:
    1. A string - "move" / "suggestion" / "accusation"
    2. A dict of {Weapon: , Suspect: , Room_index: }, or null (if "move" was chosen)
    """
    def play_move(self, game_state: GameState):
        # Open UI
        pass

    def reject(self, state: GameState):
        all_rejections = state.get_possible_rejections(self.get_cards(), state._active_suggestion)
        if all_rejections:
            return random.choice(all_rejections)
        return None