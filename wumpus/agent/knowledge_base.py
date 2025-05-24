from agent import adjacent_cells

def interpret_percept(percept, x, y, knowledge, grid_size=4):
    if (x, y) == (0, 0):
        knowledge.setdefault((x, y), {})
        knowledge[(x, y)]['safe'] = True

    if 'Breeze' in percept:
        for nx, ny in adjacent_cells(x, y, grid_size):
            knowledge.setdefault((nx, ny), {})
            knowledge[(nx, ny)]['maybe_pit'] = True

    if 'Stench' in percept:
        for nx, ny in adjacent_cells(x, y, grid_size):
            knowledge.setdefault((nx, ny), {})
            knowledge[(nx, ny)]['maybe_wumpus'] = True

    if 'Glitter' in percept:
        knowledge.setdefault((x, y), {})
        knowledge[(x, y)]['gold'] = True

    if 'Bump' in percept:
        knowledge.setdefault((x, y), {})
        knowledge[(x, y)]['bump'] = True

    if 'Scream' in percept:
        knowledge['wumpus_dead'] = True
