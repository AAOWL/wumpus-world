from dataclasses import dataclass, field
from typing import List

from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept


@dataclass
class Knowledge_Cell:
    """에이전트의 지식 베이스 각 칸의 상태 저장하는 데이터 클래스"""

    visited: bool = False
    possible_wumpus: int = 0
    possible_pit: int = 0
    safe: bool = False
    wall: bool = False


@dataclass
class Knowledge_base:
    """
    agent의 내부 모델(관측된 환경)을 2차원 배열로 저장합니다.
    """

    # 지도 정보
    size: int = 6
    grid: List[List[Knowledge_Cell]] = field(
        default_factory=list
    )  # 각 칸이 Knowledge_Cell로 구성됨

    def __post_init__(self):
        """지식 베이스 격자 초기화"""
        self.grid = [
            [Knowledge_Cell() for _ in range(self.size)] for _ in range(self.size)
        ]

    def update_with_percept(
        self, location: Location, percept: Percept, direction: Direction
    ) -> None:
        """현재 위치에서의 감각 정보를 바탕으로 지식 업데이트"""
        row, col = location.row, location.col

        # bump가 감지되면 agent 앞에 있는 칸을 벽으로 표시
        if percept.bump:
            dr, dc = direction.delta
            wall_row = row + dr
            wall_col = col + dc
            if 0 <= wall_row < self.size and 0 <= wall_col < self.size:
                self.grid[wall_row][wall_col].wall = True
            return  # bump가 발생하면 더 이상 주변 cell을 탐색하지 않고 돌아감

        # 현재 위치는 방문했음을 표시
        self.grid[row][col].visited = True
        self.grid[row][col].safe = True  # 현재 위치는 안전하다고 가정 (죽지 않았으므로)
        self.grid[row][col].possible_wumpus = 0  # 현재 위치엔 왐퍼스 없음
        self.grid[row][col].possible_pit = 0  # 현재 위치엔 구덩이 없음

        # 인접한 위치들 계산
        adjacent = location.get_adjacent()  # Location 클래스에 get_adjacent 메서드 추가

        # 유효한 위치 추출 (pit 또는 wumpus가 존재 할 수 있는 위치
        # 즉 visited되지 않은 위치 and wall이 아닌 위치 and 안전하지 않은 위치
        adjacent_locations = [
            loc
            for loc in adjacent
            if not self.grid[loc.row][loc.col].visited
            and not self.grid[loc.row][loc.col].wall
            and not self.grid[loc.row][loc.col].safe
        ]

        # Breeze, Stench 감지 시 인접 칸에 가능성 표시
        for adj_loc in adjacent_locations:
            adj_r, adj_c = adj_loc.row, adj_loc.col

            # 방문하지 않은 칸에 대해서만 추론
            if not self.grid[adj_r][adj_c].visited:
                # Breeze가 존재
                if percept.breeze:
                    self.grid[adj_r][adj_c].possible_pit += 1

                # Breeze가 없으면 인접 칸에 Pit이 없음
                if not percept.breeze:
                    self.grid[adj_r][adj_c].possible_pit = 0

                # Stench가 존재
                if percept.stench:
                    self.grid[adj_r][adj_c].possible_wumpus += 1

                # Stench가 없으면 인접 칸에 Wumpus가 없음
                if not percept.stench:
                    self.grid[adj_r][adj_c].possible_wumpus = 0

                if not percept.breeze and not percept.stench:
                    self.grid[adj_r][adj_c].possible_wumpus += 1
                    self.grid[adj_r][adj_c].possible_pit += 1
                    self.grid[adj_r][adj_c].safe = True

    def get_adjacent_cells(self, location: Location) -> List["Location"]:
        """
        방문 한 적 없는, 이동을 고려 해 봐야하는 인접셀 반환
        인접 셀 중, 벽X 방문x인 셀들을 위험도(possible_wumpus + possible_pit)기준 오름차순으로 정렬하여 반환.
        """
        adj_loc = location.get_adjacent()
        valid_loc = [
            adj
            for adj in adj_loc
            if not self.grid[adj.row][adj.col].wall
            and not self.grid[adj.row][adj.col].visited
        ]

        # 위험도 기준으로 정렬
        sorted_loc = sorted(
            valid_loc,
            key=lambda loc: self.grid[loc.row][loc.col].possible_wumpus
            + self.grid[loc.row][loc.col].possible_pit,
        )

        return sorted_loc
