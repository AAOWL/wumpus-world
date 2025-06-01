"""Wumpus World의 에이전트를 구현한 모듈"""

from dataclasses import dataclass, field
from typing import Optional, List

from wumpus.models.action import Action
from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept
from wumpus.agent.knowledge_base import Knowledge_base


@dataclass
class Agent:
    """Wumpus World의 에이전트

    에이전트는 다음과 같은 상태를 유지합니다:
        - agent가 backtrack중인지 여부
        - agent의 생존 여부 (is_alive)
        - 현재 위치와 방향
        - 화살의 소유 여부
        - 획득한 금의 유무
        - Knowledge_base
        - 위치 히스토리 (path_stack)
    """

    # 현재 상태
    is_backtracking: bool = False
    is_alive: bool = True
    location: Location = field(default_factory=lambda: Location(1, 1))
    direction: Direction = Direction.NORTH

    has_arrow: bool = True
    has_gold: bool = False
    kb: Knowledge_base = field(default_factory=Knowledge_base)

    path_stack: List[Location] = field(default_factory=list)

    # ============================= KB 갱신 =============================
    def update_state_with_percept(self, percept: Percept) -> None:
        """
        현재 위치에서 받은 Percept를 바탕으로
            - Knowledge_base 업데이트
        """
        
        # bump 발생시 W 표시
        if percept.bump:
            self.kb.mark_wall(self.location, percept, self.direction)

        # kb에 percept 반영
        row, col = self.location.row, self.location.col

        cell = self.kb.grid[row][col]
        if not cell.visited:
            self.kb.update_with_percept(self.location, percept)

    # ============================= agent의 행동(Action) =============================
    def perform_action(self, action: Action) -> Optional[str]:
        """주어진 행동을 수행

        Args:
            action: 수행할 행동

        Returns:
            str: 행동 수행 결과 메시지 (실패 시 실패 이유)
            None: 행동 수행 성공
        """
        action_handlers = {
            Action.FORWARD: self._move_forward,
            Action.TURN_LEFT: self._turn_left,
            Action.TURN_RIGHT: self._turn_right,
            Action.SHOOT_ARROW: self._shoot_arrow,
            Action.GRAB_GOLD: self._grab_gold,
            Action.CLIMB: self._climb,
        }

        return action_handlers[action]()

    def _move_forward(self) -> Optional[str]:
        """현재 방향으로 한 칸 전진

        Returns:
            str: 이동 실패 시 실패 이유
            None: 이동 성공
        """
        new_location = self.location.move(self.direction)

        # 맵 범위(4x4) 체크
        if not (1 <= new_location.row <= 4 and 1 <= new_location.col <= 4):
            return "벽에 부딪혔습니다."

        # 둘 중 하나가 참일때는 path_stack 저장X
        if self.has_gold or self.is_backtracking:
            None
        else:
            self.path_stack.append(self.location)

        self.location = new_location

        return None

    def _turn_left(self) -> None:
        """왼쪽으로 90도 회전"""
        directions = list(Direction)
        current_idx = directions.index(self.direction)
        self.direction = directions[(current_idx - 1) % 4]

    def _turn_right(self) -> None:
        """오른쪽으로 90도 회전"""
        directions = list(Direction)
        current_idx = directions.index(self.direction)
        self.direction = directions[(current_idx + 1) % 4]

    def _shoot_arrow(self) -> Optional[str]:
        """현재 방향으로 화살 발사

        Returns:
            str: 발사 실패 시 실패 이유
            None: 발사 성공
        """
        if not self.has_arrow:
            return "화살이 없습니다."

        self.has_arrow = False
        return None

    def _grab_gold(self) -> Optional[str]:
        """현재 위치에서 금 획득 시도

        Returns:
            str: 획득 실패 시 실패 이유
            None: 획득 성공
        """
        if self.has_gold:
            return "이미 금을 보유하고 있습니다."

        self.has_gold = True
        return None

    def _climb(self) -> Optional[str]:
        """동굴 탈출 시도

        Returns:
            str: 탈출 실패 시 실패 이유
            None: 탈출 성공
        """
        if self.location != Location(1, 1):
            return "시작 지점(1,1)에서만 탈출할 수 있습니다."

        if not self.has_gold:
            return "금을 획득해야 탈출할 수 있습니다."

        return None

    # ============================= 다음 행동 결정 =============================

    def decide_next_action(self, percept:Percept) -> Optional[Action]:
        """
        update_state_with_percept 이후에 쓰여야함.
        흐름: update_state_with_percept -> decide_next_action -> perfrom_action

        현재 상태와 Percept를 바탕으로, 다음에 취할 Action을 결정.
          1) 금을 가지고 있다면 → 되돌아가기(백트래킹) 또는 CLIMB
          2) 현재 위치에 금이 반짝거리면 → GRAB_GOLD
          3) 백트래킹 모드인지 아닌지 판정하여 → get_backtrack_action()
          4) 그 외 탐색 모드 → get_exploration_action()
        """
        self.is_backtracking = False
        
        # 지각 정보 출력
        print("\n=== 지각 정보 ===")
        print(f"냄새 (Stench): {'있음' if percept.stench else '없음'}")
        print(f"미풍 (Breeze): {'있음' if percept.breeze else '없음'}")
        print(f"반짝임 (Glitter): {'있음' if percept.glitter else '없음'}")
        print(f"부딪힘 (Bump): {'있음' if percept.bump else '없음'}")
        print(f"비명 (Scream): {'있음' if percept.scream else '없음'}")
        
        # 1) 금을 이미 가지고 있다면
        if self.has_gold:
            # 시작 위치(1,1)까지 되돌아오면 CLIMB
            if self.location == Location(1, 1):
                print("\n=== 행동 결정 ===")
                print("금을 가지고 시작 지점에 도착했습니다. 탈출을 시도합니다.")
                return Action.CLIMB
            # 아니라면 백트래킹 행동 리턴
            print("\n=== 행동 결정 ===")
            print("금을 획득했습니다. 시작 지점으로 돌아갑니다.")
            return self.get_backtrack_action()

        # 2) 현재 칸에 GOLD(Glitter) 가 있으면 바로 줍기
        if percept.glitter:
            print("\n=== 행동 결정 ===")
            print("금이 반짝이는 것을 발견했습니다. 금을 줍습니다.")
            return Action.GRAB_GOLD

        # 3) 아직 탐색 중일 때: 안전한 인접 칸 선택
        exploration_action = self.get_exploration_action()
        if exploration_action is not None:
            print("\n=== 행동 결정 ===")
            if exploration_action == Action.FORWARD:
                print("안전한 전방으로 이동합니다.")
            elif exploration_action == Action.TURN_RIGHT:
                print("더 나은 경로를 찾기 위해 오른쪽으로 회전합니다.")
            return exploration_action

        # 4) 그 외 탐색 모드: 백트래킹
        print("\n=== 행동 결정 ===")
        print("더 이상 안전한 경로가 없습니다. 이전 위치로 돌아갑니다.")
        return self.get_backtrack_action()

    def get_backtrack_action(self) -> Optional[Action]:
        """
        path_stack에서 다음 위치를 꺼내 현재 에이전트의 위치와 방향을 기반으로
        백트래킹을 위한 다음 액션(TURN_RIGHT 또는 FORWARD)을 결정.

        Returns:
            Optional[Action]: 수행할 액션 (TURN_RIGHT, FORWARD) 또는
                             더 이상 돌아갈 경로가 없다면 None.
        """
        if not self.path_stack:
            # path_stack이 비어있으면 더 이상 돌아갈 경로가 없음
            print(
                "DEBUG: path_stack이 비어있습니다. 더 이상 백트래킹할 경로가 없습니다."
            )
            return None

        # path_stack에서 가장 최근 방문했던 위치를 꺼냅니다. (이전 위치로 돌아감)
        target_location = self.path_stack[-1]
        print(f"DEBUG: {target_location}으로 돌아갑니다.")

        # 현재 위치에서 목표 위치(이전 위치)로 가기 위한 방향을 계산
        # 예: 현재 (1,1), target (0,1) -> delta_row = -1, delta_col = 0 (NORTH)
        delta_row = target_location.row - self.location.row
        delta_col = target_location.col - self.location.col

        # 이 delta 값과 일치하는 방향(Direction)을 찾습니다.
        # 즉, 에이전트가 target_location을 향하기 위해 바라봐야 할 방향을 찾습니다.
        target_direction = next(
            (
                direction
                for direction in Direction
                if direction.delta == (delta_row, delta_col)
            ),
            None,  # 일치하는 방향이 없을 경우 None 반환
        )

        # stack에 잘못된 좌표가 들어온 경우
        if target_direction is None:
            print("target_direction이 None입니다.: get_backtrack_action")
            return None

        if self.direction != target_direction:
            return Action.TURN_RIGHT  # 방향 맞추기

        else:
            self.path_stack.pop()
            self.is_backtracking = True
            return Action.FORWARD  # 이동

    def get_exploration_action(self) -> Optional[Action]:
        """
        금을 찾기 위해 에이전트가 취할 다음 액션을 결정.
        가장 위험도가 낮은 인접 셀을 선택.
        이동하기 위해 회전/이동 행동을 반환.

        Returns:
            Optional[Action]: 수행할 탐색 액션 (FORWARD, TURN_RIGHT) 또는
                             더 이상 탐색할 곳이 없는 경우 None.
        """

        valid_adjacent = self.kb.get_adjacent_cells(self.location)

        if not valid_adjacent:
            # 이동 가능한 방향이 X backtrak 진행
            return None

        target = valid_adjacent[0]
        delta_row = target.row - self.location.row
        delta_col = target.col - self.location.col

        # Direction의 delta 속성을 역으로 검색
        target_direction = next(
            (
                direction
                for direction in Direction
                if direction.delta == (delta_row, delta_col)
            ),
            None,
        )

        if target_direction is None:
            print("target_direction이 None입니다.: get_exploration_action")
            return None
        
        # 현재 방향과 타겟 방향 일치시킬 때까지 회전 (오른쪽 우선)
        if self.direction != target_direction:
            return Action.TURN_RIGHT  # 방향 맞추기

        # 이동 시도
        return Action.FORWARD

    # ============================= Debug용 =============================
    def print_path_stack_status(self):
        """
        현재 path_stack의 상태를 디버깅 목적으로 출력.
        """
        if not self.path_stack:
            print("DEBUG: path_stack은 현재 비어 있습니다.")
        else:
            # path_stack의 내용을 (row, col) 형태로 보기 쉽게 출력
            stack_representation = ", ".join(
                [f"({loc.row},{loc.col})" for loc in self.path_stack]
            )
            print(
                f"DEBUG: path_stack 현재 상태: [{stack_representation}] (길이: {len(self.path_stack)})"
            )
