import random
from game_elements.cluedo_game_manager import CluedoGameManager
from argparse import ArgumentParser
from game_elements.human_player import HumanPlayer
from algorithms.search.expectimax_player import ExpectimaxPlayer
from algorithms.search.random_player import RandomPlayer
from algorithms.search.minimax_player import MinimaxPlayer
from algorithms.knowledge_representation.KRAgent import KRAgent
from game_elements.board import Board
from game_elements.card import Card
from ui.ui_manager import UIManager
import time
# from algorithms.reinforcement_learning.trainer import ReinforceTrainer
# from algorithms.reinforcement_learning.state_encoder import StateEncoder
# from algorithms.reinforcement_learning.q_learning_agent import train_agent, QLearningPlayer
# from algorithms.reinforcement_learning.reinforce_player import ReinforcePlayer
# import pickle

# DEFAULTS
PLAYERS_NUM = 2
SUSPECTS_NUM = 6
WEAPONS_NUM = 6
ROUNDS_NUM = 1
SEED = 1
UI_ON = 'n'
TEST_MODE = 'n'
DEFAULT_PLAYERS = "random expectimax"
base_suspects = ["Miss Scarlet", "Professor Plum", "Mrs. Peacock", "Mr. Green", "Colonel Mustard", "Mrs. White"]
base_weapons = ["Knife", "Candlestick", "Revolver", "Rope", "Lead Pipe", "Wrench"]


def generate_new_suspect():
    first_names = [
        "Silly", "Goofy", "Wacky", "Loopy", "Zany", "Bizarre", 
        "Quirky", "Noodle", "Funky", "Whacky"
    ]
    last_names = [
        "McSqueezy", "Bananahead", "Wobblebottom", "Snickerdoodle", 
        "Fluffernutter", "Picklejuice", "Fuzzypants", "Jellybean", 
        "Muffinbutt", "Wigglesworth"
    ]
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return f"{first_name} {last_name}"

def generate_new_weapon():
    weapons_base = [
        "Banana", "Cucumber", "Soda", "Sock", "Water Balloon", "Jellybean", 
        "Rubber", "Marshmallow", "Confetti", "Bubble"
    ]
    weapons_type = [
        "Sword", "Cannon", "Bomb", "Grenades", 
        "Sprayer", "Blaster", "Hammer", "Launcher", "Gun"
    ]
    base = random.choice(weapons_base)
    type = random.choice(weapons_type)
    return f"{base} {type}"

def define_input_args():
    input_parser = ArgumentParser()
    input_parser.add_argument(
        '--players_num',
        type=int, 
        default=PLAYERS_NUM,
        help=f"The number of players who will participate in the Cluedo game. Default: {PLAYERS_NUM}, Min: 2, Max: 6"
    )
    input_parser.add_argument(
        '--suspects_num',
        type=int, 
        default=SUSPECTS_NUM,
        help=f"The number of possible suspects you will need to choose from. Default: {SUSPECTS_NUM}, Max: 10"
    )
    input_parser.add_argument(
        '--weapons_num',
        type=int, 
        default=WEAPONS_NUM,
        help=f"The number of possible weapons you will need to choose from. Default: {WEAPONS_NUM}, Max: 10"
    )
    input_parser.add_argument(
        '--ui',
        type=str, 
        default=UI_ON,
        help=f"Turn on ('y') or off ('n')  the UI. Default: y"
    )
    input_parser.add_argument(
        '--players',
        type=str,
        default=DEFAULT_PLAYERS,
        help="Choose which types of players will play the game: human (Manaul), random (AI), minimax (AI), expectimax (AI), kr (AI), rl (AI). Write a type for each player (using spaces). Default: human human"
    )
    input_parser.add_argument(
        '--rounds',
        type=int,
        default=ROUNDS_NUM,
        help=f"Choose how much rounds of the game you would like to play/be played. Default: {ROUNDS_NUM}"
    )
    input_parser.add_argument(
        '--test_mode',
        type=str,
        default=TEST_MODE,
        help="Run the test mode - no UI, only final results, no human player (y/n). Default: n"
    )
    input_parser.add_argument(
        '--seed',
        type=int,
        default=SEED,
        help="Seed for reproducibility. Default: 1"
    )
    return input_parser

def validate_input_args(args):
    errors = []

    # Validate players_num
    if not 2 <= args.players_num <= 6:
        errors.append(f"Number of players must be between {PLAYERS_NUM} and 6. Got: {args.players_num}")

    # Validate suspects_num
    if not 1 <= args.suspects_num <= 10:
        errors.append(f"Number of suspects must be between 1 and 10. Got: {args.suspects_num}")

    # Validate weapons_num
    if not 1 <= args.weapons_num <= 10:
        errors.append(f"Number of weapons must be between 1 and 10. Got: {args.weapons_num}")

    # Validate algorithm
    valid_algorithms = ['human', 'random', 'minimax', 'expectimax', 'kr']
    algorithms = args.players.split()
    if not all(algo in valid_algorithms for algo in algorithms):
        errors.append(f"Invalid algorithm(s). Must be one or more of {', '.join(valid_algorithms)}. Got: {args.players}")
    if len(algorithms) != args.players_num: 
        errors.append(f"Not enough/too much player types ({len(algorithms)}). Expected {args.players_num}")

    # Validate rounds
    if args.rounds < 1:
        errors.append(f"Number of rounds must be at least 1. Got: {args.rounds}")

    # Validate test_mode
    if args.test_mode.lower() not in ['y', 'n']:
        errors.append(f"Test mode must be 'y' or 'n'. Got: {args.test_mode}")
    

    # Validate ui
    if args.ui.lower() not in ['y', 'n']:
        errors.append(f"UI must be 'y' or 'n'. Got: {args.ui}")

    if 'human' in algorithms and args.ui.lower() == 'n':
        errors.append(f"Cannot play human without UI (Got ui: 'n')")
    
    if 'human' in algorithms and args.test_mode.lower() == 'y':
        errors.append(f"Cannot play human in test mode (Got test_mode: 'y')")

    if args.ui.lower() == 'y' and args.test_mode.lower() == 'y':
        errors.append(f"Cannot run test_mode in UI (Got test_mode and ui: 'y')")

    return errors

