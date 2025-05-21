"""agnet의 가능한 행동 열거형"""

from enum import Enum, auto


class Action(Enum):
    FORWARD = auto()
    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    SHOOT_ARROW = auto()
    GRAB_GOLD = auto()
    CLIMB = auto()
