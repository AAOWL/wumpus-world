"""Wumpus World의 게임 환경을 구현한 모듈"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random

from wumpus.models.action import Action
from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept
from wumpus.environment.cell import Cell


@dataclass
class Environment:
    """Wumpus World의 게임 환경
    
    4x4 격자로 이루어진 동굴을 표현합니다.
    - (1,1)은 시작 지점으로, 항상 안전합니다.
    - Wumpus와 Pit은 각각 최대 2개까지 존재할 수 있습니다.
    - Gold는 정확히 1개 존재합니다.
    """
    
    size: int = 4  # 격자의 크기 (4x4)
    max_wumpus: int = 2  # 최대 Wumpus 수
    max_pits: int = 2    # 최대 Pit 수
    
    # 게임 상태
    is_game_over: bool = False
    is_wumpus_killed: bool = False
    score: int = 0
    
    # 격자 정보 (Cell의 2차원 배열)
    grid: List[List[Cell]] = field(default_factory=list)
    
    def __post_init__(self):
        """환경 초기화: 격자 생성 및 객체 배치"""
        # 빈 격자 생성
        self.grid = [
            [Cell(False, False, False, False, False) 
             for _ in range(self.size)]
            for _ in range(self.size)
        ]
        
        # 시작 지점 (1,1)에 에이전트 배치
        self.grid[0][0].has_agent = True
        
        # 랜덤하게 Wumpus, Pit, Gold 배치
        self._place_objects()
    
    def _place_objects(self):
        """Wumpus, Pit, Gold를 랜덤하게 배치"""
        available_cells = [
            (r, c) for r in range(self.size) 
            for c in range(self.size)
            if (r, c) != (0, 0)  # 시작 지점 제외
        ]
        
        # Wumpus 배치
        wumpus_count = random.randint(1, self.max_wumpus)
        wumpus_cells = random.sample(available_cells, wumpus_count)
        for r, c in wumpus_cells:
            self.grid[r][c].has_wumpus = True
            available_cells.remove((r, c))
            
        # Pit 배치
        pit_count = random.randint(1, self.max_pits)
        pit_cells = random.sample(available_cells, pit_count)
        for r, c in pit_cells:
            self.grid[r][c].has_pit = True
            available_cells.remove((r, c))
            
        # Gold 배치 (남은 셀 중 하나 선택)
        gold_r, gold_c = random.choice(available_cells)
        self.grid[gold_r][gold_c].has_gold = True
    
    def get_percept(self, location: Location) -> Percept:
        """주어진 위치에서의 감각 정보를 반환
        
        Args:
            location: 현재 위치
            
        Returns:
            Percept: 해당 위치에서의 감각 정보
        """
        row, col = location.row - 1, location.col - 1  # 1-based to 0-based
        
        # 인접한 셀들의 위치 계산 (상하좌우)
        adjacent = [
            (row + dr, col + dc)
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]
            if 0 <= row + dr < self.size and 0 <= col + dc < self.size
        ]
        
        # 감각 정보 수집
        stench = any(self.grid[r][c].has_wumpus for r, c in adjacent)
        breeze = any(self.grid[r][c].has_pit for r, c in adjacent)
        glitter = self.grid[row][col].has_gold
        
        return Percept(
            stench=stench,
            breeze=breeze,
            glitter=glitter,
            scream=self.is_wumpus_killed
        )
    
    def perform_action(self, action: Action, agent_location: Location, 
                      agent_direction: Direction) -> Tuple[bool, Optional[str], int]:
        """에이전트의 행동을 처리
        
        Args:
            action: 수행할 행동
            agent_location: 현재 에이전트의 위치
            agent_direction: 현재 에이전트의 방향
            
        Returns:
            Tuple[bool, Optional[str], int]:
                - bool: 행동 성공 여부
                - str: 결과 메시지 (실패 시 실패 이유)
                - int: 점수 변화량
        """
        old_row = agent_location.row - 1
        old_col = agent_location.col - 1
        
        score_delta = -1  # 기본적으로 모든 행동은 -1점
        
        if action == Action.FORWARD:
            # 새로운 위치 계산
            new_location = agent_location.move(agent_direction)
            new_row, new_col = new_location.row - 1, new_location.col - 1
            
            # 이동 가능 여부 확인
            if not (0 <= new_row < self.size and 0 <= new_col < self.size):
                return False, "벽에 부딪혔습니다.", score_delta
                
            # 에이전트 이동
            self.grid[old_row][old_col].has_agent = False
            self.grid[new_row][new_col].has_agent = True
            
            # 위험 요소 체크
            if self.grid[new_row][new_col].has_wumpus:
                self.is_game_over = True
                score_delta -= 1000  # 사망 페널티
                return True, "Wumpus에게 잡혔습니다!", score_delta
                
            if self.grid[new_row][new_col].has_pit:
                self.is_game_over = True
                score_delta -= 1000  # 사망 페널티
                return True, "구덩이에 빠졌습니다!", score_delta
                
        elif action == Action.SHOOT_ARROW:
            # 화살 발사 방향의 모든 셀 확인
            current_row, current_col = old_row, old_col
            dr, dc = agent_direction.delta
            
            while 0 <= current_row + dr < self.size and 0 <= current_col + dc < self.size:
                current_row += dr
                current_col += dc
                if self.grid[current_row][current_col].has_wumpus:
                    self.grid[current_row][current_col].has_wumpus = False
                    self.is_wumpus_killed = True
                    score_delta -= 10  # 화살 사용 페널티
                    return True, "Wumpus를 죽였습니다!", score_delta
            
            score_delta -= 10  # 화살 사용 페널티
            return True, "화살이 빗나갔습니다.", score_delta
            
        elif action == Action.GRAB_GOLD:
            if self.grid[old_row][old_col].has_gold:
                self.grid[old_row][old_col].has_gold = False
                score_delta += 1000  # 금 획득 보상
                return True, "금을 획득했습니다!", score_delta
            return False, "이 위치에 금이 없습니다.", score_delta
            
        elif action == Action.CLIMB:
            if (old_row, old_col) == (0, 0):  # (1,1) 위치
                self.is_game_over = True
                return True, "탈출에 성공했습니다!", score_delta
            return False, "시작 지점에서만 탈출할 수 있습니다.", score_delta
            
        return True, None, score_delta  # TURN_LEFT, TURN_RIGHT는 항상 성공
    
    def is_valid_location(self, location: Location) -> bool:
        """주어진 위치가 유효한지 확인"""
        row, col = location.row - 1, location.col - 1
        return 0 <= row < self.size and 0 <= col < self.size
