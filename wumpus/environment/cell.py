"""Agent가 탐험하는 그리드 하나하나를 구성하는 Cell"""

from dataclasses import dataclass


@dataclass
class Cell:
    has_pit: bool
    has_wumpus: bool
    has_gold: bool
    has_agent: bool
    has_wall: bool
