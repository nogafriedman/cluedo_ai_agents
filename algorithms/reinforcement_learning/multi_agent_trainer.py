import random
import torch
import torch.nn as nn
import torch.optim as optim
from game_elements.cluedo_game_manager import CluedoGameManager
from game_elements.game_state import GameState
from algorithms.reinforcement_learning.reinforce_player_trainer import ReinforcePlayerTrainer
from algorithms.reinforcement_learning.state_encoder import StateEncoder
from game_elements.action import Action
import copy


class OpponentModel(nn.Module):
    def __init__(self, input_size, output_size):
        super(OpponentModel, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.softmax(self.fc3(x), dim=-1)

class MultiAgentReinforceTrainer:
    def __init__(self, game_manager: CluedoGameManager, num_agents, lr=0.001):
        self._game_manager = game_manager
        self._num_agents = num_agents
        self._input_size = self._calculate_input_size()
        self._output_size = self._calculate_output_size()

        self._agents = [ReinforcePlayerTrainer(self._input_size, self._output_size, lr) for _ in range(num_agents)]
        self._opponent_models = [OpponentModel(self._input_size, self._output_size) for _ in range(num_agents)]
        self._encoder = StateEncoder(game_manager)

    def _calculate_input_size(self):
        return 2 + 10 + 10 * len(self._game_manager.cards) + 1 + 1 + 1 + 1        
        
    def _calculate_output_size(self):
        board_size = self._game_manager.game_board.get_size()
        card_combinations = len(self._game_manager.suspects) * len(self._game_manager.weapons) * len(self._game_manager.rooms)
        return 2 * card_combinations + 1 + board_size * board_size

    def reset_game(self):
        self._game_manager = CluedoGameManager(suspects=self._game_manager.suspects, weapons=
                                               self._game_manager.weapons, rooms=self._game_manager.rooms, players=self._game_manager.players, 
                                               game_board=self._game_manager.game_board, test_mode=self._game_manager.test_mode)
        return self._game_manager.create_current_state()

    def train(self, episodes):
        for episode in range(episodes):
            print(f"Starting training episode {episode}")
            state = self.reset_game()
            done = False
            
            while not done:
                for agent_index in range(self._num_agents):
                    if not state.is_terminal:
                        state, _, done = self.play_step(state, agent_index)

            # Update policies for all agents
            for agent in self._agents:
                agent.update_policy()



    def play_step(self, state: GameState, agent_index):
        encoded_state = self._encoder.encode(state)
        action = self._agents[agent_index].select_action(encoded_state)
        decoded_action = self._encoder.decode_action(action)
        
        new_state = self.simulate_action(state, agent_index, decoded_action)
        reward = new_state.get_score()
        
        self._agents[agent_index].rewards.append(reward)
        
        done = new_state.is_terminal
        
        if not done:
            new_state._player_index = new_state.get_next_active_player(agent_index)
            
            while new_state._player_index != agent_index and not new_state.is_terminal:
                opponent_action = self.simulate_opponent_action(new_state, new_state._player_index)
                new_state = self.simulate_action(new_state, new_state._player_index, opponent_action)
                if not new_state.is_terminal:
                    new_state._player_index = new_state.get_next_active_player(new_state._player_index)
        
        return new_state, reward, done

    def simulate_action(self, state: GameState, player_index: int, action: Action):
        new_state = copy.deepcopy(state)
        
        if action[0] == Action.MOVE:
            new_state.apply_move(action[1])
        elif action[0] == Action.SUGGESTION:
            new_state.apply_suggestion(action[1])
            rejected_card = self.random_reject(new_state, player_index)
            if rejected_card:
                new_state._players[player_index].cards_rejected_for_me.add(rejected_card)
            else:
                for card in new_state._active_suggestion:
                    if card not in new_state._players[player_index]._cards:
                        new_state._players[player_index].cards_no_one_could_reject_for_me.add(card)
        elif action[0] == Action.ACCUSATION:
            new_state.apply_accusation(action[1])
            result = self.random_accusation(new_state, player_index)
            if result:
                new_state.winner = player_index
                new_state.is_terminal = True
            else:
                new_state._players[player_index].is_in_game = False
                # Check if game ended
                active_players = sum(1 for player in new_state._players if player.is_in_game)
                if active_players <= 1:
                    new_state.is_terminal = True
                    new_state.winner = next(i for i, player in enumerate(new_state._players) if player.is_in_game)
        elif action[0] == Action.ENDTURN:
            new_state.apply_end_turn()
        
        return new_state

    def update_opponent_models(self, episode_rewards, episode_log_probs):
        # Update opponent models based on observed behavior of other agents
        for i in range(self._num_agents):
            for j in range(self._num_agents):
                if i != j:
                    # Update opponent model i's perception of agent j
                    self.update_single_opponent_model(i, j, episode_rewards[j], episode_log_probs[j])

    def update_opponent_models(self, episode_rewards, episode_log_probs):
        for i in range(self._num_agents):
            for j in range(self._num_agents):
                if i != j:
                    self.update_single_opponent_model(i, j, episode_rewards[j], episode_log_probs[j])


    def simulate_opponent_action(self, state, opponent_index):
        encoded_state = self._encoder.encode(state)
        action_probs = self._opponent_models[opponent_index](torch.FloatTensor(encoded_state))
        action = torch.multinomial(action_probs, 1).item()
        return self._encoder.decode_action(action)



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

