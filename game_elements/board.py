from game_elements.room import Room

BOARD_SIZE = 7
START_LOCATION = (3,3)
# Define the room locations, names, and corresponding image paths
ROOM_LOCATIONS = [
    (0, 0), (0, 3), (0, 6),
    (6, 2), (4, 6), (2, 6),
    (6, 4), (4, 0), (2, 0)
]
ROOM_NAMES = [
    "Kitchen", "Ballroom", "Conservatory",
    "Dining Room", "Billiard Room", "Library",
    "Lounge", "Hall", "Study"
]

class Board:
    def __init__(self):
        self._board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self._rooms = []

        for loc, name in zip(ROOM_LOCATIONS, ROOM_NAMES):
            row, col = loc
            room = Room(location=loc, name=name)
            self._board[row][col] = room
            self._rooms.append(room)
    
    def display_board(self):
        for row in self._board:
            print([room.get_name() if room else "| |" for room in row])

    def get_board(self):
        return self._board
    
    def get_start_location(self):
        return START_LOCATION
    
    def get_location(self, location):
        return self._board[location[0]][location[1]]
    
    def set_location(self, location, player):
        self._board[location[0]][location[1]] = player
    
    def get_room_locations(self):
        return ROOM_LOCATIONS

    def get_room_names(self):
        return ROOM_NAMES
    
    def get_size(self):
        return BOARD_SIZE
    
    @staticmethod
    def get_room_name(location):
        if location in ROOM_LOCATIONS:
            return ROOM_NAMES[ROOM_LOCATIONS.index(location)]
        return None

    @staticmethod
    def get_room_location(name):
        if name in ROOM_NAMES:
            return ROOM_LOCATIONS[ROOM_NAMES.index(name)]
        return None