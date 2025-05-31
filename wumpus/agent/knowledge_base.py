from dataclasses import dataclass, field
from typing import List

from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept


@dataclass
class Knowledge_Cell:
    """에이전트의 지식 베이스 각 칸의 상태 저장하는 데이터 클래스"""

    visited: bool = False  # agent가 직접 이동하여 안전함이 확인됨.
    possible_wumpus: int = 0
    possible_pit: int = 0
    safe: bool = (
        False  # agent가 percept를 했을 때 breeze와 stench가 나타나지 않았다면 인접셀에 표기(직접 가 보진 않았지만 안전함이 입증됨)
    )
    unsafe: bool = False  # agent가 이동 후 죽었던 위치 표기
    wall: bool = False

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현 반환"""
        # (우선순위, 문자열) 튜플을 저장할 임시 리스트
        # 0순위: Wall
        if self.wall:
            return "W"

        # 1순위: Unsafe
        if self.unsafe:
            return "US"

        # 2순위: Visited
        if self.visited:
            return "V"

        # 3순위: Safe
        if self.safe:
            return "S"

        contents = []
        # 4순위: Possible Wumpus + Possible Pit
        if self.possible_wumpus > 0 or self.possible_pit > 0:
            total_possibility = self.possible_wumpus + self.possible_pit
            contents.append(str(total_possibility))  # int를 str으로 명시적 변환

        return "[" + ",".join(contents) + "]" if contents else "[ ]"


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
        """
        현재 위치에서의 감각 정보를 바탕으로 지식 업데이트"
        인접 셀 중 유효 셀들 가져와서
            - Breeze/Stench 감지시 possible 가중치 증가
            - 둘 다 없으면 safe 마킹
        """
        row, col = location.row, location.col

        # 1) 현재 위치 마킹
        self._mark_current_as_visited_and_safe(location)

        # 2) 유효한 인접 셀 필터링 (pit 또는 wumpus가 존재 할 수 있는 위치
        valid_adjacent = self._get_valid_adjacent_cells(location)

        # 3) percept에 따른 인접 셀 업데이트
        self._apply_breeze_and_stench(valid_adjacent, percept)

    def get_adjacent_cells(self, location: Location) -> List["Location"]:
        """
        방문 한 적 없는, 이동을 고려 해 봐야하는 인접셀 반환
        인접 셀 중 벽X 방문x 위험x인 셀들을 위험도(possible_wumpus + possible_pit)기준 오름차순으로 정렬하여 반환.
        """
        adj_loc = location.get_adjacent()
        valid_loc = [
            adj
            for adj in adj_loc
            if not self.grid[adj.row][adj.col].wall
            and not self.grid[adj.row][adj.col].visited
            and not self.grid[adj.row][adj.col].unsafe
        ]

        # 위험도 기준으로 정렬
        sorted_loc = sorted(
            valid_loc,
            key=lambda loc: self.grid[loc.row][loc.col].possible_wumpus
            + self.grid[loc.row][loc.col].possible_pit,
        )

        return sorted_loc

    def _mark_current_as_visited_and_safe(self, location: Location) -> None:
        """
            현재 위치 방문 + 안전 + possible 0으로 초기화
        """

        row, col = location.row, location.col
        cell = self.grid[row][col]
        cell.visited = True
        cell.safe = True
        cell.possible_pit = 0
        cell.possible_wumpus = 0

    def _get_valid_adjacent_cells(self, location: Location) -> list[Location]:
        """
        location 기준 인접 셀 중에서
        - visited X
        - wall X
        - safe X
        인 모든 셀 필터링하여 반환
        """

        adjacent = location.get_adjacent() #인접 셀 리스트 반환

        valid = []
        for loc in adjacent:
            cell = self.grid[loc.row][loc.col]
            if not cell.visited and not cell.wall and not cell.safe:
                valid.append(loc)

        return valid

    def _apply_breeze_and_stench(self, adjacent_cells: list[Location], percept: Percept) -> None:
        """
        인접 셀 중 valid한 셀들에 대해서
        - breeze가 있으면 possible_pit += 1, 없으면 possible_pit = 0
        - stench가 있으면 possible_wumpus += 1, 없으면 possible_wumpus = 0
        """
        for loc in adjacent_cells:
            row, col = loc.row, loc.col
            cell = self.grid[row][col]

            # 이미 방문된 셀은 불필요 (visited 체크)
            if cell.visited:
                continue

            # 1) pit 가능성 업데이트
            if percept.breeze:
                cell.possible_pit += 1
            else:
                cell.possible_pit = 0

            # 2) wumpus 가능성 업데이트
            if percept.stench:
                cell.possible_wumpus += 1
            else:
                cell.possible_wumpus = 0

            # 3) 양쪽 모두 없으면(= 깨끗한 셀이면) 안전 마킹
            if not percept.breeze and not percept.stench:
                cell.safe = True

    def _print_knowledge_base(self) -> None:
        """현재 환경 상태를 격자 형태로 출력

        각 셀은 3x3 크기로 고정되며, 다음과 같은 형식으로 출력됩니다:
        +---+---+---+---+
        |[A]|[W]|[ ]|[G]|
        +---+---+---+---+
        |[ ]|[P]|[ ]|[ ]|
        +---+---+---+---+
        |[ ]|[ ]|[ ]|[ ]|
        +---+---+---+---+
        |[ ]|[ ]|[P]|[ ]|
        +---+---+---+---+
        """

        # 구분선 출력 함수
        def print_separator():
            print("+" + "---+" * self.size)

        # 격자 출력
        print_separator()
        for row in range(self.size):
            # 셀 내용 (각 셀은 3칸 고정 너비)
            print("|", end="")
            for col in range(self.size):
                cell_str = str(self.grid[row][col])
                print(f"{cell_str:^3}", end="|")  # :^3는 3칸 중앙 정렬
            print()
            print_separator()

    def mark_unsafe(self, location: Location) -> None:

        row, col = location.row, location.col
        self.grid[row][col].unsafe = True

        return

    def mark_wall(
        self, location: Location, percept: Percept, direction: Direction
    ) -> None:
        row, col = location.row, location.col

        # bump가 감지되면 agent 앞에 있는 칸을 벽으로 표시
        if percept.bump:
            dr, dc = direction.delta
            wall_row = row + dr
            wall_col = col + dc
            if 0 <= wall_row < self.size and 0 <= wall_col < self.size:
                self.grid[wall_row][wall_col].wall = True
            return  # bump가 발생하면 더 이상 주변 cell을 탐색하지 않고 돌아감