def set_up_game(args):
    # players_num = args.players_num
    suspects = random.sample(base_suspects, min(args.suspects_num, SUSPECTS_NUM))
    if args.suspects_num > SUSPECTS_NUM:
        while len(suspects) < args.suspects_num:
            new_suspect = generate_new_suspect()
            if new_suspect not in suspects:
                suspects.append(new_suspect)
    
    weapons = random.sample(base_weapons, min(args.weapons_num, WEAPONS_NUM))
    if args.weapons_num > WEAPONS_NUM:
        while len(weapons) < args.weapons_num:
            new_weapon = generate_new_weapon()
            if new_weapon not in weapons:
                weapons.append(new_weapon)

    game_board = Board()
    rooms = game_board.get_room_names()
    
    suspects_cards = []
    for s in suspects:
        suspects_cards.append(Card("suspect", s))
    weapons_cards = []
    for w in weapons:
        weapons_cards.append(Card("weapon", w))
    rooms_cards = []
    for r in rooms:
        rooms_cards.append(Card("room", r))

    players = []
    algorithms = args.players.split()
    for i, p in enumerate(algorithms):
        if p == "human":
            players.append(HumanPlayer(i, f"Human {i + 1}"))
        if p == "minimax":
            players.append(MinimaxPlayer(i, f"Minimax {i + 1}"))
        if p == "expectimax":
            players.append(ExpectimaxPlayer(i, f"Expectimax {i + 1}"))
        if p == "random":
            players.append(RandomPlayer(i, f"Random {i + 1}"))
        # if p == "rl":
        #     with open('algorithms/reinforcement_learning/rl_model.pkl', 'rb') as file:
        #         trainer = pickle.load(file)
        #     players.append(ReinforcePlayer(trainer._player, i, f"Reinforce {i + 1}"))
        if p == "kr":
            players.append(KRAgent(i, f"KR {i + 1}", suspects_cards, weapons_cards, rooms_cards))

    test_mode = True if args.test_mode == 'y' else False

    return CluedoGameManager(suspects=suspects_cards, weapons=weapons_cards, rooms=rooms_cards, players=players, game_board=game_board, test_mode=test_mode)
    
def run():
    input_parser = define_input_args()
    args = input_parser.parse_args()
    errors = validate_input_args(args)
    if len(errors) > 0:
        print(errors)
        return
    
    random.seed(args.seed)
    game_manager = set_up_game(args)

    #######################
    ####  RL TRAINING  ####
    #######################

    # Not in use in the final submission #

    # trainer = ReinforceTrainer(game_manager, lr = 0.001)
    # trainer.train(episodes = 1000)
    # with open('algorithms/reinforcement_learning/rl_model.pkl', 'wb') as file:
    #     pickle.dump(trainer, file)
    
    # if 'rl' in args.players.split():
    #     for p, player in enumerate(args.players.split()):
    #         if player == 'rl':
    #             game_manager.players[p].set_encoder(game_manager)
    

    turns_count = {}
    average_nodes_expanded = {}
    average_moves_played = {}

    for player in game_manager.players:
        if isinstance(player, ExpectimaxPlayer) or isinstance(player, MinimaxPlayer):
            average_nodes_expanded[player.name] = 0
        average_moves_played[player.name] = 0

    players_win_count = [0] * args.players_num
    for i in range(args.rounds):
        round_start_time = time.time()
        if args.ui == 'y':
            ui_manager = UIManager(game_manager, game_manager.game_board)
            winner = ui_manager.run()
        else:
            winner, turns = game_manager.run_game()
            round_end_time = time.time()

            for j, player in enumerate(game_manager.players):
                if isinstance(player, ExpectimaxPlayer) or isinstance(player, MinimaxPlayer):
                    average_nodes_expanded[player.name] += player.expanded
                average_moves_played[player.name] += turns[j]
        players_win_count[winner] += 1
        game_manager = CluedoGameManager(game_manager.suspects, game_manager.weapons, game_manager.rooms,
                                         game_manager.players, game_manager.game_board, game_manager.test_mode)
        if game_manager.test_mode:
            print(f"Finished game {i + 1}; Time elapsed: {round_end_time - round_start_time}")
    
    print()
    print("#---------##########---------#\n           RESULTS        \n#---------##########---------#\n\n")
    
    print("Total wins:")
    for i, player in enumerate(players_win_count):
        print(f"{game_manager.players[i].name}: {player} wins")
    print(" ----- ")

    if game_manager.test_mode:
        if average_nodes_expanded:
            for player in average_nodes_expanded:
                print(f"Average nodes expanded by {player}: {average_nodes_expanded[player] / args.rounds}")
            print(" ----- ")
        
        for player in average_moves_played:
            print(f"Average turns played by {player}: {average_moves_played[player] / args.rounds}")
        
        print(" ----- \n\n")

    print("#---------##########---------#\n(c) Cluedo the HUJI edition\n#---------##########---------#\n")
    
if __name__ == "__main__":
    run()