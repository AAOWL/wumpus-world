# tests/agent/test_knowledge_base.py
from wumpus.agent.knowledge_base import Knowledge_base
from wumpus.models.location import Location

def test_knowledge_base_initial_state():
    # Knowledge_base 객체가 올바르게 초기화되는지 테스트
    kb = Knowledge_base()
    assert len(kb.visited) == 0
    assert len(kb.unsafe) == 0
    assert len(kb.possible_wumpus) == 0
    assert len(kb.possible_pit) == 0

def test_knowledge_base_add_visited():
    # visited 세트에 Location이 올바르게 추가되는지 테스트
    kb = Knowledge_base()
    loc1 = Location(0, 0)
    loc2 = Location(1, 0)

    kb.visited.add(loc1)
    assert loc1 in kb.visited
    assert len(kb.visited) == 1

    kb.visited.add(loc2)
    assert loc2 in kb.visited
    assert len(kb.visited) == 2

    # 중복 추가 시 크기 변화 없음
    kb.visited.add(loc1)
    assert len(kb.visited) == 2