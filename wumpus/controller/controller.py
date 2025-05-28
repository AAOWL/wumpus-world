"""
게임 컨트롤러 클래스.

게임 전체 흐름을 제어하고, 게임 상태를 관리합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from wumpus.agent.agent import Agent
from wumpus.models.action import Action
from wumpus.models.location import Location
from wumpus.models.direction import Direction
from wumpus.models.percept import Percept
from wumpus.environment.environment import Environment


@dataclass
class Controller:
    """Wumpus World 게임 컨트롤러
    
    게임의 전체적인 흐름을 제어하고 상태를 관리합니다.
    Agent와 Environment 사이의 상호작용을 조정합니다.
    """
    
    # 게임 구성 요소
    env: Environment = field(default_factory=Environment)
    agent: Agent = field(default_factory=Agent)
    is_bump: bool = False
    # 게임 상태
    is_game_over: bool = False
    total_steps: int = 0
    messages: List[str] = field(default_factory=list)
    
    def start_game(self) -> None:
        """새로운 게임 시작"""
        self.is_game_over = False
        self.total_steps = 0
        self.messages.clear()
        
        # 환경과 에이전트 초기화
        self.env = Environment()
        self.agent = Agent()
        
        print("새로운 게임을 시작합니다!")
        self._print_game_state()
    
    def step(self) -> bool:
        """한 단계 진행
        
        Returns:
             bool: 게임이 계속 진행 중이면 True, 종료되었으면 False
        """
        if self.is_game_over:
            return False
        
        # 감각 수집 (bump가 발생하면 인자로 넘겨줌)
        percept = self.env.get_percept(self.agent.location, bump=self.is_bump)

        # 지식 업데이트
        self.agent.kb.update_with_percept(
            self.agent.location, percept, self.agent.direction
        )

        # KB기반 행동 결정 로직 (wumpus/pit에 빠질 경우, (1,1)에서 부활하여 재시작하는것 X 추후 수정)
        if percept.glitter:
            action = Action.GRAB_GOLD
            print("금 발견! 금을 획득하고 탈출을 준비합니다.")
            self.agent.backtrack_to_start()

        else:
            # glitter 없으면 다음 행동 결정
            action = self.agent.move_to_safest_adjacent_cell()
            if action is None:
                # 이동할 위치 없을 때 backtrack
                print("이동 가능한 위치가 없어 backtrack 시도")
                return self.agent.backtrack() is None  # backtrack 성공 시 게임 계속 진행
                
        # 행동 수행, bump 여부 판단
        success, self.is_bump = self._process_action(action)



        self._print_game_state()
        self.total_steps += 1
        
        return not self.is_game_over
    
    def run_game(self) -> Tuple[bool, int]:
        """게임을 끝까지 실행
        
        Returns:
            Tuple[bool, int]:
                - bool: 승리 여부
                - int: 최종 점수
        """
        self.start_game()
        
        while self.step():
            pass
            
        return self._get_game_result()
    
    def _process_action(self, action: Action) -> tuple[bool, bool]:
        """에이전트의 행동을 처리
        
        Args:
            action: 수행할 행동
        Returns:
            tuple[bool, bool]: (행동 성공 여부, bump 발생 여부)
        """
        # 환경에 행동 수행 요청
        success, message, score_delta = self.env.perform_action(
            action, self.agent.location, self.agent.direction
        )

        is_bump = (action == Action.FORWARD and message == "벽에 부딪혔습니다.")
        
        # 결과 메시지 저장
        if message:
            self.messages.append(f"Step {self.total_steps + 1}: {message}")
        
        # 점수 업데이트
        self.env.score += score_delta
        
        # 행동이 성공한 경우, 에이전트 상태 업데이트
        if success:
            if action == Action.FORWARD:
                # 새 위치로 이동
                self.agent.location = self.agent.location.move(self.agent.direction)
            elif action == Action.TURN_LEFT:
                # 왼쪽으로 회전
                directions = list(Direction)
                current_idx = directions.index(self.agent.direction)
                self.agent.direction = directions[(current_idx - 1) % 4]
            elif action == Action.TURN_RIGHT:
                # 오른쪽으로 회전
                directions = list(Direction)
                current_idx = directions.index(self.agent.direction)
                self.agent.direction = directions[(current_idx + 1) % 4]
            elif action == Action.SHOOT_ARROW:
                # 화살 사용
                self.agent.has_arrow = False
            elif action == Action.GRAB_GOLD:
                # 금 획득
                self.agent.has_gold = True
            elif action == Action.CLIMB and self.agent.location == Location(1, 1):
                # 탈출 성공
                self.is_game_over = True
                
        # 게임 종료 조건 체크
        if self.env.is_game_over:
            self.is_game_over = True

        return success, is_bump
    
    def _print_game_state(self) -> None:
        """현재 게임 상태를 출력"""
        print("\n" + "=" * 40)
        print("=== Wumpus World 게임 상태 ===")
        print("=" * 40)
        
        # 기본 정보
        print(f"진행 단계: {self.total_steps}")
        print(f"현재 점수: {self.env.score}")
        print(f"에이전트 위치: {self.agent.location}")
        print(f"에이전트 방향: {self.agent.direction.name}")
        print(f"화살 보유: {'예' if self.agent.has_arrow else '아니오'}")
        print(f"금 보유: {'예' if self.agent.has_gold else '아니오'}")
        
        # 최근 메시지
        if self.messages:
            print("\n=== 최근 메시지 ===")
            for msg in self.messages[-3:]:  # 최근 3개 메시지만
                print(msg)
        
        # 환경 상태
        print("\n=== 월드 맵 ===")
        self._print_environment()
        print("=" * 40 + "\n")
    
    def _print_environment(self) -> None:
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
            print("+" + "---+" * self.env.size)
            
        # 격자 출력
        print_separator()
        for row in range(self.env.size):
            # 셀 내용 (각 셀은 3칸 고정 너비)
            print("|", end="")
            for col in range(self.env.size):
                cell_str = str(self.env.grid[row][col])
                print(f"{cell_str:^3}", end="|")  # :^3는 3칸 중앙 정렬
            print()
            print_separator()
    
    def _get_game_result(self) -> Tuple[bool, int]:
        """게임 결과 반환
        
        Returns:
            Tuple[bool, int]:
                - bool: 승리 여부 (금을 가지고 탈출 성공 시 True)
                - int: 최종 점수
        """
        is_victory = (
            self.agent.has_gold and 
            self.agent.location == Location(1, 1) and
            self.is_game_over
        )
        
        # 결과 메시지 출력
        print("\n" + "=" * 40)
        print("=== 게임 종료 ===")
        print("=" * 40)
        print(f"총 진행 단계: {self.total_steps}")
        print(f"최종 점수: {self.env.score}")
        print(f"결과: {'승리!' if is_victory else '패배...'}")
        
        if is_victory:
            print("축하합니다! 금을 찾아 무사히 탈출하는데 성공했습니다!")
        else:
            print("다음에 다시 도전해보세요!")
            
        print("=" * 40)
        
        return is_victory, self.env.score

