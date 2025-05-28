import pytest
from wumpus.agent.knowledge_base import Knowledge_base, Knowledge_Cell
from wumpus.models.location import Location

wall_cell = Knowledge_Cell(
    visited=False, possible_wumpus=0, possible_pit=0, safe=False, wall=True
)
visited_cell = Knowledge_Cell(
    visited=True, possible_wumpus=0, possible_pit=0, safe=False, wall=False
)


@pytest.fixture
def knowledge_base():
    # 4x4 grid의 Knowledge_base 초기화
    kb = Knowledge_base(size=4)
    return kb


def test_valid_cell_selection(knowledge_base):
    kb = knowledge_base
    current_location = Location(1, 1)
    # (0,1), (2,1), (1,0), (1,2) 인접 셀

    # (0,1): wall, (2,1): safe
    kb.grid[0][1] = wall_cell
    kb.grid[2][1] = visited_cell

    # (1,2): (1, 0)에 비해서 위험도가 높음
    kb.grid[1][2].possible_wumpus = 2

    valid_cell = kb.get_adjacent_cells(current_location)

    expected_cells = [(1, 2), (1, 0)]
    result_cells = [(cell.row, cell.col) for cell in valid_cell]

    assert sorted(result_cells) == sorted(
        expected_cells
    ), f"예상된 유효 셀 {expected_cells}, 실제 {result_cells}"
