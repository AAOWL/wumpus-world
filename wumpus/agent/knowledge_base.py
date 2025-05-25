from dataclasses import field
from typing import Set

from wumpus.models.direction import Direction
from wumpus.models.location import Location
from wumpus.models.percept import Percept
    
class Knowledge_base:
    """
    agent의 내부 모델(관측된 환경)을 저장
    """

    # 지도 정보
    visited: Set[Location] = field(default_factory=set)
    unsafe: Set[Location] = field(default_factory=set)
    possible_wumpus: Set[Location] = field(default_factory=set)
    possible_pit: Set[Location] = field(default_factory=set)


    def update_knowledge(self, location: Location, percept: Percept) -> None:
        """현재 위치에서의 감각 정보를 바탕으로 지식 업데이트
        
        Args:
            percept: 현재 위치에서의 감각 정보
        """
        current = location
        
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