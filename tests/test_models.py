# pylint: disable=missing-class-docstring, missing-function-docstring
"""tests for the types module (Action, Location, Percept)"""

from wumpus.models.action import Action
from wumpus.models.location import Location
from wumpus.models.direction import Direction
from wumpus.models.percept import Percept


def test_action_enum_values():
    # auto()로 1부터 순서대로 할당됐는지

    for idx, act in enumerate(Action, start=1):
        assert act.value == idx


def test_location_move():
    loc = Location(row=2, col=3)

    # 각 방향으로 이동 시 올바른 좌표가 나오는지
    for d in Direction:
        new_loc = loc.move(d)
        dr, dc = d.delta
        assert new_loc == Location(2 + dr, 3 + dc)


def test_percept_fields_and_repr():
    p = Percept(stench=True, breeze=False, glitter=True, scream=False)

    # 필드 값 확인
    assert p.stench is True
    assert p.breeze is False
    assert p.glitter is True
    assert p.scream is False

    # dataclass 기본 repr 확인
    assert repr(p) == "Percept(stench=True, breeze=False, glitter=True, scream=False)"
