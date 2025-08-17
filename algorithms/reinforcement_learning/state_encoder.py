from game_elements.game_state import GameState
from game_elements.action import Action
class StateEncoder:
    def __init__(self, game_manager):
        self.board_size = game_manager.game_board.get_size()
        self.cards = list(game_manager.cards)
        self.card_combinations = len(game_manager.suspects) * len(game_manager.weapons) * len(game_manager.rooms)
        self.game_manager = game_manager
        self.encode_actions()
    
    def encode_actions(self):
        self.actions_encoding = dict()
        combinations = [(suspect, weapon, room) for suspect in self.game_manager.suspects for weapon in self.game_manager.weapons for room in self.game_manager.rooms]
        
        # End Turn
        self.actions_encoding[0] = [Action.ENDTURN, None]

        # Encode all possible suggestions
        i = 1
        for j in range(self.card_combinations):
            self.actions_encoding[i + j] = [Action.SUGGESTION, combinations[j]]
        i += j + 1

        # Encode all possible accusations
        for j in range(self.card_combinations):
            self.actions_encoding[i + j] = [Action.ACCUSATION, combinations[j]]
        i += j + 1


        # for j in range(len(self.cards)):
        #     self.actions_encoding[i + j] = [Action.REJECT, self.cards[j]]
        # self.actions_encoding[i + j + 1] = [Action.REJECT, []]
        # i += j + 1 + 1

        # Encode all possible moves
        for j in range(self.board_size):
            for k in range(self.board_size):
                self.actions_encoding[i + j + k] = [Action.MOVE, (j,k)]
            i += k
        i += j
        
    def encode(self, game_state: GameState):
        """
        Encodes the game state into a numerical representation for the ReinforcePlayer
        """
        all_cards = list(game_state._cards)
        board_size = game_state._game_board.get_size()

        # Encoding a location
        def encode_location(location, board_size):
            # Normalize location to the board size
            return [location[0] / board_size, location[1] / board_size]
        
        def encode_cards(cards, all_cards):
            # One-hot vector encodings of the cards
            card_vector = [0] * len(all_cards)
            # all_cards = list(all_cards)
            if cards:
                for card1 in cards:
                    # for card2 in all_cards:
                    #     if card1.get_name() == card2.get_name() and card1.get_type() == card2.get_type()
                    index = all_cards.index(card1)
                    card_vector[index] = 1
            return card_vector

        # Player's location encoding
        player = game_state._players[game_state._player_index]
        player_location_encoded = encode_location(player.get_location(), board_size)
        
        # Encode the cards the player has
        player_cards_encoded = encode_cards(player.get_cards(), all_cards)
        
        # Player's cards encodings
        player_showed_cards_encoded = encode_cards(player.cards_i_showed, all_cards)
        player_rejected_cards_encoded = encode_cards(player.cards_rejected_for_me, all_cards)
        player_asked_cards_encoded = encode_cards(player.cards_i_asked, all_cards)
        player_was_asked_cards_encoded = encode_cards(player.cards_i_was_asked, all_cards)
        player_no_reject_cards_encoded = encode_cards(player.cards_no_one_could_reject_for_me, all_cards)

        # Encode all suggestions and accusations so far

        all_suggested_cards = set()
        all_accused_cards = set()
        if game_state.all_suggestions:
            for s in game_state.all_suggestions:
                all_suggested_cards.add(s[2][0])
                all_suggested_cards.add(s[2][1])
                all_suggested_cards.add(s[2][2])
        if game_state.all_accusations:
            for s in game_state.all_accusations:
                all_accused_cards.add(s[0])
                all_accused_cards.add(s[1])
                all_accused_cards.add(s[2])
        
        all_suggestions_encoded = encode_cards(all_suggested_cards, all_cards)
        all_accusations_encoded = encode_cards(all_accused_cards, all_cards)
        
        opponent_locations = [0] * 10
        for i, player in enumerate(game_state._players):
            player_loc = encode_location(player.get_location(), board_size)
            opponent_locations[i] = player_loc[0]
            opponent_locations[i + 1] = player_loc[1]
            i += 1


        # Active suggestion encoding
        active_suggestion_encoded = encode_cards(game_state._active_suggestion, all_cards)
        
        # Accusation encoding
        active_accusation_encoded = encode_cards(game_state._active_accusation, all_cards)
        
        # Terminal state encoding
        is_terminal_encoded = [1 if game_state.is_terminal else 0]
        
        # Current player
        current_player_encoding = [game_state.get_current_player()]

        # Winner
        winner_encoding = [game_state.winner]
        if game_state.winner == None:
            winner_encoding = [-1]
        
        last_turn_encoded = [0]
        if game_state.last_turn == Action.MOVE:
            last_turn_encoded = [1]
        if game_state.last_turn == Action.SUGGESTION:
            last_turn_encoded = [2]
        if game_state.last_turn == Action.ACCUSATION:
            last_turn_encoded = [3]
        
        encoding = (tuple(map(str, player_location_encoded)) + 
            tuple(map(str, opponent_locations)) + 
            tuple(map(str, player_cards_encoded)) + 
            tuple(map(str, player_showed_cards_encoded)) + 
            tuple(map(str, player_rejected_cards_encoded)) + 
            tuple(map(str, player_asked_cards_encoded)) + 
            tuple(map(str, player_was_asked_cards_encoded)) + 
            tuple(map(str, player_no_reject_cards_encoded)) + 
            tuple(map(str, all_suggestions_encoded)) +
            tuple(map(str, all_accusations_encoded)) +
            tuple(map(str, active_suggestion_encoded)) + 
            tuple(map(str, active_accusation_encoded)) + 
            tuple(map(str, is_terminal_encoded)) +
            tuple(map(str, current_player_encoding)) + 
            tuple(map(str, winner_encoding)) + 
            tuple(map(str, last_turn_encoded)))
        
        return encoding
    
    def decode_action(self, action):
        return self.actions_encoding[action]