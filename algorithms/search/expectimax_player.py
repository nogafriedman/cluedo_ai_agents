from game_elements.cluedo_player import CluedoPlayer
from game_elements.game_state import GameState
from game_elements.action import Action
import copy
import random

MAX_DICE_ROLL = 6
DEPTH = 2
ACCUSATION_PROB = 5

class ExpectimaxPlayer(CluedoPlayer):
    def __init__(self, player_index, name):
        super().__init__(index=player_index, name=name)
        self._player_index = player_index
        self.expanded = 0
    
    def expectimax(self, state: GameState, depth):
        if depth == 0 or self.is_terminal(state):
            index = state._player_index
            state._player_index = self._player_index
            result = self.evaluate(state)
            state._player_index = index
            return result
        
        if self.is_agent_turn(state):
            possible_actions = self.get_possible_actions(state)
            unknown_cards = len(state._cards) - len(self._cards) - len(state._players[self._player_index].cards_rejected_for_me) - len(state._players[self._player_index].cards_no_one_could_reject_for_me)
            accustaion = True
            if unknown_cards > ACCUSATION_PROB: # len(state._cards) // ACCUSATION_PROB:
                accustaion = False
            possible_scores = []
            for action in possible_actions:
                if action[0] != Action.ACCUSATION or accustaion:
                    new_state = self.result(state, action)
                    possible_scores.append(self.expectimax(new_state, depth - 1))
            return max(possible_scores)
        else:
            return self.expectation_value(state, depth)
    
    def expectation_value(self, state, depth):
        actions = self.get_possible_actions(state)
        return sum(self.probability(state, action, actions) * self.expectimax(self.result(state, action), depth - 1)
                   for action in actions)
    
    def get_possible_actions(self, state: GameState):
        self.expanded += 1
        dice_roll = random.randint(1, 6)
        return state.get_all_possible_actions(self._player_index, dice_roll)
    
    def result(self, state: GameState, action):
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

    def probability(self, state, action, actions):
        return 1 / len(actions)
    
    def is_terminal(self, state: GameState):
        return state.is_terminal
    
    def is_agent_turn(self, state: GameState):
        return state.get_current_player() == self._player_index
    
    def evaluate(self, state: GameState):
        # Evaluate the desirability of a game state
        return state.get_score()
    
    def play_turn(self, state: GameState):
        # Choose the best action using expectimax
        best_action = None
        best_value = float('-inf')
        possible_actions = self.get_possible_actions(state)
        unknown_cards = len(state._cards) - len(self._cards) - len(self.cards_rejected_for_me) - len(self.cards_no_one_could_reject_for_me)
        accustaion = True
        if unknown_cards > ACCUSATION_PROB: # len(state._cards) // ACCUSATION_PROB:
            accustaion = False
        if len(self.cards_no_one_could_reject_for_me) >= 3:
            accustaion = True
        for action in possible_actions:
            if action[0] != Action.ACCUSATION or accustaion:
                value = self.expectimax(self.result(state, action), depth=DEPTH)
                if value > best_value:
                    best_value = value
                    best_action = action
        return best_action[0], best_action[1]
    
    def reject(self, state: GameState):
        all_rejections = state.get_possible_rejections(self.get_cards(), state._active_suggestion) 
        for card in state._active_suggestion:
            if card in self.cards_i_showed:
                return card
        if not all_rejections:
            return None
        return random.choice(all_rejections)