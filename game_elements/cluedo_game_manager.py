import random
from game_elements.cluedo_player import CluedoPlayer
from typing import List
from game_elements.card import Card
from game_elements.board import Board
from game_elements.action import Action
from game_elements.game_state import GameState

GAME_LOGO = '''
 .d8888b.     888                                 888              
d88P  Y88b    888                                 888              
888    888    888                                 888             
888           888    888  888     .d88b.      .d88888     .d88b.  
888           888    888  888    d8P  Y8b    d88" 888    d88""88b 
888    888    888    888  888    88888888    888  888    888  888 
Y88b  d88P    888    Y88b 888    Y8b.        Y88b 888    Y88..88P 
 "Y8888P"     888     "Y88888     "Y8888      "Y88888     "Y88P" 
 '''

class CluedoGameManager():
    def __init__(self, suspects: List[Card], weapons: List[Card], rooms: List[Card], players: List[CluedoPlayer], game_board: Board, test_mode: bool):
        # Game basic elements
        self.players = players # the game's players (CluedoPlayer)
        self.current_player = 0 # the current player that should now play his turn
        self.game_board = game_board
        self.game_active = True # game ended or not
        self.active_suggestion = None # is there an active suggestion (which the current player should respond to)
        self.active_accusation = None # is there an active accusation (which ends the game)
        self.winner = None
        self.test_mode = test_mode
        self.turns_count = [0] * len(players)

        # TODO: move to game_state
        self.current_suggesting_player = None
        self.current_rejecting_player = None
        self.current_rejecting_card = None
        self.last_turn = None
        self.all_suggestions = []
        self.all_accusations = []
        
        self.reset_players_knowledge()
        self._set_game_cards(suspects, weapons, rooms)
        self._set_player_locations()
        self._draw_solution()
        self._deal_cards()
        self.init_players_knowledge()  # todo ADDED 13.9

    def init_players_knowledge(self):  # todo ADDED 13.9
        for player in self.players:
            player.init_knowledge(len(self.players))

    def reset_players_knowledge(self):
        for player in self.players:
            player.reset_knowledge()

    def _set_player_locations(self):
        all_board_locations = []
        for i in range(self.game_board.get_size()):
            for j in range(self.game_board.get_size()):
                all_board_locations.append((i,j))
        # start_loc = self.game_board.get_start_location()
        for player in self.players:
            player.set_location(random.choice(all_board_locations))
            player.is_in_game = True

    def _set_game_cards(self, suspects, weapons, rooms):
        self.suspects = suspects
        self.weapons = weapons
        self.rooms = rooms
        self.cards = self.weapons + self.rooms + self.suspects

    def _draw_solution(self):
        # choose a random solution
        self.solution = {
            "suspect": random.choice(self.suspects),
            "weapon": random.choice(self.weapons),
            "room": random.choice(self.rooms)
        }

    def _deal_cards(self):
        for player in self.players:
            player._cards = set()
        
        players_num = len(self.players)
        remaining_cards = []
        for card in self.cards:
            if card != self.solution['suspect'] and card != self.solution['weapon'] and card != self.solution['room']:
                remaining_cards.append(card)
        
        random.shuffle(remaining_cards)
        cards_per_player = len(remaining_cards) // players_num
        
        for i, player in enumerate(self.players):
            start = i * cards_per_player
            end = start + cards_per_player
            player_cards = remaining_cards[start:end]
            player.add_cards(player_cards)
        
        # If there are any remaining cards, distribute them randomly
        remaining = len(remaining_cards) % len(self.players)
        if remaining > 0:
            for i in range(remaining):
                player = random.choice(self.players)
                card = remaining_cards[-(i+1)]
                player.add_cards([card])

        # Reset clues
        for player in self.players:    
            player.cards_i_asked = set()
            player.cards_i_showed = set()
            player.cards_i_was_asked = set()
            player.cards_rejected_for_me = set()
            player.cards_no_one_could_reject_for_me = set()

    def roll_dice(self):
        # if 1:
        return random.randint(1, 6)
        # if 2:
        # first_roll = random.randint(1, 6)
        # second_roll = random.randint(1, 6)
        # return first_roll + second_roll

    def play_accusation(self, details):
        if self.check_solution(details):
            self.winner = self.current_player
        else:
            self.print_message(f"Player {self.current_player + 1} lost")
            self.players[self.current_player].is_in_game = False
            for player in self.players:
                player.handle_accusation_response(details)

    def next_turn(self):
        self.last_turn = None
        self.current_player = self.get_next_active_player(self.current_player)

    def apply_end_turn(self):
        self.next_turn()

    def apply_accusation(self, accusation):
        self.active_accusation = accusation
        self.all_accusations.append(accusation)
        self.play_accusation(accusation)
        self.last_turn = Action.ACCUSATION
        self.check_game_over()
        self.next_turn()

    def apply_suggestion(self, suggestion):
        self.active_suggestion = suggestion
        self.current_rejecting_card = None
        self.current_rejecting_player = None
        
        self.players[self.current_player].cards_i_asked.add(suggestion[0])
        self.players[self.current_player].cards_i_asked.add(suggestion[1])
        self.players[self.current_player].cards_i_asked.add(suggestion[2])

        self.play_suggestion()
        self.last_turn = Action.SUGGESTION
        self.all_suggestions.append((self.current_player, self.current_rejecting_player, suggestion))

        return self.current_rejecting_player, self.current_rejecting_card


    def play_turn(self):
        action, details = self.players[self.current_player].play_turn(self.create_current_state())

        if action == Action.ACCUSATION:
            self.print_message(f"Player {self.current_player + 1} Accuses! {details[0].get_name()}, {details[1].get_name()}, {details[2].get_name()}")
            self.active_accusation = details
            self.all_accusations.append(details)
            self.play_accusation(details)
            self.last_turn = Action.ACCUSATION
            self.next_turn()

        if self.check_game_over():
            self.end_game()


        if action == Action.MOVE:
            self.print_message(f"Player {self.current_player + 1} Moved to {details}")
            self.players[self.current_player].set_location(details)
            self.players[self.current_player].set_room(Board.get_room_name(details))
            self.last_turn = Action.MOVE

        if action == Action.SUGGESTION:
            self.print_message(f"Player {self.current_player + 1} Suggests {details[0].get_name()}, {details[1].get_name()}, {details[2].get_name()}")
            self.active_suggestion = details
            self.current_suggesting_player = self.current_player
            self.current_rejecting_card = None
            self.current_rejecting_player = None
            
            self.players[self.current_player].cards_i_asked.add(details[0])
            self.players[self.current_player].cards_i_asked.add(details[1])
            self.players[self.current_player].cards_i_asked.add(details[2])

            self.play_suggestion()
            self.last_turn = Action.SUGGESTION
            self.all_suggestions.append((self.current_player, self.current_rejecting_player, details))

            if self.current_rejecting_player == None:
                if details[0] not in self.players[self.current_player]._cards:
                    self.players[self.current_player].cards_no_one_could_reject_for_me.add(details[0])
                if details[1] not in self.players[self.current_player]._cards:
                    self.players[self.current_player].cards_no_one_could_reject_for_me.add(details[1])
                if details[2] not in self.players[self.current_player]._cards:
                    self.players[self.current_player].cards_no_one_could_reject_for_me.add(details[2])

            # return self.current_rejecting_player, self.current_rejecting_card
        
        if action == Action.ENDTURN:
            self.print_message(f"Player {self.current_player + 1} ends his turn")
            self.next_turn()
        
        return action, details

    def play_suggestion(self):
        responding_player = self.get_next_player(self.current_player)
        current_state = self.create_current_state()
        while responding_player != self.current_player:
            rejection = self.players[responding_player].reject(current_state)
            if rejection:
                self.print_message(f"Player {responding_player + 1} Rejects, showing the card {rejection.get_name()}")
                self.current_rejecting_card = rejection
                self.current_rejecting_player = responding_player
                self.players[responding_player].cards_i_showed.add(rejection)
                self.players[self.current_player].cards_rejected_for_me.add(rejection)
                break
            else:
                responding_player = self.get_next_player(responding_player)
        if not rejection:
            self.print_message(f"No one could reject!")

        for player in self.players:
            player.handle_suggestion_response(self.create_current_state())

        
    def check_game_over(self):
        # Count number of active players
        active_players = 0
        active_player = None
        for i, player in enumerate(self.players):
            if player.is_in_game:
                active_players += 1
                active_player = i
        if active_players == 1:
            self.game_active = False
            self.winner = active_player
            return True
        if self.winner != None:
            self.game_active = False
            return True
        return False

    def get_next_active_player(self, index):
        while True:
            index += 1
            if index >= len(self.players):
                index = 0
            if self.players[index].is_in_game:
                return index

    def get_next_player(self, index):
        index += 1
        if index >= len(self.players):
            index = 0
        return index
    
    def end_game(self):
        if self.check_solution(self.active_accusation):
            self.print_message(f"{self.winner + 1} Won! very nice")
        else:        
            for i, player in enumerate(self.players):
                if player.is_in_game:
                    self.print_message(f"All other players are out of the game, Player {i + 1} Won!")
        
        self.print_message(f"The current solution: {self.solution['suspect'].get_name(), self.solution['weapon'].get_name(), self.solution['room'].get_name()}")
        self.game_active = False

    def check_solution(self, details):
        for card in details:
            if card.get_type() == "suspect":
                if card.get_name() != self.solution['suspect'].get_name():
                    return False

            if card.get_type() == "room":
                if card.get_name() != self.solution['room'].get_name():
                    return False
                
            
            if card.get_type() == "weapon":
                if card.get_name() != self.solution['weapon'].get_name():
                    return False
                
        return True
    
    def run_game(self):
        self.print_message(GAME_LOGO)
        while self.game_active:
            self.turns_count[self.current_player] += 1
            self.play_turn()
        return self.winner, self.turns_count

    def create_current_state(self) -> GameState:
        return GameState(game_cards=self.cards, accusation=self.active_accusation, game_board=self.game_board, players=self.players, 
                         is_terminal=self.check_game_over(), player_index=self.current_player, suggestion=self.active_suggestion,
                         current_rejecting_player = self.current_rejecting_player, current_rejecting_card = self.current_rejecting_card,
                         all_suggestions = self.all_suggestions, last_turn = self.last_turn, all_accusations = self.all_accusations,
                         current_suggesting_player=self.current_suggesting_player)
    
    def print_message(self, message):
        if not self.test_mode:
            print(" --- ")
            print(message)
            print(" --- \n")