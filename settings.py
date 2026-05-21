import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GREY = (120, 120, 130)

CELL_SIZE = 40
FPS = 60

# Reorganized Table
# Difficulty -> Grid Size -> {Obstacles, AI Speed, Timer}
DIFFICULTY_DATA = {
    "Easy": {
        10: {"obs": 8, "speed": 0.2, "time": 30},
        15: {"obs": 17, "speed": 0.2, "time": 40}
    },
    "Hard": {
        10: {"obs": 11, "speed": 0.2, "time": 15},
        15: {"obs": 23, "speed": 0.2, "time": 20}
    }
}