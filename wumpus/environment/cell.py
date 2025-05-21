"""Agent가 탐험하는 그리드 하나하나를 구성하는 Cell

각 Cell은 다음과 같은 상태를 가질 수 있습니다:
- Pit (구덩이)
- Wumpus (괴물)
- Gold (금)
- Agent (에이전트)
- Wall (벽)

각 상태는 boolean 값으로 표현되며, 다음과 같은 제약이 있습니다:
- Pit과 Wumpus는 같은 칸에 존재할 수 없음
- Gold는 Pit이나 Wumpus가 있는 곳에는 배치될 수 없음
- Agent는 시작할 때 (1,1)에 위치
- Wall은 현재 버전에서는 사용되지 않음 (확장성을 위해 유지)
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Cell:
    """격자의 한 칸을 표현하는 클래스
    
    Attributes:
        has_pit (bool): 구덩이 존재 여부
        has_wumpus (bool): Wumpus 존재 여부
        has_gold (bool): 금 존재 여부
        has_agent (bool): 에이전트 존재 여부
        has_wall (bool): 벽 존재 여부 (현재 버전에서는 미사용)
    """
    
    has_pit: bool = False
    has_wumpus: bool = False
    has_gold: bool = False
    has_agent: bool = False
    has_wall: bool = False
    
    def __post_init__(self):
        """객체 생성 후 제약조건 검증"""
        if self.has_pit and self.has_wumpus:
            raise ValueError("Pit과 Wumpus는 같은 칸에 존재할 수 없습니다.")
        if self.has_gold and (self.has_pit or self.has_wumpus):
            raise ValueError("Gold는 Pit이나 Wumpus가 있는 칸에 존재할 수 없습니다.")
    
    def place_pit(self) -> bool:
        """구덩이 배치 시도
        
        Returns:
            bool: 배치 성공 여부
        """
        if self.has_wumpus or self.has_gold:
            return False
        self.has_pit = True
        return True
    
    def place_wumpus(self) -> bool:
        """Wumpus 배치 시도
        
        Returns:
            bool: 배치 성공 여부
        """
        if self.has_pit or self.has_gold:
            return False
        self.has_wumpus = True
        return True
    
    def place_gold(self) -> bool:
        """금 배치 시도
        
        Returns:
            bool: 배치 성공 여부 (Pit이나 Wumpus가 있는 칸에는 배치 불가)
        """
        if self.has_pit or self.has_wumpus:
            return False
        self.has_gold = True
        return True
    
    def remove_wumpus(self) -> None:
        """Wumpus 제거 (화살에 맞았을 때)"""
        self.has_wumpus = False
    
    def remove_gold(self) -> None:
        """금 제거 (에이전트가 획득했을 때)"""
        self.has_gold = False
    
    def get_percepts(self) -> List[str]:
        """현재 칸에서 감지할 수 있는 모든 감각 정보 반환
        
        Returns:
            List[str]: 감지된 감각들의 목록
            - "STENCH": Wumpus가 인접한 칸에 있음
            - "BREEZE": Pit이 인접한 칸에 있음
            - "GLITTER": 현재 칸에 Gold가 있음
        """
        percepts = []
        if self.has_wumpus:
            percepts.append("STENCH")
        if self.has_pit:
            percepts.append("BREEZE")
        if self.has_gold:
            percepts.append("GLITTER")
        return percepts
    
    def is_safe(self) -> bool:
        """현재 칸이 안전한지 여부 반환
        
        Returns:
            bool: Pit이나 Wumpus가 없으면 True
        """
        return not (self.has_pit or self.has_wumpus)
    
    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현 반환"""
        contents = []
        if self.has_agent:
            contents.append("A")  # Agent
        if self.has_wumpus:
            contents.append("W")  # Wumpus
        if self.has_pit:
            contents.append("P")  # Pit
        if self.has_gold:
            contents.append("G")  # Gold
        if self.has_wall:
            contents.append("X")  # Wall
            
        return "[" + ",".join(contents) + "]" if contents else "[ ]"
