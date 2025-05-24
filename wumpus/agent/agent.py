def adjacent_cells(x, y, size=4):
    candidates = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
    return [(nx, ny) for nx, ny in candidates if 0 <= nx < size and 0 <= ny < size]
