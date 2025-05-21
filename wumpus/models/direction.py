"""
격자 맵 내에서의 4방향 열거형.

각 값은 (row_delta, col_delta) 튜플, 이동 시 좌표 변화량을 의미함.
ex) NORTH는 위로 한 칸 → (-1, 0)
"""

from enum import Enum


class Direction(Enum):
    """4방향 열거. 시계방향으로 북동남서"""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @property
    def delta(self) -> tuple[int, int]:
        """
        현재 방향에 따른 (row, col) 변화량을 튜플로 반환

        예:
           - NORTH → (-1, 0): 한 칸 위로 이동
           - EAST  → (0, 1): 한 칸 오른쪽으로 이동
           - SOUTH → (1, 0): 한 칸 아래로 이동
           - WEST  → (0, -1): 한 칸 왼쪽으로 이동
        """
        return {
            Direction.NORTH: (-1, 0),
            Direction.EAST: (0, 1),
            Direction.SOUTH: (1, 0),
            Direction.WEST: (0, -1),
        }[self]
