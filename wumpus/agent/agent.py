"""Wumpus World의 에이전트를 구현한 모듈"""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict

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
    location: Location = field(default_factory=lambda: Location(1, 1))
    direction: Direction = Direction.EAST
    has_arrow: bool = True
    has_gold: bool = False
    kb: Knowledge_base = Knowledge_base()

    def __post_init__(self):
        """초기 상태 설정"""
        # 삭제예정. percept -> reasoning -> action 중, reasoning(knowledge_base.py의 update_knowledge)에서 처리할 예정
        # self.kb.visited.add(self.location)  
        
    
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
        if not self.kb.grid[new_location.row][new_location.col].safe:
            return "안전하지 않은 위치입니다."
            
        self.location = new_location
        self.kb.grid[new_location.row][new_location.col].visited = True
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