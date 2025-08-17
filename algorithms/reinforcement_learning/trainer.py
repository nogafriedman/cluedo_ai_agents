from game_elements.cluedo_game_manager import CluedoGameManager
from algorithms.reinforcement_learning.state_encoder import StateEncoder
from algorithms.reinforcement_learning.reinforce_player_trainer import ReinforcePlayerTrainer
from game_elements.game_state import GameState
from game_elements.action import Action
import torch
import copy
import random

# Max dice roll
DICE_ROLL = 6

class ReinforceTrainer:
    def __init__(self, game_manager: CluedoGameManager, lr=0.001):
        self._game_manager = game_manager

        """
        encoding = (player_location_encoded + 
                    opponent_locations + 
                    player_cards_encoded + 
                    player_showed_cards_encoded + 
                    player_rejected_cards_encoded + 
                    player_asked_cards_encoded + 
                    player_was_asked_cards_encoded + 
                    player_no_reject_cards_encoded + 
                    + all_suggestions_encoded +
                    + all_accusations_encoded +
                    active_suggestion_encoded + 
                    active_accusation_encoded + 
                    is_terminal_encoded +
                    current_player_encoding + winner_encoding + last_turn)
        """
        self._input_size = 2 + 10 + 10 * len(game_manager.cards) + 1 + 1 + 1 + 1
        
        # All possible suggestions (card_combinations), accusations (card_combinations), 
        # moves (for each position on the board), end_turn
        board_size = game_manager.game_board.get_size()
        card_combinations = len(game_manager.suspects) * len(game_manager.weapons) * len(game_manager.rooms)
        self._output_size = 2 * card_combinations + 1 + board_size * board_size
        self._encoder = StateEncoder(game_manager)
        self._player = ReinforcePlayerTrainer(self._input_size, self._output_size, lr)

    def reset_game(self):
        self._game_manager = CluedoGameManager(suspects=self._game_manager.suspects, weapons=
                                               self._game_manager.weapons, rooms=self._game_manager.rooms, players=self._game_manager.players, 
                                               game_board=self._game_manager.game_board, test_mode=self._game_manager.test_mode)
        return self._game_manager.create_current_state()
    
    def get_current_state(self):
        return self._game_manager.create_current_state()
    
    def play_step(self, actions, state: GameState):
        # Choosing the best action to perform
        action_index = 0
        dice_roll = random.randint(1, 6)
        possible_actions = state.get_all_possible_actions(state._player_index, dice_roll)
        for action in actions:
            action = actions.T[action_index].item()
            decoded_action = self._encoder.decode_action(action)
            if decoded_action in possible_actions:
                break
            action_index += 1
        
        action = self._encoder.decode_action(action)
        player_index = state._player_index
        
        # Simulating the state
        new_state = copy.deepcopy(state)
        if action[0] == Action.MOVE:
            new_state.apply_move(action[1])
        elif action[0] == Action.SUGGESTION:
            new_state.apply_suggestion(action[1])
            rejected_card = self.random_reject(new_state, player_index)
            if rejected_card:
                new_state._players[player_index].cards_rejected_for_me.add(rejected_card)
            else:
                if new_state._active_suggestion[0] not in new_state._players[player_index]._cards:
                    new_state._players[player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[0])
                if new_state._active_suggestion[1] not in new_state._players[player_index]._cards:
                    new_state._players[player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[1])
                if new_state._active_suggestion[2] not in new_state._players[player_index]._cards:
                    new_state._players[player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[2])

        if action[0] == Action.ACCUSATION:
            new_state.apply_accusation(action[1])
            result = self.random_accusation(new_state, player_index)
            if result:
                new_state.winner = player_index
                new_state.is_terminal = True
            else:
                new_state._players[player_index].is_in_game = False
                # Check if game ended
                active_players = 0
                active_player = None
                for player in new_state._players:
                    if player.is_in_game:
                        active_player = player
                        active_players += 1
                if active_players <= 1:
                    new_state.is_terminal = True
                    new_state.winner = active_player
                else:
                    new_state.next_turn()
                
        if action[0] == Action.ENDTURN:
            new_state.apply_end_turn()
        
        # Scoring/Reward
        new_player_index = new_state._player_index
        new_state._player_index = player_index
        score = new_state.get_score()
        new_state._player_index = new_player_index
        
        return new_state, score, new_state.is_terminal, action_index

    def train(self, episodes):
        for episode in range(episodes):
            print(f"starting training epoch {episode}")
            state = self.reset_game()
            encoded_state = self._encoder.encode(state)
            done = False
            episode_rewards = []
            episode_log_probs = []
            while not done:
                actions, action_probs = self._player.select_action(encoded_state)
                next_state, reward, done, action_index = self.play_step(actions, state)
                
                # Calculate log probability of the chosen action
                log_prob = torch.log(action_probs[action_index])
                
                # Store trajectory
                episode_rewards.append(reward)
                episode_log_probs.append(log_prob)
                
                state = next_state
                encoded_state = self._encoder.encode(next_state)
            
            # After episode ends, store the entire trajectory
            self._player.store_trajectory(episode_rewards, episode_log_probs)
            self._player.update_policy()

    
    def random_accusation(self, state: GameState, player_index):
        if state._active_accusation in state.all_accusations:
            return False
        num_of_cards_i_discovered = len(state._players[player_index].cards_rejected_for_me) + len(state._players[player_index].cards_no_one_could_reject_for_me)
        unknown_cards = len(state._cards) - len(state[player_index]._cards) - num_of_cards_i_discovered

        choices = [True, False]
        win_prob = [0.05, 0.95]
        if unknown_cards <= 5:
            win_prob = [0.2, 0.80]
        if unknown_cards <= 4:
            win_prob = [0.4, 0.60]
        if unknown_cards < 4:
            win_prob = [0.9, 0.10]
        choice = random.choices(choices, weights=[win_prob, 1 - win_prob])[0]
        return choice

    def random_reject(self, state: GameState, player_index):
        rejects = []
        suspects_num = 0
        rooms_num = 0
        weapons_num = 0
        for card in state._cards:
            if card.get_type() == 'suspect':
                suspects_num += 1
            if card.get_type() == 'weapon':
                weapons_num += 1
            if card.get_type() == 'room':
                rooms_num += 1
        suspects_rejected = 0
        rooms_rejected = 0
        weapons_rejected = 0
        for card in state._players[player_index].cards_rejected_for_me:
            if card.get_type() == 'suspect':
                suspects_rejected += 1
            if card.get_type() == 'weapon':
                weapons_rejected += 1
            if card.get_type() == 'room':
                rooms_rejected += 1
        
        for card in state._players[player_index]._cards:
            if card.get_type() == 'suspect':
                suspects_rejected += 1
            if card.get_type() == 'weapon':
                weapons_rejected += 1
            if card.get_type() == 'room':
                rooms_rejected += 1
                
        unknown_suspects = suspects_num - suspects_rejected
        unknown_weapons = weapons_num - weapons_rejected
        unknown_rooms = rooms_num - rooms_rejected

        for card in state._active_suggestion:
            if card in state._players[player_index].cards_rejected_for_me:
                return card
        for card in state._active_suggestion:
            if card not in state._players[player_index]._cards and card not in state._players[player_index].cards_no_one_could_reject_for_me:
                if (card.get_type() == 'suspect' and unknown_suspects > 1) or (card.get_type() == 'weapon' and unknown_weapons > 1) \
                    or (card.get_type() == 'room' and unknown_rooms > 1):
                    rejects.append(card)
        if not rejects:
            return None
    
        
        # Random choice
        known_cards = len(state._players[player_index].cards_rejected_for_me) + len(state._players[player_index].cards_no_one_could_reject_for_me) * 1.5
        rejection_prob = min(known_cards / len(state._cards) + 0.01, 1)
        rejects.append(None)
        reject_probs = [1] * len(rejects)
        reject_probs[-1] = rejection_prob


        return random.choices(rejects, weights=reject_probs)[0]

