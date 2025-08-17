from enum import Enum

class Action(Enum):
    MOVE = 1
    SUGGESTION = 2
    ACCUSATION = 3
    REJECT = 4
    ENDTURN = 5