"""감각 정보를 표현하는 객체. 불변이며, 수정되지 않고 새로 갱신됨."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Percept:
    """
    인접칸 = 상하좌우(대각선X)
    - stench: 인접 칸에 Wumpus가 있어 냄새가 나는 경우
    - breeze: 인접 칸에 구덩이가 있어 바람이 부는 경우
    - glitter: 현재 칸에 금이 있는 경우
    - scream: Wumpus가 죽었을 때 들리는 비명
    """

    stench: bool = False
    breeze: bool = False
    glitter: bool = False
    scream: bool = False
