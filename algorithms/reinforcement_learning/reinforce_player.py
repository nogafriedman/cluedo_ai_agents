from game_elements.cluedo_player import CluedoPlayer
from algorithms.reinforcement_learning.reinforce_player_trainer import ReinforcePlayerTrainer
from game_elements.action import Action
from game_elements.game_state import GameState
from algorithms.reinforcement_learning.state_encoder import StateEncoder
import random

class ReinforcePlayer(CluedoPlayer):
    def __init__(self, trained_player: ReinforcePlayerTrainer, index, name):
        super().__init__(index, name)
        self.player = trained_player
        self.game_manager = None
        self.encoder = None

    def set_encoder(self, game_manager):
        self.encoder = StateEncoder(game_manager)
        self.game_manager = game_manager

    def play_turn(self, state: GameState):
        # Encode the state
        encoded_state = self.encoder.encode(state)

        # Get the action probabilities from the policy network
        actions, probs = self.player.select_action(encoded_state)

        # Determine the current player's index and generate a random dice roll
        current_player_index = state._player_index
        dice_roll = random.randint(1, 6)

        # Get all possible actions for the current state and dice roll
        possible_actions = state.get_all_possible_actions(current_player_index, dice_roll)

        # Iterate through actions in order of probability
        for action in actions:
            decoded_action = self.encoder.decode_action(action.item())
            if decoded_action in possible_actions:
                return decoded_action

        # If no valid action is found (which shouldn't happen), return a random valid action
        return random.choice(possible_actions)
    
    def reject(self, state: GameState):
        all_rejections = state.get_possible_rejections(self.get_cards(), state._active_suggestion)
        if all_rejections:
            return random.choice(all_rejections)
        return None