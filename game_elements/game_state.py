from game_elements.board import Board
from game_elements.card import Card
from game_elements.action import Action

# max step size, with rolling one dice
MAX_STEPS = 6

class GameState():
    def __init__(self, game_cards, accusation, game_board: Board, 
                 players, player_index: int, current_suggesting_player, current_rejecting_player, current_rejecting_card,
                         all_suggestions, last_turn, all_accusations, is_terminal = False, suggestion = None):
        self._cards = game_cards # a list of Card
        self._game_board = game_board # Board
        self._active_accusation = accusation # a list of three Card (the accusation)
        self._players = players # a list of the game CluedoPlayers
        self._player_index = player_index # index of the player that is currently playing
        self._active_suggestion = suggestion # a list of three Card (the active suggestion)
        self._suggesting_player = None # index of the player that made the suggestion
        self._disproving_player = None # index of the player that disproved the suggestion
        self.is_terminal = is_terminal # boolean (is a terminal state)
        self.winner = None
        
        self.current_suggesting_player = current_suggesting_player
        self.current_rejecting_player = current_rejecting_player
        self.current_rejecting_card = current_rejecting_card
        self.last_turn = last_turn
        self.all_suggestions = all_suggestions
        self.all_accusations = all_accusations

    def get_current_player(self):
        return self._player_index

    # Returns a score for the current GameState (for the current_player)
    def get_score(self):
        my_cards = self._players[self._player_index].get_cards()
        num_of_cards_i_discovered = len(self._players[self._player_index].cards_rejected_for_me)
        num_of_not_rejected = len(self._players[self._player_index].cards_no_one_could_reject_for_me)
        num_of_cards_i_discovered += num_of_not_rejected
        cards_i_discovered = self._players[self._player_index].cards_rejected_for_me | self._players[self._player_index].cards_no_one_could_reject_for_me
        num_unknown_cards = len(self._cards) - len(my_cards) - num_of_cards_i_discovered
        unknown_cards = [card for card in self._cards if card not in my_cards and card not in cards_i_discovered]
        not_rejected_yet = self._players[self._player_index].cards_no_one_could_reject_for_me


        suspects_num = 0
        rooms_num = 0
        weapons_num = 0
        for card in self._cards:
            if card.get_type() == 'suspect':
                suspects_num += 1
            if card.get_type() == 'weapon':
                weapons_num += 1
            if card.get_type() == 'room':
                rooms_num += 1
        suspects_rejected = 0
        rooms_rejected = 0
        weapons_rejected = 0
        for card in self._players[self._player_index].cards_rejected_for_me:
            if card.get_type() == 'suspect':
                suspects_rejected += 1
            if card.get_type() == 'weapon':
                weapons_rejected += 1
            if card.get_type() == 'room':
                rooms_rejected += 1
        
        for card in self._players[self._player_index]._cards:
            if card.get_type() == 'suspect':
                suspects_rejected += 1
            if card.get_type() == 'weapon':
                weapons_rejected += 1
            if card.get_type() == 'room':
                rooms_rejected += 1
                
        unknown_suspects = suspects_num - suspects_rejected
        unknown_weapons = weapons_num - weapons_rejected
        unknown_rooms = rooms_num - rooms_rejected

        move_rank = 0
        accusation_rank = 0
        suggestion_rank = 0

        base_score = num_of_cards_i_discovered + len(my_cards)
        player_loc = self.get_player_location(self._player_index)

        if self.last_turn == Action.MOVE:    
            if player_loc in self._game_board.get_room_locations():
                move_rank += 10
                cur_room = Board.get_room_name(player_loc)
                if self._active_suggestion == None:
                    move_rank /= 100
                if cur_room:
                    move_rank += 1
                    if cur_room not in self._players[self._player_index].cards_rejected_for_me:
                        move_rank += 10
                    if cur_room in unknown_cards:
                        move_rank += 10
            
        
        if self.last_turn == Action.SUGGESTION:
            base_score *= 4
            if self._active_suggestion[0] in not_rejected_yet:
                suggestion_rank += 100
            if self._active_suggestion[1] in not_rejected_yet:
                suggestion_rank += 100
            if self._active_suggestion[2] in not_rejected_yet:
                suggestion_rank += 100
                if player_loc in self._game_board.get_room_locations():
                    suggestion_rank += 1000
            known_cards = self._players[self._player_index].get_cards() | self._players[self._player_index].cards_rejected_for_me
            if self._active_suggestion[0] in known_cards or self._active_suggestion[1] in known_cards or self._active_suggestion[2] in known_cards:
                suggestion_rank += 10
            if self._active_suggestion[0] in known_cards and self._active_suggestion[1] in known_cards:
                suggestion_rank += 100
            if self._active_suggestion[0] in known_cards and self._active_suggestion[2] in known_cards:
                suggestion_rank += 100
            if self._active_suggestion[1] in known_cards and self._active_suggestion[2] in known_cards:
                suggestion_rank += 100
            
            
        if self.last_turn == Action.ACCUSATION:
            if self._active_accusation[0] not in cards_i_discovered \
            and self._active_accusation[0] not in my_cards:
                accusation_rank += 10
            if self._active_accusation[0] not in self._players[self._player_index].cards_i_asked:
                accusation_rank /= 10

            if self._active_accusation[1] not in cards_i_discovered \
            and self._active_accusation[1] not in my_cards:
                accusation_rank += 10
            if self._active_accusation[1] not in self._players[self._player_index].cards_i_asked:
                accusation_rank /= 10

            if self._active_accusation[2] not in cards_i_discovered \
            and self._active_accusation[2] not in my_cards:
                accusation_rank += 10
            if self._active_accusation[2] not in self._players[self._player_index].cards_i_asked:
                accusation_rank /= 10

            if unknown_rooms > 3 or unknown_suspects > 3 or unknown_weapons > 3:
                accusation_rank /= 100
            if unknown_weapons < 2 or unknown_rooms < 2 or unknown_suspects < 2:
                accusation_rank += 10
            if unknown_weapons < 2 and unknown_rooms < 2 and unknown_suspects < 2:
                accusation_rank += 10000

            if num_unknown_cards < 4:
                accusation_rank += 10000
            if num_unknown_cards > 6:
                accusation_rank = 0
            if self._active_accusation not in self.all_accusations:
                accusation_rank += 10

            if num_of_not_rejected == 3:
                if self._active_accusation[0] in self._players[self._player_index].cards_no_one_could_reject_for_me and \
                self._active_accusation[1] in self._players[self._player_index].cards_no_one_could_reject_for_me and \
                self._active_accusation[2] in self._players[self._player_index].cards_no_one_could_reject_for_me:
                    accusation_rank += 10000000    
                
        return max(move_rank + accusation_rank + suggestion_rank, base_score)

    # Returns player_index location on the board
    def get_player_location(self, player_index):
        player_loc = None
        if player_index < len(self._players):
            player_loc = self._players[player_index].get_location()
        return player_loc

    # Returns a list of actions that player_index can take - MOVE, SUGGESTION OR ACCUSATION
    def get_legal_actions(self, player_index):
        legal_actions = [Action.ACCUSATION]
        if self.last_turn != None:
            legal_actions.append(Action.ENDTURN)

        if self.last_turn != Action.MOVE and self.last_turn != Action.SUGGESTION:
            legal_actions.append(Action.MOVE)
            
        player_loc = self.get_player_location(player_index)
        if player_loc in self._game_board.get_room_locations():
            room_name = Board.get_room_name(player_loc)
            flag = True
            for card in self._players[player_index].cards_rejected_for_me:
                if card.get_type() == 'room' and card.get_name() == room_name:
                    flag = False
            if flag and self.last_turn != Action.SUGGESTION:
                legal_actions.append(Action.SUGGESTION)

        return legal_actions

    # Returns a list of the possible locations which player_index can move to with the given step size (a dice roll)
    def get_legal_move_locations(self, step_size, player_index):
        legal_moves = []
        player_loc = self.get_player_location(player_index)

        # TODO: debug
        if not player_loc:
            print(f"player_index: {player_index}, player: {player}")
            return


        def is_within_bounds(loc, board_size):
            row, col = loc
            return 0 <= row < board_size and 0 <= col < board_size

        player_locations = []
        for player in self._players:
            player_locations.append(player.get_location())

        # row, col = player_loc
        board_size = self._game_board.get_size()

        def find_moves(loc, remaining_steps, path):
            row, col = loc
            if remaining_steps == 0:
                # Add to legal moves if within bounds
                if is_within_bounds((row, col), board_size) and (row,col) != player_loc:
                    if (row,col) not in player_locations:
                        legal_moves.append((row, col))
                return
        
        # Try all four directions if there are still steps remaining
            possible_moves = [
                (row + 1, col),    # Move down
                (row - 1, col),    # Move up
                (row, col + 1),    # Move right
                (row, col - 1)     # Move left
            ]

            for move in possible_moves:
                if is_within_bounds(move, board_size):
                    find_moves(move, remaining_steps - 1, path + [move])

        # Initialize recursion from player's current location
        find_moves(player_loc, step_size, [])

        return legal_moves

    # Returns a list of all possible suggestions that player_index can make with his cards
    def get_possible_suggestions(self, player_index):
        known_cards = self._players[player_index].cards_rejected_for_me | self._players[player_index].cards_no_one_could_reject_for_me
        # remaining_cards = [card for card in self._cards if card not in known_cards]
        suspects = [card for card in self._cards if card.get_type() == "suspect"]
        weapons = [card for card in self._cards if card.get_type() == "weapon"]
        room_name = Board.get_room_name(self._players[player_index].get_location())
        room = None
        for card in self._cards:
            if card.get_name() == room_name and card.get_type() == 'room':
                room = card
                break
        
        possible_suggestions = []
        cards_i_know = 0
        if room in self._players[player_index].get_cards() or room in known_cards:
            cards_i_know += 1
        cards_i_know_1 = cards_i_know
        for suspect in suspects:
            cards_i_know = cards_i_know_1
            i = 0
            if suspect in self._players[player_index].get_cards() or suspect in known_cards:
                i = 1
            cards_i_know += i
            cards_i_know_2 = cards_i_know
            for weapon in weapons:
                cards_i_know = cards_i_know_2
                j = 0
                if weapon in self._players[player_index].get_cards() or weapon in known_cards:
                    j = 1
                cards_i_know += j

                if cards_i_know != 3:
                    possible_suggestions.append((suspect, weapon, room))
                
                if cards_i_know > 3:
                    raise(Exception("AHH"))

        return possible_suggestions

    def get_possible_accusations(self, player_index):
        used_cards = self._players[player_index].cards_rejected_for_me
        player_cards = self._players[player_index].get_cards()
        remaining_cards = [card for card in self._cards if card not in used_cards and card not in player_cards]
        suspects = []
        weapons = []
        rooms = []
        for card in remaining_cards:
            if card.get_type() == "suspect":
                suspects.append(card)
            if card.get_type() == "room":
                rooms.append(card)
            if card.get_type() == "weapon":
                weapons.append(card)

        possible_accusations = [(suspect, weapon, room) for suspect in suspects for weapon in weapons for room in rooms if (suspect,weapon,room) not in self.all_accusations]

        return possible_accusations

    # Returns a list of the cards that the opponent suggested, and which player_index can reject
    def get_possible_rejections(self, cards, suggestion):
        possible_rejections = []
        for card in suggestion:
            name = card.get_name()
            type = card.get_type()
            for c in cards:
                c_name = c.get_name()
                c_type = c.get_type()
                if c_name == name and c_type == type:
                    possible_rejections.append(c)
        return possible_rejections

    # Returns a list of lists: all possible actions (type + description) which
    # player_index can perform
    def get_all_possible_actions(self, player_index, dice_roll):
        actions = []
        all_suggestions = None
        legal_moves = self.get_legal_actions(player_index)
        if Action.MOVE in legal_moves:
            all_locations = []
            new_locations = self.get_legal_move_locations(dice_roll, player_index=player_index)
            for loc in new_locations:
                if loc not in all_locations:
                    all_locations.append(loc)
            for loc in all_locations:
                actions.append([Action.MOVE, loc])
        if Action.SUGGESTION in legal_moves:
            all_suggestions = self.get_possible_suggestions(player_index)
            for s in all_suggestions:
                actions.append([Action.SUGGESTION, s])
        if Action.ACCUSATION in legal_moves:
            all_accusations = self.get_possible_accusations(player_index)
            for s in all_accusations:
                actions.append([Action.ACCUSATION, s])
        if Action.ENDTURN in legal_moves:
            actions.append([Action.ENDTURN, None])
        return actions
    


    ##### Apply actions to current state #####
    def apply_move(self, move):
        self._players[self._player_index].set_location(move)
        self.last_turn = Action.MOVE
    def apply_suggestion(self, suggestion):
            self._active_suggestion = suggestion
            self.current_rejecting_card = None
            self.current_rejecting_player = None
            self.all_suggestions.append((self._player_index, self.current_rejecting_player, suggestion))
            
            self._players[self._player_index].cards_i_asked.add(suggestion[0])
            self._players[self._player_index].cards_i_asked.add(suggestion[1])
            self._players[self._player_index].cards_i_asked.add(suggestion[2])
            for i, player in enumerate(self._players):
                if i != self._player_index:
                    player.cards_i_was_asked.add(suggestion[0])
                    player.cards_i_was_asked.add(suggestion[1])
                    player.cards_i_was_asked.add(suggestion[2])

            self.last_turn = Action.SUGGESTION
            
    def apply_accusation(self, accusation):
            self._active_accusation = accusation
            self.all_accusations.append(accusation)
            self.last_turn = Action.ACCUSATION
            
    def apply_end_turn(self):
        self.next_turn()
            
    def play_accusation(self, details):
        if self.check_solution(details): ##### TODO: check with minimax/expectimax
            self.winner = self._player_index
        else:
            self._players[self._player_index].is_in_game = False

    def next_turn(self):
        self.last_turn = None
        self._player_index = self.get_next_active_player(self._player_index)

    def get_next_active_player(self, index):
        for p in range(len(self._players)):
            cur_player = self.get_next_player(index)
            if self._players[cur_player].is_in_game:
                return cur_player
            index = cur_player
        return index

    def get_next_player(self, index):
        index += 1
        if index >= len(self._players):
            index = 0
        return index
