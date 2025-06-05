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
    is_scream: bool = False

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
        """
        한 단계 진행한다.

        1) 이미 게임 종료 플래그가 세워져 있으면 False를 반환하며 즉시 종료.
        2) 이전 위치에서 Agent가 사망했는지 확인하고, 
        사망 상태라면 _handle_death_and_respawn()로 부활 처리 후 True 반환(게임 계속).
        3) 현재 위치에서 환경으로부터 Percept을 반환.
            - bump 여부는 self.is_bump 플래그를 사용해 전달.
            - 받은 Percept를 agent.update_state_with_percept()로 KB에 모두 반영.
        4) 최신 지식 베이스를 출력(self.agent.kb._print_knowledge_base()).
        5) 에이전트의 decide_next_action(percept)를 호출해 다음 행동을 결정.
        6) 결정된 action을 _process_action(action)으로 수행하고, 
        결과(success), bump 여부(self.is_bump) 갱신.
        7) 이동(혹은 다른 action) 후에 env.check_for_death(self.agent.location)으로 
        에이전트 사망 여부를 다시 확인하여 self.agent.is_alive를 False로 설정.
        8) 현재 게임 상태(_print_game_state())를 화면에 출력하고, total_steps를 1 증가.
        9) 스텝 한계를 확인(check_step_limit()):
            - total_steps가 200 이상이면 False 반환(게임 종료).
            - 그렇지 않으면 True 반환(게임 계속).

        **특이사항**
            - Agent가 사망해도 게임이 즉시 끝나지 않습니다. 사망 시에는 부활 로직(_handle_death_and_respawn)이 먼저 실행되고,
            그 결과 True를 반환하여 다음 스텝으로 넘어갑니다.
            - 게임 종료 조건은 오직 스텝 수가 200을 넘는 경우뿐입니다.
        
        Returns:
            bool: 게임이 계속 진행 중이면 True, 종료되었으면 False
        """

        # 1)
        if self.is_game_over:
            return False

        # 2) 사망/부활 로직 
        if self._handle_death_and_respawn():
            return True

        # 3) percept 수집 + KB 업데이트
        percept = self.env.get_percept(self.agent.location, bump=self.is_bump, scream=self.is_scream)
        self.agent.update_state_with_percept(percept)

        # 4) KB 출력 (디버깅)
        self.agent.kb._print_knowledge_base()

        # 5) 행동 결정 로직. 
        # 화살 사용 로직 X 구현필요 -> gold가 없는 상태로 시작지점(1,1)에 돌아왔다면, has_wumpus가 가장 높은 곳으로 이동하여 화살사용 하면 될듯
        action = self.agent.decide_next_action(percept)

        # 6) 행동 수행, bump 여부 판단
        success, self.is_bump , self.is_scream = self._process_action(action)  # type: ignore
        
        # 7) agent 이동 한/ 사망 체크
        if self.env.check_for_death(self.agent.location):
            self.agent.is_alive = False  # agent 상태 사망으로 변경

        # 8) 상태 출력
        self.agent.print_path_stack_status()
        self._print_game_state()
        self.total_steps += 1

        # 9) 스텝 한계 체크
        return self.check_step_limit()

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

    def _process_action(self, action: Action) -> tuple[bool, bool, bool]:
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

        is_bump = action == Action.FORWARD and message == "벽에 부딪혔습니다."
        is_scream = action == Action.SHOOT_ARROW and message == "Wumpus를 죽였습니다!"

        # 결과 메시지 저장
        if message:
            self.messages.append(f"Step {self.total_steps + 1}: {message}")

        # 점수 업데이트
        self.env.score += score_delta

        # 행동이 성공한 경우, 에이전트 상태 업데이트
        if success:
            if action == Action.FORWARD:
                # 새 위치로 이동
                self.agent._move_forward()

            elif action == Action.TURN_LEFT:
                # 왼쪽으로 회전
                self.agent._turn_left()
            elif action == Action.TURN_RIGHT:
                # 오른쪽으로 회전
                self.agent._turn_right()
            elif action == Action.SHOOT_ARROW:
                # 화살 사용
                self.agent._shoot_arrow()
            elif action == Action.GRAB_GOLD:
                # 금 획득
                self.agent.has_gold = True
            elif action == Action.CLIMB and self.agent.location == Location(1, 1):
                # 탈출 성공
                self.is_game_over = True

        return success, is_bump, is_scream

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
        print(f"화살 개수: {f'{self.agent.count_arrow}'}")
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
            self.agent.has_gold
            and self.agent.location == Location(1, 1)
            and self.is_game_over
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
    
    def _handle_death_and_respawn(self) -> bool:
        
        """
        ** 해당 메서드도 total_steps를 증가시킨다. **

        Agent가 죽었는지 확인. 죽었다면
            - 죽은 위치에 kb에 unsafe 표기.
            - 죽기 직전의 위치로 되돌아 감.
            - return True

        죽지 않았다면
            - return False
        """

        # Agent가 이전턴에 죽었다면 부활 로직
        if self.env.check_for_death(self.agent.location):
            dead_at_location = self.agent.location
            self.messages.append(f"에이전트가 {dead_at_location}에서 사망했습니다!")

            # 1. 죽은 장소에 unsafe 표기. env의 has_agent 지우기
            self.agent.kb.mark_unsafe(dead_at_location)

            # 2. 시작 장소에서 부활. 죽기 직전의 지점으로 되돌아가기.
            self.agent.location = self.agent.path_stack.pop()
            self.env.update_agent_position_in_grid(
                dead_at_location, self.agent.location
            )
            print(f"DEBUG: agent는 이전칸인 {self.agent.location} 으로 돌아갑니다.")

            # 3. 죽음으로 인해 게임이 종료되지 않음.
            self.agent.is_alive = True

            # 4. total_steps 증가
            self.total_steps += 1
            
            return True
        
        # Agent가 이전턴에 죽지 않았음
        else:
            return False
        
    def check_step_limit(self) -> bool:
        """
        total_steps가 200이 넘어가는 경우, 실패로 종료(game over)
        """
        if self.total_steps >= 200:
            return self.is_game_over
        else:
            return not self.is_game_over