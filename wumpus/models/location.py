"""
불변 좌표 객체.

- row, col로 좌표를 표현하며, 이동(move) 연산 시 새로운 Location 인스턴스를 반환함.
- 위치를 변경할 때는 row/col 값을 직접 수정하지 말고, 반드시 move() 메서드를 사용할 것.
"""

from __future__ import annotations
from dataclasses import dataclass
from wumpus.models.direction import Direction
from wumpus.models.action import Action
from wumpus.models.percept import Percept


@dataclass(frozen=True)
class Location:
    """격자 상의 좌표 표현하는 불변 객체"""

    row: int
    col: int

    def move(self, direction: Direction) -> Location:
        """주어진 방향으로 한 칸 이동한 새 Location객체 반환"""
        dr, dc = direction.delta
        return Location(self.row + dr, self.col + dc)
