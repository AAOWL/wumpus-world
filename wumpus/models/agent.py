"""Wumpus World의 에이전트를 구현한 모듈"""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict
from wumpus.models.action import Action
from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept


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
    location: Location = field(default_factory=lambda: Location(1, 1))
    direction: Direction = Direction.EAST
    has_arrow: bool = True
    has_gold: bool = False
    
    # 지도 정보
    visited: Set[Location] = field(default_factory=set)
    unsafe: Set[Location] = field(default_factory=set)
    possible_wumpus: Set[Location] = field(default_factory=set)
    possible_pit: Set[Location] = field(default_factory=set)
    
    def __post_init__(self):
        """초기 상태 설정"""
        self.visited.add(self.location)  # 시작 위치 방문 처리
    
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
            
        # 안전하지 않은 위치 체크
        if new_location in self.unsafe:
            return "안전하지 않은 위치입니다."
            
        self.location = new_location
        self.visited.add(new_location)
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
    
    def update_knowledge(self, percept: Percept) -> None:
        """현재 위치에서의 감각 정보를 바탕으로 지식 업데이트
        
        Args:
            percept: 현재 위치에서의 감각 정보
        """
        current = self.location
        
        # 인접한 위치들 계산
        adjacent = [current.move(d) for d in Direction]
        valid_adjacent = [
            loc for loc in adjacent 
            if 1 <= loc.row <= 4 and 1 <= loc.col <= 4
        ]
        
        # Breeze가 감지되면 인접한 위치에 Pit이 있을 수 있음
        if percept.breeze:
            self.possible_pit.update(valid_adjacent)
            
        # Stench가 감지되면 인접한 위치에 Wumpus가 있을 수 있음
        if percept.stench:
            self.possible_wumpus.update(valid_adjacent)
            
        # 현재 위치는 안전함이 확인됨
        if current in self.unsafe:
            self.unsafe.remove(current)
        
        # 방문한 위치는 Wumpus나 Pit이 없음이 확인됨
        self.possible_wumpus.discard(current)
        self.possible_pit.discard(current) 