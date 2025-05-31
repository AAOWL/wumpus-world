"""Wumpus World 게임 실행 모듈

이 모듈은 게임의 진입점으로, 다음과 같은 기능을 제공합니다:
1. 게임 시작 및 종료
2. 사용자 입력 처리
3. 게임 상태 표시
"""

import sys
import time
from typing import Optional

from wumpus.controller.controller import Controller
from wumpus.models.action import Action


def print_title():
    """게임 타이틀 출력"""
    title = """
    ██╗    ██╗██╗   ██╗███╗   ███╗██████╗ ██╗   ██╗███████╗
    ██║    ██║██║   ██║████╗ ████║██╔══██╗██║   ██║██╔════╝
    ██║ █╗ ██║██║   ██║██╔████╔██║██████╔╝██║   ██║███████╗
    ██║███╗██║██║   ██║██║╚██╔╝██║██╔═══╝ ██║   ██║╚════██║
    ╚███╔███╔╝╚██████╔╝██║ ╚═╝ ██║██║     ╚██████╔╝███████║
     ╚══╝╚══╝  ╚═════╝ ╚═╝     ╚═╝╚═╝      ╚═════╝ ╚══════╝
                        WORLD
    """
    print(title)
    print("\n" + "=" * 60)
    print("황금을 찾아 안전하게 탈출하세요!")
    print("=" * 60 + "\n")


def print_help():
    """도움말 출력"""
    help_text = """
사용 가능한 명령어:
    w: 앞으로 이동
    a: 왼쪽으로 회전
    d: 오른쪽으로 회전
    s: 화살 발사
    g: 금 줍기
    c: 탈출하기
    h: 도움말 보기
    q: 게임 종료
    """
    print(help_text)


def get_action(command: str) -> Optional[Action]:
    """사용자 입력을 Action으로 변환

    Args:
        command: 사용자가 입력한 명령어

    Returns:
        Optional[Action]: 해당하는 Action 또는 None
    """
    action_map = {
        "w": Action.FORWARD,
        "a": Action.TURN_LEFT,
        "d": Action.TURN_RIGHT,
        "s": Action.SHOOT_ARROW,
        "g": Action.GRAB_GOLD,
        "c": Action.CLIMB,
    }
    return action_map.get(command.lower())


def main():
    """게임 메인 함수"""
    print_title()
    print_help()

    while True:
        # 새 게임 시작 여부 확인
        start = input("\n새 게임을 시작하시겠습니까? (y/n): ")
        if start.lower() != "y":
            print("\n게임을 종료합니다. 안녕히 가세요!")
            sys.exit(0)

        # 게임 컨트롤러 생성 및 초기화
        controller = Controller()
        controller.start_game()

        # 게임 루프
        while not controller.is_game_over:
            # DEBUG용 path_stack 출력
            controller.agent.print_path_stack_status()

            # 사용자 입력 받기
            command = input("\n행동을 선택하세요 (h: 도움말): ")

            # 도움말
            if command.lower() == "h":
                print_help()
                continue

            # 게임 종료
            if command.lower() == "q":
                print("\n게임을 종료합니다.")
                sys.exit(0)

            # 행동 변환 및 실행
            action = get_action(command)
            if action is None:
                print("잘못된 명령입니다. 'h'를 입력하여 도움말을 확인하세요.")
                continue

            # 행동 실행 (자동으로 상태가 출력됨)
            if not controller.step():
                break  # 게임 종료

        # 게임 결과 출력 (승리/패배)
        is_victory, final_score = controller._get_game_result()

        # 잠시 대기 후 다음 게임 준비
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n게임이 강제 종료되었습니다. 안녕히 가세요!")
        sys.exit(0)
