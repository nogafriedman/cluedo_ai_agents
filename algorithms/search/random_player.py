from game_elements.cluedo_player import CluedoPlayer
from game_elements.game_state import GameState
from game_elements.action import Action
import random

MAX_DICE_ROLL = 6
ACCUSATION_PROB = 0.001

class RandomPlayer(CluedoPlayer):
    def __init__(self, player_index, name):
        super().__init__(player_index, name)
        self._player_index = player_index
    
    def get_possible_actions(self, state: GameState):
        dice_roll = random.randint(1, 6)
        return state.get_all_possible_actions(self._player_index, dice_roll)
    
    def play_turn(self, state: GameState):
        all_actions = self.get_possible_actions(state)
        move = random.choice(all_actions)
        probs = [1]* len(all_actions)
        for i, action in enumerate(all_actions):
            if action[0] == Action.ACCUSATION:
                probs[i] = ACCUSATION_PROB
        move = random.choices(all_actions, weights=probs, k=1)[0]
        return move[0], move[1]
    
    def reject(self, state: GameState):
        all_rejections = state.get_possible_rejections(self.get_cards(), state._active_suggestion)
        if all_rejections:
            return random.choice(all_rejections)
        return None