"""Wumpus World의 에이전트를 구현한 모듈"""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, List

from wumpus.models.action import Action
from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.agent.knowledge_base import Knowledge_base

@dataclass
class Agent:
    """Wumpus World의 에이전트
    
    에이전트는 다음과 같은 상태를 유지합니다:
    - 현재 위치와 방향
    - 방문한 위치들의 집합
    - 안전하지 않은 위치들의 집합
    - Wumpus가 있을 수 있는 위치들의 집합
    - Pit이 있을 수 있는 위치들의 집합
    - 보유한 화살의 수
    - 획득한 금의 유무
    """
    
    # 현재 상태
    is_alive: bool = True
    location: Location = field(default_factory=lambda: Location(1, 1))
    direction: Direction = Direction.NORTH
    has_arrow: bool = True
    has_gold: bool = False
    kb: Knowledge_base = field(default_factory=Knowledge_base)
    
    # 지나온 길 저장하는 스택
    path_stack: List[Location] = field(default_factory=list)
    
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
            Action.CLIMB: self._climb
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

        # 금이 없을 때 현재 위치를 스택에 저장
        if not self.has_gold:
            self.path_stack.append(self.location)
        
            
        self.location = new_location
        # self.kb.grid[new_location.row][new_location.col].visited = True
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
    
    # 더이상 진행할 수 없다면 백트래킹
    def backtrack(self) -> Optional[str]:
        if len(self.path_stack) <= 1:
            return "더 이상 되돌아갈 위치가 없습니다."

        self.location = self.path_stack.pop()
        return f"{self.location}로 되돌아갔습니다."
    
    # path_stack을 따라 시작 지점으로 복귀
    def backtrack_to_start(self):
        """
        스택을 역추적하여 시작 위치(1,1)로 되돌아감.
        Direction은 신경쓰지 않고, agent의 위치만 순서대로 이동.
        """
        path_back = self.path_stack[::-1]  # 스택을 역순으로

        for loc in path_back:
            if loc == self.location:
                continue  # 현재 위치는 제외

            print(f"시작 위치로 돌아가는 중: {self.location} → {loc}")
            self.location = loc  # 위치 이동(direction 상관X)
    # path_stack을 따라 시작 지점으로 복귀하기 위한 Action을 반환
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
            print("DEBUG: path_stack이 비어있습니다. 더 이상 백트래킹할 경로가 없습니다.")
            return None

        # path_stack에서 가장 최근 방문했던 위치를 꺼냅니다. (이전 위치로 돌아감)
        target_location = self.path_stack[-1]
        print(f"DEBUG: {target_location}으로 돌아갑니다.")

        # 현재 위치에서 목표 위치(이전 위치)로 가기 위한 상대적인 이동량 계산
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
            None, # 일치하는 방향이 없을 경우 None 반환
        )

        if self.direction != target_direction:
            return Action.TURN_RIGHT  # 방향 맞추기
                
        else:
            self.path_stack.pop()
            return Action.FORWARD # 이동동
            
    # KB를 참조하여, 금을 찾기 위해 방문할 위치를 결정. 해당 위치로 이동하기 위한 Action 반환
    def get_exploration_action(self) -> Optional[Action]:

        
        """
        탐색 모드에서 금을 찾기 위해 에이전트가 취할 다음 액션을 결정.
        안전한 인접 셀로 이동하거나, 필요시 회전하는 등의 탐색 행동을 반환.

        Returns:
            Optional[Action]: 수행할 탐색 액션 (FORWARD, TURN_RIGHT) 또는
                             더 이상 탐색할 곳이 없는 경우 None.
        """

        adjacent_cells = self.kb.get_adjacent_cells(self.location)

        if not adjacent_cells: 
            # 이동 가능한 방향이 X backtrak 진행
            return None

        target = adjacent_cells[0]
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

        # 현재 방향과 타겟 방향 일치시킬 때까지 회전 (오른쪽 우선)
        if self.direction != target_direction:
            return Action.TURN_RIGHT  # 방향 맞추기

        # 이동 시도
        return Action.FORWARD
    
    def print_path_stack_status(self):
        """
        현재 path_stack의 상태를 디버깅 목적으로 출력.
        """
        if not self.path_stack:
            print("DEBUG: path_stack은 현재 비어 있습니다.")
        else:
            # path_stack의 내용을 (row, col) 형태로 보기 쉽게 출력
            stack_representation = ", ".join([
                f"({loc.row},{loc.col})" for loc in self.path_stack
            ])
            print(f"DEBUG: path_stack 현재 상태: [{stack_representation}] (길이: {len(self.path_stack)})")
