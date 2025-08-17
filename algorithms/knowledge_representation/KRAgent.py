from game_elements.cluedo_player import CluedoPlayer
from game_elements.board import Board, ROOM_LOCATIONS
from game_elements.action import Action
from collections import defaultdict
import itertools
import copy
import random

SUSPECT = 0
WEAPON = 1
ROOM = 2

TYPE = 0
CARD = 1
SUGGESTION = 1
ACCUSATION = 1
PLAYER = 2


class KRAgent(CluedoPlayer):
    def __init__(self, index, name, suspect_cards, weapon_cards, room_cards): # todo - get the cards data somehow else
        super().__init__(index, name)
        self.board = Board
        self.cards = suspect_cards + weapon_cards + room_cards
        self.suspect_cards = suspect_cards
        self.weapon_cards = weapon_cards
        self.room_cards = room_cards
        self.players_idx = []

        self.unexplored_rooms = ROOM_LOCATIONS.copy()
        self.target_room_location = None
        self.past_suggestions = []

        self.all_possible_solutions = list(itertools.product(self.suspect_cards, self.weapon_cards, self.room_cards))

        # Maps cards to True or False (or None if unknown) to track which cards are in the solution and which can't be
        self.card_values = {
            'suspect': {suspect: None for suspect in suspect_cards},
            'weapon': {weapon: None for weapon in weapon_cards},
            'room': {room: None for room in room_cards}
        }
        # {'suspects': {Miss Scarlett: None, Colonel Mustard: None, ...}, 'weapons': {...}, 'rooms': {...}}

        # Maps players to a dictionary of cards and their status, True if held by the player, False if not, None if unknown
        self.players_hands = {player: {card: None for card in self.cards} for player in self.players_idx}
        # {player 1: {card 1: True, card 2: None, ...}, player 2: {card 1: False, card 2: True, ...}}

        # Maps players to a list of suggestions they disproved, as a list of cards in the suggestion
        self.possible_disproofs = {player: [] for player in self.players_idx}
        # {player 1: [[suspect, weapon, room], [suspect, weapon, room]], player 2: [[suspect, weapon, room]]}

        self.solution_found = False  # Tracks whether the AI is ready to make an accusation

        self.agenda = []  # Tracks facts that need to be inferred from
        self.inferred = defaultdict(lambda: False)  # Tracks facts that have been inferred from and processed
        # [('solution', card), ('held_by_player', card, player), ('not_held_by_player', card, player), ...]

    def init_knowledge(self, num_players):
        """
        Initializes the player's knowledge base at the start of the game.
        :param num_players: The number of players in the game.
        """
        self.players_idx = list(range(num_players))
        self.reset_knowledge()
        for card in self.cards:
            if card in self.get_cards():
                self.agenda.append(('held_by_player', card, self.get_index()))
            else:
                self.agenda.append(('not_held_by_player', card, self.get_index()))

    def reset_knowledge(self):
        """
        Resets and sets up the player's knowledge base at the start of a new game.
        """
        self.unexplored_rooms = ROOM_LOCATIONS.copy()
        self.target_room_location = None
        self.past_suggestions = []
        self.all_possible_solutions = list(itertools.product(self.suspect_cards, self.weapon_cards, self.room_cards))

        self.card_values = {
            'suspect': {suspect: None for suspect in self.suspect_cards},
            'weapon': {weapon: None for weapon in self.weapon_cards},
            'room': {room: None for room in self.room_cards}
        }
        self.players_hands = {player: {card: None for card in self.cards} for player in self.players_idx}
        self.possible_disproofs = {player: [] for player in self.players_idx}
        self.solution_found = False
        self.agenda = []
        self.inferred = defaultdict(lambda: False)

    def forward_chaining_inference(self):
        """
        Performs forward chaining inference to deduce new facts from the agenda and update the knowledge base.
        :return: The number of new facts derived from the inference, used to determine suggestion quality.
        """
        num_facts_derived = 0

        while self.agenda:
            fact = self.agenda.pop(0)  # Get the next fact to be inferred

            if self.inferred[fact]:
                continue  # Fact has already been processed

            self.inferred[fact] = True

            # Apply Rule: If a card is known to be in the solution, then it can't be in the hand of any player,
                                                              # and any solution that doesn't contain it is not valid
            if fact[TYPE] == 'solution':
                card = fact[CARD]
                for player in self.players_idx:
                    # Update the player's hand to show they don't have the card
                    self.players_hands[player][card] = False
                    num_facts_derived += 1
                    # Add the fact to the agenda
                    self.agenda.append(('not_held_by_player', card, player))

                for solution in self.all_possible_solutions[:]:
                    if card not in solution:
                        # Remove any solution that doesn't contain the card
                        self.all_possible_solutions.remove(solution)
                        num_facts_derived += 1

            # Apply Rule: If a card is known to be held by a player, then it can't be in the solution,
                                                            # and none of the other players can hold it
            elif fact[TYPE] == 'held_by_player':
                card, player = fact[CARD], fact[PLAYER]
                # Update the knowledge base to show the card is not in the solution
                self.card_values[card.get_type()][card] = False

                for solution in self.all_possible_solutions[:]:  # Iterate over a copy of the list
                    if card in solution:
                        self.all_possible_solutions.remove(solution)
                        num_facts_derived += 1

                for p in self.players_idx:
                    if p == player:
                        self.players_hands[p][card] = True
                    elif p != player:
                        # Update the other player's hand to show they don't have the card
                        self.players_hands[p][card] = False
                        num_facts_derived += 1
                        # Add the fact to the agenda
                        self.agenda.append(('not_held_by_player', card, p))

                # Check if now only one card in the category is unknown, and if so, it must be in the solution
                category = card.get_type()
                unknown = [card for card in self.card_values[category] if self.card_values[category][card] is None]
                if len(unknown) == 1:
                    # Update the knowledge base to show the last unknown card is in the solution
                    self.card_values[category][unknown[0]] = True
                    num_facts_derived += 1
                    # Add the fact to the agenda
                    self.agenda.append(('solution', unknown[0]))

            # Apply Rule: If a card is not held by a player, then they could not disprove a suggestion with that card
            elif fact[TYPE] == 'not_held_by_player':
                card, player = fact[CARD], fact[PLAYER]
                self.update_disproofs(card, player, 'remove')
                num_facts_derived += 1

            # Apply Rule: If a player could not disprove a suggestion, then they don't hold any of the cards in it
            elif fact[TYPE] == 'could_not_disprove':
                card, player = fact[CARD], fact[PLAYER]
                # Update the player's hand to show they don't have the card
                self.players_hands[player][card] = False
                num_facts_derived += 1
                # Add the fact to the agenda
                self.agenda.append(('not_held_by_player', card, player))

            # Apply Rule: If a player disproved a suggestion, then they must hold one of the cards in it,
                                                            # and the suggestion is not the solution
            elif fact[TYPE] == 'disproved':
                suggestion, player = fact[SUGGESTION], fact[PLAYER]
                # Update the player's disprove list with the suggestion to indicate they hold one of the cards
                self.update_disproofs(suggestion, player, 'add')
                num_facts_derived += 1
                # Remove the suggestion from the list of possible solutions
                if suggestion in self.all_possible_solutions:
                    self.all_possible_solutions.remove(suggestion)
                    num_facts_derived += 1

            # Apply Rule: If a suggestion made by the agent couldn't be disproved,
            # and the agent doesn't hold its cards, then they are the solution
            elif fact[TYPE] == 'not_disproved':
                suggestion = fact[SUGGESTION]
                for card in suggestion:
                    if self.players_hands[self.get_index()][card] is not True:
                        # Update the knowledge base to show the card is in the solution
                        self.card_values[card.get_type()][card] = True
                        # Add the fact to the agenda
                        self.agenda.append(('solution', card))
                num_facts_derived += float('inf')  # Solution is revealed, so the fact is infinitely important

            # Apply Rule: If an accusation is incorrect, then the trio is not the solution - one of the 3 is wrong
            elif fact[TYPE] == 'incorrect_accusation':
                accusation = fact[ACCUSATION]
                if accusation in self.all_possible_solutions:
                    # Remove the incorrect accusation from the list of possible solutions
                    self.all_possible_solutions.remove(accusation)
                    num_facts_derived += 1

                # If two of the three cards are known to be in the solution, the third is not
                cards = {'suspect': accusation[SUSPECT], 'weapon': accusation[WEAPON], 'room': accusation[ROOM]}

                for card_type, card in cards.items():
                    other_types = [t for t in cards if t != card_type]

                    if self.card_values[other_types[0]][cards[other_types[0]]] is True and \
                            self.card_values[other_types[1]][cards[other_types[1]]] is True:
                        # Update the knowledge base to show the current card is not in the solution
                        self.card_values[card_type][card] = False
                        num_facts_derived += 1
                        self.agenda.append((card, 'not_solution'))

            # Apply Rule: If a card is known to not be in the solution, then any solution containing it is not valid
            elif fact[TYPE] == 'not_solution':
                card = fact[CARD]
                for solution in self.all_possible_solutions[:]:
                    if card in solution:
                        self.all_possible_solutions.remove(solution)
                        num_facts_derived += 1

        return num_facts_derived

    def update_disproofs(self, information, player, action):
        """
        Makes an update to the possible disproofs list based on new information.
        If action='add', adds the suggestion to the list of possible disproofs for the player.
        If action='remove', removes a card from possible disproofs for the player.
        Either way, updates the knowledge base accordingly, and adds to the agenda.
        :param information: If action='add', the suggestion to add to the list of possible disproofs, a tuple of suspect, weapon, room.
                            If action='remove', the card to remove from possible disproofs.
        :param player: The player in question.
        :param action: Whether to add or remove the suggestion from the list of possible disproofs.
        """
        if action == 'add':
            # Convert the suggestion from a tuple to a list of cards to make it mutable:
            suggestion = [information[SUSPECT], information[WEAPON], information[ROOM]]
            for card in suggestion:
                if self.players_hands[player][card] is False:
                    # Already known that the player doesn't have the card, so it can't be the card that disproved the suggestion
                    suggestion.remove(card)
            if len(suggestion) == 1:
                # If only one card remains in the suggestion, it must be the card the player showed to disprove it
                self.agenda.append(('held_by_player', suggestion[0], player))
                return
            else:
                # Add the suggestion to the list of possible disproofs for the player
                self.possible_disproofs[player].append(suggestion)

        else:  # Removing a card from the possible disproofs
            card = information
            for disproof in self.possible_disproofs[player][:]:
                if card in disproof:
                    # Remove the suggestion from the list of possible disproofs for the player
                    disproof.remove(card)
                    if len(disproof) == 1:
                        # If only one card remains in the disproof, it must be the card the player showed
                        self.players_hands[player][disproof[0]] = True
                        self.agenda.append(('held_by_player', disproof[0], player))
                        self.possible_disproofs[player].remove(disproof)

    def find_minimal_distance(self, target, locations):
        """
        Finds the closest board location to a certain location.
        :param target: The target location to find the closest location to (x, y).
        :param locations: A list of locations to choose from [(x1, y1), (x2, y2), ...].
        :return: The closest location to the target (x, y).
        """
        min_distance = float('inf')
        closest_location = None

        for location in locations:
            # Calculate Euclidean distance between the target and the location

            distance = ((target[0] - location[0]) ** 2 + (target[1] - location[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_location = location
        return closest_location

    def roll_dice(self):
        """
        Simulates rolling a 6-sided dice.
        :return: A random integer between 1 and 6.
        """
        return random.randint(1, 6)

    def get_move(self, game_state, dice_roll):
        """
        Chooses the move to make based on the player's current position and the distance to each room.
        Prioritizes moving towards the closest unknown room (that the agent has no information about).
        :param game_state: The current state of the game.
        :param dice_roll: The number rolled on the dice.
        :return: The move to make (x, y).
        """
        # Choose a room randomly out of the unknown rooms:
        unknown_rooms = [room for room in self.room_cards if self.card_values['room'][room] is None]
        if unknown_rooms:
            target_room = random.choice(unknown_rooms)
            self.target_room_location = self.board.get_room_location(target_room.get_name())
        else:
            self.target_room_location = random.choice(ROOM_LOCATIONS)

        legal_moves = game_state.get_legal_move_locations(dice_roll, self._index)
        # If the target room is reachable in one move, move there
        if self.target_room_location in legal_moves:
            return self.target_room_location
        else:  # Move to the closest tile to the target room
            return self.find_minimal_distance(self.target_room_location, legal_moves)

    def play_turn(self, game_state):
        """
        Makes a move in the player's turn. Possible moves are:
        - Rolling the dice and moving on the board or into a room
        - Making a suggestion
        - Making an accusation
        :param game_state: The current state of the game.
        """
        if game_state.last_turn is None:  # Start of the turn
            # Check if agent knows the solution (ready to make an accusation)
            if len(self.all_possible_solutions) == 1:
                self.solution_found = True
                accusation = self.make_accusation()
                return Action.ACCUSATION, accusation

            # Perform forward chaining to see if new information can be inferred before making a move
            res = self.forward_chaining_inference()  # (return value is irrelevant here)

            # Move
            # Roll the dice and move on the board:
            dice_roll = self.roll_dice()
            location = self.get_move(game_state, dice_roll)  # Move towards the chosen room
            # If new location is not a room, end turn:
            if location not in ROOM_LOCATIONS:
                return Action.MOVE, location
            else:  # If new location is a room, prepare to make a suggestion:
                if location in self.unexplored_rooms:
                    self.unexplored_rooms.remove(location)
                return Action.MOVE, location

        if game_state.last_turn == Action.MOVE:
            # If reached a room after moving, make a suggestion:
            if self.get_room() is not None:
                # Now in a room, make a suggestion
                suggestion = self.make_suggestion()
                self.past_suggestions.append(suggestion)
                return Action.SUGGESTION, suggestion
            # If didn't reach a room after moving, make an accusation if ready or end turn:
            else:
                if len(self.all_possible_solutions) == 1:
                    accusation = self.make_accusation()
                    return Action.ACCUSATION, accusation
                else:
                    return Action.ENDTURN, None

        if game_state.last_turn == Action.SUGGESTION:
            # Perform forward chaining to see if new information can be inferred based on the suggestion's responses
            res = self.forward_chaining_inference()  # (return value is irrelevant here)

            # If only one possible solution set remains, the agent knows the solution - make an accusation
            if len(self.all_possible_solutions) == 1:
                self.solution_found = True
                accusation = self.make_accusation()
                return Action.ACCUSATION, accusation

        return Action.ENDTURN, None

    def reject(self, game_state):
        """
        Rejects a suggestion made by another player if possible.
        :param game_state: The current state of the game.
        :return: The card to show to disprove the suggestion, or None if the agent can't disprove it.
        """
        card = self.respond_to_suggestion(game_state)  # Pick a card to disprove the suggestion if any
        return card  # Card could be None

    def evaluate_suggestion(self, suggestion):
        """
        Evaluate how many new facts can be derived from the given suggestion using forward chaining.
        :param suggestion: Tuple of the suspect, weapon, and room of type Card.
        :return: An integer representing how many new facts can be derived from this suggestion.
        """
        # Make a deep copy of the entire agent
        agent_copy = copy.deepcopy(self)

        # Simulate possible player responses to the suggestion
        for player in agent_copy.players_idx:
            if player != agent_copy.get_index():
                for card in suggestion:
                    if agent_copy.players_hands[player][card] is not False:
                        # If the player could potentially have the card, simulate a disproof by the player with the card
                        agent_copy.simulate_suggestion_response(agent_copy, suggestion, player, card)

        # Run forward chaining on the agenda derived from the response simulation
        new_facts_derived = agent_copy.forward_chaining_inference()

        return new_facts_derived

    def find_best_suggestion(self):
        """
        Finds the best suggestion to make based on maximizing the number of new facts that can be derived using
        forward chaining. The suggestions considered are all possible combinations that haven't been eliminated yet
         from the possible solution sets, and contain the room the player is currently in.
        :return: A tuple containing a suspect, weapon, and a room.
        """
        suggestion_scores = {}
        current_room = self.get_room()

        # Filter out the possible solution sets that contain the current room
        valid_solutions = [possible_solution for possible_solution in self.all_possible_solutions
                           if possible_solution[ROOM].get_name() == current_room]

        # Iterate over the suggestions
        for possible_solution in valid_solutions:
            suspect = possible_solution[SUSPECT]
            weapon = possible_solution[WEAPON]
            room = possible_solution[ROOM]

            suggestion = (suspect, weapon, room)

            # Evaluate the suggestion based on how many new facts we can infer
            new_facts = self.evaluate_suggestion(suggestion)
            suggestion_scores[suggestion] = new_facts

        # Sort the suggestion_scores dictionary by the number of new facts in descending order
        # (list of tuples (suggestion, new_facts))
        sorted_suggestions = sorted(suggestion_scores.items(), key=lambda item: item[1], reverse=True)

        return sorted_suggestions

    def make_informative_suggestion(self):
        """
        Makes a suggestion based on the best possible combination of suspect, weapon, and room to maximize the number
        of new facts that can be derived from the suggestion.
        :return: A tuple containing a suspect, weapon, and a room.
        """
        # Choose strategically (based on the number of new facts that can be derived from the suggestion):
        suggestion_scores = self.find_best_suggestion()

        if not suggestion_scores:
            # Pick a random suggestion if no suggestions are available
            suggestion = self.make_random_suggestion()
        else:
            # Pick an informative suggestion that hasn't been made before
            i = 0
            for i in range(len(suggestion_scores)):
                if suggestion_scores[i][0] in self.past_suggestions:
                    continue
            suggestion = suggestion_scores[i][0]

        return suggestion

    def make_suggestion(self):
        """
        Makes a suggestion
        """
        return self.make_informative_suggestion()
        # return self.make_random_suggestion()

    def make_random_suggestion(self):
        """
        Makes a random suggestion based on the current room and the unknown cards.
        :return: A tuple containing a suspect, weapon, and a room.
        """
        current_room = self.get_room()
        current_room = [room for room in self.room_cards if room.get_name() == current_room][0]
        unknown_suspects = [card for card in self.suspect_cards if self.card_values['suspect'][card] is None]
        unknown_weapons = [card for card in self.weapon_cards if self.card_values['weapon'][card] is None]

        # Randomly suggest from the unknown sets, and if all are known, suggest randomly from all cards
        if not unknown_suspects:
            suspect = random.choice(self.suspect_cards)
        else:
            suspect = random.choice(unknown_suspects)
        if not unknown_weapons:
            weapon = random.choice(self.weapon_cards)
        else:
            weapon = random.choice(unknown_weapons)

        return (suspect, weapon, current_room)

    def respond_to_suggestion(self, game_state):
        """
        Responds to another player's suggestion. Chooses a card to disprove the suggestion if possible.
        If the agent has more than one matching card, it randomly chooses one to show.
        Alternatively, can be implemented with a heuristic to choose the best card to show.
        :param game_state: The current state of the game.
        :return: The card to show to disprove the suggestion, or None if the agent can't disprove it.
        """
        suggestion = game_state._active_suggestion
        matching_cards = []
        if suggestion[SUSPECT] in self.get_cards():
            matching_cards.append(suggestion[SUSPECT])
        if suggestion[WEAPON] in self.get_cards():
            matching_cards.append(suggestion[WEAPON])
        if suggestion[ROOM] in self.get_cards():
            matching_cards.append(suggestion[ROOM])

        # If agent has a matching card, randomly choose one to show
        if matching_cards:
            return random.choice(matching_cards)  # Randomly choose a card to show (if multiple)
        return None

    def simulate_suggestion_response(self, agent, suggestion, player, card):
        """
        Simulates the outcome of a suggestion the agent can make in order to choose the best suggestion.
        :param agent: A deep copy of the agent to simulate the suggestion response.
        :param suggestion: The suggestion made by the agent.
        :param player: The player responding to the suggestion.
        :param card: The card the player will show to disprove the suggestion.
        """
        agent.agenda.append(('held_by_player', card, player))

        # None of the players before the disproving player had any of the 3 cards suggested, use this information to infer
        for i in range(self.get_index() + 1, player):
            for card in suggestion:
                agent.agenda.append(('could_not_disprove', card.get_name(), player))

    def handle_suggestion_response(self, game_state):
        """
        Handles the responses of the other players to a suggestion.
        Adds the information gained to the agenda to be inferred later.
        :param game_state: The current state of the game.
        """
        # If suggestion was made by the agent:
        if game_state.current_suggesting_player == self.get_index():
            # If no one could disprove the suggestion, the agent knows the suggestion is not the solution:
            if game_state.current_rejecting_card is None:
                suspect = game_state._active_suggestion[0]
                weapon = game_state._active_suggestion[1]
                room = game_state._active_suggestion[2]
                self.agenda.append(('not_disproved', (suspect, weapon, room)))
                return

            # If the suggestion was disproved:
            else:
                self.agenda.append(('held_by_player', game_state.current_rejecting_card, game_state.current_rejecting_player))

        # If the suggestion was made by another player (the agent can't see the card shown)
        else:
            # If no one could disprove the suggestion, and it was not the agent's suggestion, can't infer anything:
            if game_state.current_rejecting_card is None:
                return

            # If another player disproved the suggestion:
            if game_state.current_rejecting_player != self.get_index():
                suspect = game_state._active_suggestion[0]
                weapon = game_state._active_suggestion[1]
                room = game_state._active_suggestion[2]
                self.agenda.append(('disproved', (suspect, weapon, room), game_state.current_rejecting_player))

        # None of the players before the disproving player had any of the 3 cards suggested, use this information to infer
        for i in range(game_state.current_suggesting_player + 1 ,game_state.current_rejecting_player):
            for card in game_state._active_suggestion:
                self.agenda.append(('could_not_disprove', card, i))

    def make_accusation(self):
        """
        Makes an accusation based on the known solution.
        :return: A tuple containing the suspect, weapon, and room of the accusation.
        """
        if len(self.all_possible_solutions) == 1:
            solution = self.all_possible_solutions[0]
            return solution

    def handle_accusation_response(self, accusation):  # todo: implement in manager
        """
        Handles the response to an accusation made by another player.
        If the accusation is correct, the game is over.
        If the accusation is incorrect, the agent can infer new information based on the wrong accusation.
        :param accusation: The accusation made by the player (dictionary of suspect, weapon, room).
        """
        self.agenda.append(('incorrect_accusation', accusation))

    ###### Extra Functions ######

    def print_knowledge_base(self):
        """
        Prints the player's knowledge of cards, categorizing them as:
        - "Not in solution" (cards with value False)
        - "In solution" (cards with value True)
        - "Unknown" (cards with value None)
        """
        in_solution = []
        not_in_solution = []
        unknown = []

        # Iterate through the player's card_values
        for category, cards in self.card_values.items():
            for card, value in cards.items():
                if value is True:
                    in_solution.append(card)
                elif value is False:
                    not_in_solution.append(card)
                else:
                    unknown.append(card)

        # Print categorized cards
        print("Player ", self.get_index() + 1, "'s knowledge base:")
        print(f"In solution:")
        for card in in_solution:
            print(f" - {card.get_name()}")

        print(f"\nnot in solution:")
        for card in not_in_solution:
            print(f" - {card.get_name()}")

        print(f"\nUnknowns:")
        for card in unknown:
            print(f" - {card.get_name()}")

        print()  # Extra line for clarity


    # Heuristic Functions

    # For choosing the best room to move to:

    def find_closest_room(self):
        """
        Finds the closest room to the player's current position with respect to the Euclidean metric.
        :return: The closest room's location (x,y) to the player's current position.
        """
        closest_room = None
        cur_position = self.get_location()

        min_distance = float('inf')
        optional_rooms = ROOM_LOCATIONS.copy()
        # Keep only the unknown rooms
        if self.unexplored_rooms:
            optional_rooms = [room for room in optional_rooms if room in self.unexplored_rooms]

        if cur_position in optional_rooms:
            # Look for the closest room excluding the current room
            optional_rooms.remove(cur_position)

        # Iterate over each room and its position to find the closest one
        for room_position in optional_rooms:
            # Calculate Euclidean distance between the current position and the room
            distance = ((cur_position[0] - room_position[0]) ** 2 + (cur_position[1] - room_position[1]) ** 2) ** 0.5

            # Update the closest room if a shorter distance is found
            if distance < min_distance:
                min_distance = distance
                closest_room = room_position

        return closest_room

    def find_strategic_room(self):
        """
        Finds the optimal room to move to based on the player's current position and the distance to each room.
        Prefer rooms that are:
        1. Close
        2. Unknown
        3. Not yet visited
        """
        best_room = None
        if self.unexplored_rooms:
            room_scores = {room: self.score_room_distance(room, self.get_location()) for room in self.unexplored_rooms}
            best_room = min(room_scores, key=room_scores.get)  # Choose the closest unexplored room
        else:
            all_rooms = ROOM_LOCATIONS  # Assuming ROOM_LOCATIONS has all room coordinates
            room_scores = {room: self.score_room_distance(room, self.get_location()) for room in all_rooms}

            unknown_rooms = [room for room in all_rooms if room not in self.unexplored_rooms]

            # Choose the closest room that is unknown (if any)
            if unknown_rooms:
                best_room = min([room for room in all_rooms if room in unknown_rooms], key=room_scores.get)
            else:
                best_room = min(room_scores, key=room_scores.get) # Choose the closest room overall

        return best_room

    def score_room_distance(self, room, cur_position):
        """
        Scores the distance between the player's current position and a target room with respect to the Euclidean metric.
        :param room: The target room's location (x, y).
        :param cur_position: The player's current position (x, y).
        :return: The distance between the player's current position and the target room.
        """
        return ((cur_position[0] - room[0]) ** 2 + (cur_position[1] - room[1]) ** 2) ** 0.5

    def choose_random_room(self):
        """
        Chooses a room to move to randomly.
        :return: The location of a room to move to (x, y).
        """
        return random.choice(ROOM_LOCATIONS)

    def get_strategic_move(self, game_state, dice_roll):
        """
        Chooses the best move based on the player's current position and the distance to each room.
        :param game_state: The current state of the game.
        :param dice_roll: The number rolled on the dice.
        :return: The best move to make based on the player's current position and the distance to each room.
        """
        # Choose a room strategically:
        # target_room_location = self.find_strategic_room()
        target_room_location = self.find_closest_room()
        legal_moves = game_state.get_legal_move_locations(dice_roll, self._index)
        # If the target room is reachable in one move, move there
        if target_room_location in legal_moves:
            return target_room_location
        else:  # Move to the closest tile to the target room
            return self.find_minimal_distance(target_room_location, legal_moves)

# Rules to add or include:
# todo: each player starts in the designated place on the board - not a must but could be interesting
# todo: change clockwise order of players each new game for fairness
# todo: deal with uneven dealt cards when there is an uneven number
# todo: don't allow moving on board on an occupied spot or into a room through a door blocked by a player
# todo: 2 six-sided dice instead of one
# todo: you dont have to use all of your movement from the dice
# todo: handle_accusation_response add to manager to trigger if someone made an accusation and it was wrong

# extra features probably won't be implemented:
# todo: add secret passages as one of the options in a turn
# todo: add the feature of a player moving into a room if another player named them in a suggestion
