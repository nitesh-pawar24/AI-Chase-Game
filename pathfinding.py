import heapq

def heuristic(a, b):
    # Manhattan distance: |x1 - x2| + |y1 - y2|
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(grid_size, start, goal, obstacles):
    """
    A* Search — uses f(n) = g(n) + h(n).
    Guarantees the SHORTEST path to the target.
    Used for Hard mode: AI always takes the optimal route.
    """
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    close_set = set()
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    o_heap = []

    heapq.heappush(o_heap, (f_score[start], start))

    while o_heap:
        current = heapq.heappop(o_heap)[1]

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]  # Path from start to goal

        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j

            if 0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size:
                if neighbor in obstacles or neighbor in close_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                    heapq.heappush(o_heap, (f_score[neighbor], neighbor))

    return None  # No path exists


def best_first_search(grid_size, start, goal, obstacles):
    """
    Greedy Best First Search — uses only h(n) (heuristic distance to goal).
    Does NOT track path cost g(n), so it can take non-optimal routes.
    Used for Easy mode: AI moves greedily toward the player but can be misled
    by obstacles, making it easier to escape than the A* AI in Hard mode.
    """
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    visited   = set()
    came_from = {}
    h_score   = heuristic(start, goal)
    o_heap    = [(h_score, start)]

    while o_heap:
        _, current = heapq.heappop(o_heap)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]  # Path from start to goal

        if current in visited:
            continue
        visited.add(current)

        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j

            if 0 <= neighbor[0] < grid_size and 0 <= neighbor[1] < grid_size:
                if neighbor in obstacles or neighbor in visited:
                    continue

                if neighbor not in came_from:
                    came_from[neighbor] = current
                    h = heuristic(neighbor, goal)
                    heapq.heappush(o_heap, (h, neighbor))

    return None  # No path exists
