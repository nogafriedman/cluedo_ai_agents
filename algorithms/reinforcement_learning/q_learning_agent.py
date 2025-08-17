from game_elements.cluedo_player import CluedoPlayer
from game_elements.game_state import GameState
from game_elements.action import Action
import random
import copy
from game_elements.cluedo_game_manager import CluedoGameManager

class QLearningPlayer(CluedoPlayer):
    def __init__(self, player_index, name, state_encoder, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        super().__init__(index=player_index, name=name)
        self._player_index = player_index
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.state_encoder = state_encoder
        self.q_table = {}

    def get_q_value(self, state: GameState, action):
        action = tuple(action)
        state_encoding = tuple(self.state_encoder.encode(state))
        if state_encoding not in self.q_table:
            self.q_table[state_encoding] = {}
        if action not in self.q_table[state_encoding]:
            self.q_table[state_encoding][action] = 0.0
        return self.q_table[state_encoding][action]

    def update_q_value(self, state: GameState, action, reward, next_state: GameState):
        action = tuple(action)
        state_encoding = tuple(self.state_encoder.encode(state))
        next_state_encoding = tuple(self.state_encoder.encode(next_state))
        
        if next_state_encoding not in self.q_table:
            self.q_table[next_state_encoding] = {}
        
        max_next_q = max(self.q_table[next_state_encoding].values()) if self.q_table[next_state_encoding] else 0
        
        current_q = self.get_q_value(state, action)
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state_encoding][action] = new_q

    def choose_action(self, state: GameState, possible_actions):
        if random.random() < self.epsilon:
            return random.choice(possible_actions)
        else:
            q_values = [self.get_q_value(state, action) for action in possible_actions]
            max_q = max(q_values)
            best_actions = [action for action, q_value in zip(possible_actions, q_values) if q_value == max_q]
            return random.choice(best_actions)

    def play_turn(self, state: GameState):
        possible_actions = state.get_all_possible_actions(self._player_index, random.randint(1, 6))
        chosen_action = self.choose_action(state, possible_actions)
        # return chosen_action[0], chosen_action[1]
        
        # Apply the chosen action and get the next state
        next_state = self.apply_action(state, chosen_action)
        
        # Calculate reward
        reward = next_state.get_score()
        
        # Update Q-value
        self.update_q_value(state, chosen_action, reward, next_state)
        
        return chosen_action[0], chosen_action[1]

    def apply_action(self, state: GameState, action):
        player_index = state._player_index
        new_state = copy.deepcopy(state)
        if action[0] == Action.MOVE:
            new_state.apply_move(action[1])
        if action[0] == Action.SUGGESTION:
            new_state.apply_suggestion(action[1])
            rejected_card = self.random_reject(new_state, player_index)
            if rejected_card and rejected_card: # not in new_state._players[player_index]._cards:
                new_state._players[self._player_index].cards_rejected_for_me.add(rejected_card)
            else:
                if new_state._active_suggestion[0] not in new_state._players[self._player_index]._cards:
                    new_state._players[self._player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[0])
                if new_state._active_suggestion[1] not in new_state._players[self._player_index]._cards:
                    new_state._players[self._player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[1])
                if new_state._active_suggestion[2] not in new_state._players[self._player_index]._cards:
                    new_state._players[self._player_index].cards_no_one_could_reject_for_me.add(new_state._active_suggestion[2])

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
        return new_state

    def reject(self, state: GameState):
        all_rejections = state.get_possible_rejections(self.get_cards(), state._active_suggestion)
        for card in state._active_suggestion:
            if card in self.cards_i_showed:
                return card
        if not all_rejections:
            return None
        return random.choice(all_rejections)

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


def train_agent(agent: QLearningPlayer, num_games: int, game_manager):
    """
    Train the Q-Learning agent by playing multiple games.
    
    :param agent: The QLearningPlayer instance to train
    :param num_games: Number of games to play for training
    :param game_setup_func: A function that sets up and returns a new game state
    """
    def reset_game(game_manager):
        game_manager = CluedoGameManager(suspects=game_manager.suspects, weapons=game_manager.weapons, rooms=game_manager.rooms,
                                          players=game_manager.players, game_board=game_manager.game_board, test_mode=game_manager.test_mode)
        return game_manager.create_current_state()

    for game in range(num_games):
        state = reset_game(game_manager)
        total_reward = 0
        
        while not state.is_terminal:
            if state._player_index == agent._player_index:
                action_type, action_value = agent.play_turn(state)
                state = agent.apply_action(state, (action_type, action_value))
                reward = state.get_score()
                total_reward += reward
            else:
                # Simulate other players' turns
                # This is a simplified version; you might want to implement more sophisticated opponent behavior
                possible_actions = state.get_all_possible_actions(state._player_index, random.randint(1, 6))
                action = random.choice(possible_actions)
                state = agent.apply_action(state, action)
        
        print(f"Game {game + 1}/{num_games} completed. Total reward: {total_reward}")
        
        # Optionally, you can adjust the learning parameters after each game
        # For example, decreasing epsilon over time:
        agent.epsilon = max(0.01, agent.epsilon * 0.99)
