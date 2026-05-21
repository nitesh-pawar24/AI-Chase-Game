# AI-Chase-Game

A grid-based chase game built with Python and Pygame where you navigate a maze to reach a goal while an AI hunts you down. The AI difficulty changes which pathfinding algorithm it uses — making it genuinely harder, not just faster.



Gameplay

You control a black character on a grid. Reach the gold goal tile before the timer runs out — without getting caught by the green AI.

Easy mode — The AI uses Greedy Best-First Search. It rushes toward you but gets confused by obstacles, so you can trick it.

Hard mode — The AI uses A* Search. It always finds the shortest path. There's no fooling it.

The map is randomly generated every round, and the game guarantees a valid path always exists from the AI to you and from you to the goal.



Features

- Two pathfinding algorithms — A* (Hard) and Greedy Best-First (Easy), implemented from scratch in pathfinding.py
- Animated menu background — A live maze runs in the background with BFS-driven dots chasing each other as a preview of the game
- Danger zone effect — The screen flashes red when the AI is within 3 tiles of you
- 3-second countdown before each round with scaling animation and sound
- Score system — You earn time_left × 10 points for reaching the goal
- Procedurally generated sounds — All 7 sound effects (footsteps, win/lose stings, countdown, menu music) are synthesized as WAV files by generate_sounds.py using pure numpy — no audio assets needed
- Optional sprite assets — Place player.jpg, ai.jpg, and goal.jpg in assets/ to use custom images; falls back to colored rectangles if they're missing
- Responsive HUD — Labels and fonts scale for both the 10×10 (400px) and 15×15 (600px) grid sizes


How the Pathfinding Works?

A* (Hard mode) uses f(n) = g(n) + h(n) — cost so far plus Manhattan distance to the goal. It always finds the optimal shortest path, so the AI will never waste a move.

Greedy Best-First Search (Easy mode) uses only h(n) — Manhattan distance to the goal, ignoring path cost. It moves toward you fast but can get stuck routing around obstacles, giving you windows to escape.
