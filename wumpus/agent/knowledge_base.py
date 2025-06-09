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

    no_pit_for_sure: bool = False
    no_wumpus_for_sure: bool = False
    
    safe: bool = False  # agent가 percept를 했을 때 breeze와 stench가 나타나지 않았다면 인접셀에 표기(직접 가 보진 않았지만 안전함이 입증됨)
    
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

    def update_with_percept(self, location: Location, direction: Direction, percept: Percept) -> None:
        """
        현재 위치에서의 감각 정보를 바탕으로 지식 업데이트
            - 현재 위치를 방문 및 safe 처리
            - 인접 셀 중 유효 셀들 필터링
            - Breeze/Stench 감지시 인접셀의 possible_pit/possible_wumpus 가중치 증가
            - 둘 다 없으면 인접한 모든 셀 safe 마킹
        """
        # Scream 발생시 바라보고 있는 방향의 wumpus를 삭제
        if percept.scream:
            self.delete_wumpus(location, direction,  percept)

        # bump 발생시 W 표시
        if percept.bump:
            self.mark_wall(location, direction,  percept)

        # possible_wunpus/pit 증가는 한번만
        if not self.grid[location.row][location.col].visited:
            # 1) 현재 위치 마킹
            self._mark_current_as_visited_and_safe(location)

            # 2) 유효한 인접 셀 필터링 (wumpus/pit이 존재 할 수 있는 위치)
            valid_adjacent = self._get_valid_adjacent_cells(location)

            # 3) percept에 따른 인접 셀 업데이트
            self._apply_breeze_and_stench(valid_adjacent, percept)

    def get_adjacent_cells(self, location: Location) -> List[Location]:
        """
        방문하지 않은 인접 셀들을 반환. 
        인접 셀 중 벽이 아니고 아직 방문하지 않은 모든 셀을 
        위험도(possible_wumpus + possible_pit) 기준으로 오름차순 정렬하여 반환.
        """
        adj_loc = location.get_adjacent()

        valid_loc = [
            adj
            for adj in adj_loc
            if not self.grid[adj.row][adj.col].wall         # 벽을 피함
            and not self.grid[adj.row][adj.col].visited     # 방문 한 적 있는 위치를 피함
            and not self.grid[adj.row][adj.col].unsafe      # 죽은 적 있는 위치를 피함.
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

    def _get_valid_adjacent_cells(self, location: Location) -> List[Location]:
        """
        location 기준 인접 셀 중에서
            - visited X
            - wall X
            - safe X
            인 모든 셀 필터링하여 반환
        """

        adjacent = location.get_adjacent()  # 인접 셀 리스트 반환

        valid = []
        for loc in adjacent:
            cell = self.grid[loc.row][loc.col]
            if not cell.visited and not cell.wall and not cell.safe:
                valid.append(loc)

        return valid

    def _apply_breeze_and_stench(
self, adjacent_cells: List[Location], percept: Percept
    ) -> None:
        """
            1) breeze가 없다면:
            → 인접한 모든 셀에 pit이 없다고 확정 (no_pit_for_sure = True)
            → 해당 셀은 이후 possible_pit이 증가하지 않음

            2) breeze가 있으면서 pit이 없다고 확정되지 않은 경우:
            → possible_pit += 1

            3) stench가 없다면:
            → 인접한 모든 셀에 wumpus가 없다고 확정 (no_wumpus_for_sure = True)
            → 이후 possible_wumpus 증가하지 않음

            4) stench가 있으면서 wumpus가 없다고 확정되지 않은 경우:
            → possible_wumpus += 1

            5) breeze와 stench 둘 다 없다면:
            → 완전히 안전한 셀로 간주 (safe = True)
            """
        for loc in adjacent_cells:
            row, col = loc.row, loc.col
            cell = self.grid[row][col]

            # 이미 방문된 셀은 불필요 (visited 체크)
            if cell.visited:
                continue

            # 1) pit 가능성 업데이트
            # breeze가 없으면 인접 칸에는 pit이 없다고 '확실히' 판단
            if not percept.breeze:
                cell.possible_pit = 0
                cell.no_pit_for_sure = True # Pit이 없다고 확정

            # 2) breeze가 있지만 pit이 없다고 확정되지 않았으면 가능성 증가
            elif not cell.no_pit_for_sure: 
                cell.possible_pit += 1


            # 3) wumpus 가능성 업데이트
            # stench가 없으면 인접 칸에는 wumpus가 없다고 '확실히' 판단
            if not percept.stench:
                cell.possible_wumpus = 0
                cell.no_wumpus_for_sure = True # Wumpus가 없다고 확정

             # 4) stench가 있지만 wumpus가 없다고 확정하지 않았다면 가능성 증가
            elif not cell.no_wumpus_for_sure:
                cell.possible_wumpus += 1

            # 5) 양쪽 모두 없으면 안전 마킹
            if not percept.breeze and not percept.stench:
                cell.safe = True
                cell.no_pit_for_sure = True
                cell.no_wumpus_for_sure = True

    def mark_unsafe(self, location: Location) -> None:
        """
        location 위치에서 죽었을 경우 호출.
        KB의 location위치에 unsafe = True처리
        """

        row, col = location.row, location.col
        self.grid[row][col].unsafe = True

        return

    def mark_wall(self, location: Location, direction: Direction, percept: Percept 
    ) -> None:
        """
        Percept에 bump가 존재하면 location의 direction방향 앞칸을 벽으로 표시
        """

        row, col = location.row, location.col

        # bump가 감지되면 agent 앞에 있는 칸을 벽으로 표시
        if percept.bump:
            dr, dc = direction.delta
            wall_row = row + dr
            wall_col = col + dc

            wall_cell = self.grid[wall_row][wall_col]
            if 0 <= wall_row < self.size and 0 <= wall_col < self.size:
                wall_cell.wall = True
                wall_cell.possible_pit = 0
                wall_cell.possible_wumpus = 0
                
            return  # bump가 발생하면 더 이상 주변 cell을 탐색하지 않고 돌아감

    def delete_wumpus(self, location: Location, direction: Direction, percept: Percept) -> None:
        """
        scream이 감지되면, 현재 방향을 따라 Wumpus가 있을 가능성이 있었던 unsafe 셀을 찾아
        그 셀을 safe로 마킹하고 possible_wumpus를 0으로 초기화함.
        """
        if percept.scream:
            current_row, current_col = location.row, location.col
            dr, dc = direction.delta

            while (
                0 <= current_row + dr < self.size and 0 <= current_col + dc < self.size
            ):
                current_row += dr
                current_col += dc
                if self.grid[current_row][current_col].unsafe and self.grid[current_row][current_col].possible_wumpus > 0:
                    self.grid[current_row][current_col].unsafe = False
                    self.grid[current_row][current_col].safe = True
                    self.grid[current_row][current_col].possible_wumpus = 0
                    return
                
        else:
            return
    
    def mark_no_wumpus_along_direction(self, location: Location, direction: Direction):
        """화살이 날아간 방향의 모든 칸에 possible_wumpus = 0 표시"""
        cur = location
        dr, dc = direction.delta
        while True:
            cur = Location(cur.row + dr, cur.col + dc)
            if cur.row > 5 or cur.row < 0 or cur.col > 5 or cur.col < 0: break
            cell = self.grid[cur.row][cur.col]
            cell.possible_wumpus = 0
    
    def _print_knowledge_base(self) -> None:
        """
        DEBUG용
        - 현재 KB의 grid 상태를 격자 형태로 출력
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
