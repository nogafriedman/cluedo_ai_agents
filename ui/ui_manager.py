import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
from game_elements.cluedo_game_manager import CluedoGameManager
from game_elements.board import Board
import pygame
from game_elements.human_player import HumanPlayer
import random
from game_elements.action import Action
from ui.popup_manager import PopupManager

ROOM_IMAGES = [
    "resources/Kitchen.png", "resources/Ballroom.png", "resources/Conservatory.png",
    "resources/Dining_room.png", "resources/Billiard_room.png", "resources/Library.png",
    "resources/Lounge.png", "resources/Hall.png", "resources/Study.png"
]
CELL_SIZE = 100

START_IMAGE_PATH = "resources/start.png"

class UIManager:
    def __init__(self, game_manager: CluedoGameManager, board: Board):
        self._game_manager = game_manager
        self._board = board
        self.board_size = board.get_size()
        self.room_locations = board.get_room_locations()
        self.room_names = board.get_room_names()
        self.start_location = board.get_start_location()
        self.rooms_dict = {self.room_locations[i]: (self.room_names[i], ROOM_IMAGES[i]) for i in range(len(self.room_locations))}
        self.num_of_players = len(self._game_manager.players)
        self.remaining_moves = 0
        self.buttons_drawn = False
        self.moved = False
        self.initialize_window()
        self.images_loader()
        self.game_ended = False
        self.popup_manager = PopupManager(self.root)

    def initialize_window(self):
        self.root = tk.Tk()
        self.root.title("Cluedo Game")
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=self.board_size * CELL_SIZE, height=self.board_size * CELL_SIZE)

    def images_loader(self):
        self.room_images = {name: ImageTk.PhotoImage(Image.open(image).resize((CELL_SIZE, CELL_SIZE))) for name, image in self.rooms_dict.values()}
        self.start_image = ImageTk.PhotoImage(Image.open(START_IMAGE_PATH).resize((CELL_SIZE, CELL_SIZE)))

    def draw_board(self):
        # self.root.attributes('-fullscreen', True)
        self.canvas.pack()
        for i in range(self.board_size):
            for j in range(self.board_size):
                x1, y1 = j * CELL_SIZE, i * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                # Check if the current cell is a room or the start point
                if (i, j) in self.rooms_dict:
                    label, image_path = self.rooms_dict[(i, j)]
                    # Draw the image for the room
                    self.canvas.create_image(x1, y1, anchor='nw', image=self.room_images[label])
                elif (i, j) == self.start_location:
                    # Draw the start cell with the start image
                    self.canvas.create_image(x1, y1, anchor='nw', image=self.start_image)
                else:
                    # Draw empty cells
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="blanched almond", outline="sandy brown")
        self.draw_players()
        if not self.buttons_drawn:
            self.buttons()
            self.buttons_drawn = True

    def draw_players(self):
        # Define initial offset positions for players within the same cell
        base_offsets = [(10, 10), (CELL_SIZE - 45, 10), (10, CELL_SIZE - 45), (CELL_SIZE - 45, CELL_SIZE - 45)]
        colors = ["blue", "red", "green", "yellow", "orange", "purple"]
        
        # Dictionary to track how many players are at the same location
        location_count = {}
        
        # First pass: count how many players are at each location
        for i in range(self.num_of_players):
            player_location = tuple(self._game_manager.players[i].get_location())
            if player_location not in location_count:
                location_count[player_location] = 0
            location_count[player_location] += 1
        
        # Second pass: draw players, adjusting offsets for players at the same location
        for i in range(self.num_of_players):
            player_location = tuple(self._game_manager.players[i].get_location())
            x, y = player_location[1] * CELL_SIZE, player_location[0] * CELL_SIZE
            
            # Use base offsets for normal positioning, and apply slight modifications if there are multiple players
            num_players_at_location = location_count[player_location]
            if num_players_at_location > 1:
                # If more than 1 player at the same location, adjust offsets slightly
                offset_x, offset_y = base_offsets[i % len(base_offsets)]
                offset_x += (i % num_players_at_location) * 5  # Slight horizontal offset based on player index
                offset_y += (i % num_players_at_location) * 5  # Slight vertical offset based on player index
            else:
                # If only one player, use the base offset
                offset_x, offset_y = base_offsets[i % len(base_offsets)]
            
            x1_val = x + offset_x
            y1_val = y + offset_y
            x2_val = x1_val + 35
            y2_val = y1_val + 35
            
            # Use modulo to cycle through colors if more than 6 players
            color = colors[i % len(colors)]
            
            # Draw the player oval and label it with "P1", "P2", etc.
            self.canvas.create_oval(x1_val, y1_val, x2_val, y2_val, fill=color, outline="black")
            self.canvas.create_text((x1_val + x2_val) / 2, (y1_val + y2_val) / 2, text=f"P{i + 1}", fill="white", font=("Arial", 10, "bold"))

    def show_board(self):
        # Fade out the music over 2000 milliseconds (2 seconds)
        pygame.mixer.music.fadeout(4000)
        # Hide the start window
        self.start_window.destroy()
        # Show the main game window
        self.root.deiconify()
        self.draw_board()
        self.root.after(3000, self.update_buttons_state)
        
    def play_music(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load("resources/dramatic_music.mp3")
        pygame.mixer.music.play(-1)  # Play music indefinitely

    def start_window(self):
        self.start_window = Toplevel(self.root)
        self.start_window.title("Welcome to Cluedo")
        # Load and display an image for the opening screen
        self.opening_image = Image.open("resources/CoverImage.png") 
        self.opening_image = self.opening_image.resize((422, 563), Image.LANCZOS) 
        self.opening_photo = ImageTk.PhotoImage(self.opening_image)

        # Add the image to the start window
        self.image_label = tk.Label(self.start_window, image=self.opening_photo)
        self.image_label.pack(pady=10)

        # Add a start button to the start window
        self.start_button = tk.Button(self.start_window, text="Start Game", command=self.show_board, font=("Arial", 14), bg="green", fg="black")
        self.start_button.pack(pady=20)

        # Play music when the start window is shown
        self.play_music()
    
    def roll_dice(self):
        self.dice_roll = random.randint(1, 6)
        label = f"You rolled a {self.dice_roll}!"
        self.popup_manager.show_popup(message=label)

        # Now let the player choose a direction to move
        self.direction_choice_popup()

        # Update the button states for the new current player
        self.update_buttons_state()

    def buttons(self):
        """Create and place the buttons on the UI."""
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, pady=20)

        # Roll a Dice button
        self.roll_dice_button = tk.Button(self.button_frame, text="Roll a Dice", font=("Arial", 12), bg="light coral", fg="black", state=tk.DISABLED, command=self.roll_dice)
        self.roll_dice_button.pack(side=tk.LEFT, padx=5)

        # Make Accusation button
        self.accusation_button = tk.Button(self.button_frame, text="Accusation", font=("Arial", 12), bg="light coral", fg="black", state=tk.DISABLED, command=self.make_accusation)
        self.accusation_button.pack(side=tk.LEFT, padx=5)

        # Make Suggestion button
        self.suggestion_button = tk.Button(self.button_frame, text="Suggestion", font=("Arial", 12), bg="light coral", fg="black", state=tk.DISABLED, command=self.make_suggestion)
        self.suggestion_button.pack(side=tk.LEFT, padx=5)
        
        # Make EndTurn button
        self.end_turn_button = tk.Button(self.button_frame, text="End Turn", font=("Arial", 12), bg="light coral", fg="black", state=tk.DISABLED, command=self.end_turn)
        self.end_turn_button.pack(side=tk.LEFT, padx=5)

        # Show My Cards button
        self.show_cards_button = tk.Button(self.button_frame, text="My Cards", font=("Arial", 12), bg="lightgray", fg="black", command=self.show_cards)
        self.show_cards_button.pack(side=tk.LEFT, padx=5)

        # Show What I Know button
        self.show_info_button = tk.Button(self.button_frame, text="Clues", font=("Arial", 12), bg="lightgray", fg="black", command=self.show_info)
        self.show_info_button.pack(side=tk.LEFT, padx=5)

    def is_player_in_room(self, player_pos):
        return player_pos in self.room_locations

    def update_buttons_state(self):
        # if current player is not human - all buttons are off, and we go to game_manager.play_turn()
        
        if not self.game_ended:

            if isinstance(self._game_manager.players[self._game_manager.current_player], HumanPlayer):
                legal_actions = self._game_manager.create_current_state().get_legal_actions(self._game_manager.current_player)
                if Action.MOVE in legal_actions:
                    self.roll_dice_button.config(state="normal")
                else:
                    self.roll_dice_button.config(state="disabled")
                if Action.SUGGESTION in legal_actions:
                    self.suggestion_button.config(state="normal")
                else:
                    self.suggestion_button.config(state="disabled")
                    
                self.end_turn_button.config(state="normal")
                self.accusation_button.config(state="normal")

            else:
                self.suggestion_button.config(state="disabled")
                self.accusation_button.config(state="disabled")
                self.roll_dice_button.config(state="disabled")
                self.end_turn_button.config(state="disabled")
                
                cpu_index = self._game_manager.current_player

                action, details = self._game_manager.play_turn()
                self.display_computer_actions(action, details, cpu_index)
        
    def display_computer_actions(self, action, details, cpu_index):
        if action == Action.MOVE:
            self.show_board()
            self._game_manager.last_turn = Action.MOVE
            self.root.after(2000, self.switch_turn)
        elif action == Action.ACCUSATION:
            if self._game_manager.winner == cpu_index:
                self.game_ended = True
                self.popup_manager.show_popup(f"Player {cpu_index + 1} accused and Won!\nThe solution was: {details[0].get_name()}, {details[1].get_name()}, {details[2].get_name()}")
                self.root.after(3000, self.end_game)
            else:
                self.popup_manager.show_popup(f"Player {cpu_index + 1} accused: {details[0].get_name(), details[1].get_name(), details[2].get_name()} and failed")
                if self._game_manager.check_game_over(): 
                    self.game_ended = True
                    self.end_game()
        elif action == Action.SUGGESTION:
            self.popup_manager.show_popup(f"Player {self._game_manager.current_player + 1} suggested: {details[0].get_name()}, {details[1].get_name()}, {details[2].get_name()}")
            rejecting_player = self._game_manager.current_rejecting_player
            rejecting_card = self._game_manager.current_rejecting_card
            if rejecting_player != None:
                self.popup_manager.show_popup(f"Player {rejecting_player + 1} rejected with the card: {rejecting_card.get_name()}") 
            self.root.after(2000, self.switch_turn)
        
        elif action == Action.ENDTURN:
            self.switch_turn()

    def direction_choice_popup(self):
        """Popup for player to choose a direction to move using arrow keys."""
        direction_popup = tk.Toplevel(self.root)
        # direction_popup.attributes('-fullscreen', False)
        direction_popup.title("Choose Direction")
        tk.Label(direction_popup, text=f"Use arrow keys to move {self.dice_roll} steps:").pack(pady=10)

        # Set the number of moves remaining to the dice roll
        self.remaining_moves = self.dice_roll

        # Bind the arrow keys to the move_in_direction function
        direction_popup.bind("<Up>", lambda event: self.move_in_direction("Up", direction_popup))
        direction_popup.bind("<Down>", lambda event: self.move_in_direction("Down", direction_popup))
        direction_popup.bind("<Left>", lambda event: self.move_in_direction("Left", direction_popup))
        direction_popup.bind("<Right>", lambda event: self.move_in_direction("Right", direction_popup))

        # Set focus on the popup to ensure key presses are captured
        direction_popup.focus_set()

    def move_in_direction(self, direction, popup):
        """Move the player one step in the chosen direction."""
        # Check if there are remaining moves
        
        # while self.remaining_moves > 0:
        player_pos = self._game_manager.players[self._game_manager.current_player].get_location()

        # Move the player based on the chosen direction
        if direction == "Up" and player_pos[0] > 0:
            new_pos = (player_pos[0] - 1, player_pos[1])
            self._game_manager.players[self._game_manager.current_player].set_location(new_pos)
            self.remaining_moves -= 1
            self.canvas.delete("all")
            self.draw_board()

        elif direction == "Down" and player_pos[0] < self.board_size - 1:
            new_pos = (player_pos[0] + 1, player_pos[1])
            self._game_manager.players[self._game_manager.current_player].set_location(new_pos)
            self.remaining_moves -= 1
            self.canvas.delete("all")
            self.draw_board()

        elif direction == "Left" and player_pos[1] > 0:
            new_pos = (player_pos[0], player_pos[1] - 1)
            self._game_manager.players[self._game_manager.current_player].set_location(new_pos)
            self.remaining_moves -= 1
            self.canvas.delete("all")
            self.draw_board()

        elif direction == "Right" and player_pos[1] < self.board_size - 1:
            new_pos = (player_pos[0], player_pos[1] + 1)
            self._game_manager.players[self._game_manager.current_player].set_location(new_pos)
            self.remaining_moves -= 1
            self.canvas.delete("all")
            self.draw_board()

        # If no moves are remaining, close the popup and switch turns
        if self.remaining_moves == 0:
            popup.destroy()
            self._game_manager.last_turn = Action.MOVE
            self.switch_turn()
            

    def switch_turn(self):
        """Switch turns between players."""
        self.update_buttons_state()

    def make_accusation(self):
        """Allow player to make an accusation."""
        # Get the current room based on player position
        room = self.rooms_dict.get(tuple(self._game_manager.players[self._game_manager.current_player].get_location()), None)
        # Open the popup for accusation
        self.accusation_popup(room)

    def accusation_popup(self, room):
        """Popup to let the player make an accusation."""
        accusation_popup = tk.Toplevel(self.root)
        accusation_popup.title("Make Accusation")
        tk.Label(accusation_popup, text="Enter your accusation:").pack(pady=5)

        # Room Entry (pre-filled with the current room)
        tk.Label(accusation_popup, text="Room").pack()
        room_entry = tk.Entry(accusation_popup)
        room_entry.insert(0, room[0] if room else "")
        room_entry.pack()

        # Weapon Entry
        tk.Label(accusation_popup, text="Weapon").pack()
        weapon_entry = tk.Entry(accusation_popup)
        weapon_entry.pack()

        # Suspect Entry
        tk.Label(accusation_popup, text="Suspect").pack()
        suspect_entry = tk.Entry(accusation_popup)
        suspect_entry.pack()

        # Submit Button
        tk.Button(accusation_popup, text="Submit", command=lambda: self.check_accusation(room_entry.get(), weapon_entry.get(), suspect_entry.get(), accusation_popup)).pack(pady=10)

        # All game cards
        tk.Label(accusation_popup, text=self.get_all_game_cards_text()).pack()
        # suspect_entry.pack()

    def check_accusation(self, room, weapon, suspect, popup):
        """Check if the player's accusation is correct."""
        # Close the popup window after getting inputs
        popup.destroy()

        # Convert inputs to lowercase for case-insensitive comparison
        room = room.lower()
        weapon = weapon.lower()
        suspect = suspect.lower()
        
        # Player's accusation as a tuple
        suspect_card = None
        weapon_card = None
        room_card = None
        for card in self._game_manager.cards:
            if card.get_name().lower() == weapon and card.get_type() == 'weapon':
                weapon_card = card
            if card.get_name().lower() == suspect and card.get_type() == 'suspect':
                suspect_card = card
            if card.get_name().lower() == room and card.get_type() == 'room':
                room_card = card
        if not weapon_card:
            self.popup_manager.show_popup("Oh, that's not a valid weapon. Try again")
        elif not suspect_card:
            self.popup_manager.show_popup("Oh, that's not a valid suspect. Try again")
        elif not room_card:
            self.popup_manager.show_popup("Oh, that's not a valid room. Try again")
        if weapon_card and room_card and suspect_card:
            accusation = (suspect_card, weapon_card, room_card)
            self._game_manager.apply_accusation(accusation)

            if self._game_manager.check_solution(accusation):
                self.popup_manager.show_popup("Accusation is correct! You win!")
            else:
                self.popup_manager.show_popup("Accusation is incorrect. YOU LOSE")
                if self._game_manager.check_game_over(): ############################################
                    self.game_ended = True 
                    self.end_game() #################################################################
            
            if not self._game_manager.game_active:
                self.game_ended = True
                self.root.after(2000, self.end_game)
            else:
                self.switch_turn()

    def make_suggestion(self):
        """Allow the player to make a suggestion."""
        player_pos = self._game_manager.players[self._game_manager.current_player].get_location()
        room = self.rooms_dict.get(tuple(player_pos), None)
        self.suggestion_popup(room)

    def end_turn(self):
        self._game_manager.apply_end_turn()
        self.switch_turn()

    def suggestion_popup(self, room):
        """Popup to let the player make a suggestion."""
        suggestion_popup = tk.Toplevel(self.root)
        suggestion_popup.title("Make Suggestion")

        tk.Label(suggestion_popup, text="Enter your suggestion:").pack(pady=5)
        tk.Label(suggestion_popup, text=f"Room: {room[0]}").pack()

        # Room is automatically set to the room the player is in
        room_suggestion = room[0]

        # Weapon Entry
        tk.Label(suggestion_popup, text="Weapon").pack()
        weapon_entry = tk.Entry(suggestion_popup)
        weapon_entry.pack()

        # Suspect Entry
        tk.Label(suggestion_popup, text="Suspect").pack()
        suspect_entry = tk.Entry(suggestion_popup)
        suspect_entry.pack()
        
        # Submit Button
        tk.Button(suggestion_popup, text="Submit", command=lambda: self.process_suggestion(room_suggestion, weapon_entry.get(), suspect_entry.get(), suggestion_popup)).pack(pady=10)

        # All game cards
        tk.Label(suggestion_popup, text=self.get_all_game_cards_text()).pack()
        # suspect_entry.pack()

    def process_suggestion(self, room, weapon, suspect, popup):
        """Process the suggestion and allow the other player to reject it if they have a matching card."""
        # Close the suggestion popup
        popup.destroy()

        # Convert inputs to lowercase for case-insensitive comparison
        room = room.lower()
        weapon = weapon.lower()
        suspect = suspect.lower()

        # Player's suggestion as a tuple
        suspect_card = None
        weapon_card = None
        room_card = None
        for card in self._game_manager.cards:
            if card.get_name().lower() == weapon and card.get_type() == 'weapon':
                weapon_card = card
            if card.get_name().lower() == suspect and card.get_type() == 'suspect':
                suspect_card = card
            if card.get_name().lower() == room and card.get_type() == 'room':
                room_card = card    
        if not weapon_card:
            self.popup_manager.show_popup("Oh, that's not a valid weapon. Try again")
        elif not suspect_card:
            self.popup_manager.show_popup("Oh, that's not a valid suspect. Try again")
        if weapon_card and suspect_card:
            player_suggestion = (suspect_card, weapon_card, room_card)
            player, card = self._game_manager.apply_suggestion(player_suggestion)
            if player != None:
                self.popup_manager.show_popup(f"Player {player + 1} rejected your suggestion. He has the card {card.get_name()} ({card.get_type()})")
            else:
                self.popup_manager.show_popup("No one could reject your suggestion!")
            self.switch_turn()
        
    def get_all_game_cards_text(self):
        text = "All game cards:\n"
        counter = 0
        for card in self._game_manager.cards:
            text += f"{card.get_name()} ({card.get_type()}) | "
            counter += 1
            if counter == 5:
                text += "\n"
                counter = 0
        return text

    def show_cards(self):
        """Show the current player's cards."""
        cards_popup = tk.Toplevel(self.root)
        cards_popup.title("My Cards")

        cards = self._game_manager.players[self._game_manager.current_player].get_cards()
        tk.Label(cards_popup, text=f"Player {self._game_manager.current_player + 1}'s Cards:").pack(pady=5)
        for card in cards:
            tk.Label(cards_popup, text=f"{card.get_name()} ({card.get_type()})").pack()

    def show_info(self):
        """Show the current player's known information."""
        info_popup = tk.Toplevel(self.root)
        info_popup.title("What I Know")
        info = self._game_manager.players[self._game_manager.current_player].cards_rejected_for_me
        tk.Label(info_popup, text=f"Cards rejected for Player {self._game_manager.current_player + 1}:").pack(pady=5)
        for fact in info:
            tk.Label(info_popup, text=f"{fact.get_name()} ({fact.get_type()})").pack()

    def end_game(self):
        self.popup_manager.show_popup(f"So Player {self._game_manager.winner + 1} won! Congratulation! Hope you all enjoyed")
        self.root.after(3000, self.root.destroy)
        return self._game_manager.winner

    def run(self):
        self.start_window()
        # Initialize the board and buttons
        # Start the Tkinter event loop
        self.root.mainloop()
        return self._game_manager.winner