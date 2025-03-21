import pygame
from collections import deque
from copy import deepcopy
import heapq
import logging
import sys

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Khởi tạo pygame
pygame.init()

# Cấu hình màn hình
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
POLE_WIDTH = 20
POLE_HEIGHT = 200
RING_HEIGHT = 40
POLE_SPACING = 120
POLE_BASE_Y = 500
POLE_TOP_Y = POLE_BASE_Y - POLE_HEIGHT
RING_WIDTH = 80

# Màu sắc
COLORS = {
    'purple': (128, 0, 128),
    'orange': (255, 165, 0),
    'pink': (255, 192, 203),
    'green': (0, 128, 0),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'gray': (128, 128, 128),
    'yellow': (255, 255, 0)
}

# Thiết lập màn hình
try:
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Color Sorting Game")
except Exception as e:
    logging.error(f"Error initializing screen: {e}")
    raise

# Font cho văn bản
try:
    font = pygame.font.Font(None, 36)
except Exception as e:
    logging.error(f"Error initializing font: {e}")
    raise

class GameState:
    def __init__(self):
        self.poles = [
            ['purple', 'orange', 'pink', 'green'],
            ['orange', 'green', 'purple', 'pink'],
            ['green', 'pink', 'orange', 'purple'],
            ['pink', 'purple', 'green', 'orange'],
            [],
            []
        ]
        self.moves = []
        self.max_rings = 4
        self.max_moves = 50

    def get_movable_rings(self, pole_index):
        logging.debug(f"Getting movable rings for pole {pole_index}: {self.poles[pole_index]}")
        if not self.poles[pole_index]:
            return []

        movable_rings = []
        top_color = self.poles[pole_index][-1]

        for ring in reversed(self.poles[pole_index]):
            if ring == top_color:
                movable_rings.append(ring)
            else:
                break

        movable_rings.reverse()
        logging.debug(f"Movable rings: {movable_rings}")
        return movable_rings

    def is_valid_move(self, from_pole, to_pole):
        logging.debug(f"Checking if move from pole {from_pole} to pole {to_pole} is valid")
        if from_pole < 0 or from_pole >= len(self.poles) or to_pole < 0 or to_pole >= len(self.poles):
            return False, "Invalid pole index"

        if not self.poles[from_pole]:
            return False, "Source pole is empty"

        if len(self.poles[to_pole]) + 1 > self.max_rings:
            return False, f"Destination pole cannot hold more rings (max {self.max_rings})"

        if not self.poles[to_pole]:
            return True, "Valid move: Destination pole is empty"

        if self.poles[from_pole][-1] != self.poles[to_pole][-1]:
            return False, f"Top ring colors do not match: {self.poles[from_pole][-1]} (source) vs {self.poles[to_pole][-1]} (destination)"

        return True, "Valid move"

    def make_move(self, from_pole, to_pole):
        logging.debug(f"Attempting to move from pole {from_pole} to pole {to_pole}")
        is_valid, reason = self.is_valid_move(from_pole, to_pole)
        if is_valid:
            movable_rings = self.get_movable_rings(from_pole)
            ring_to_move = movable_rings[-1:][0]
            self.poles[from_pole].pop()
            self.poles[to_pole].append(ring_to_move)
            self.moves.append((from_pole, to_pole))
            logging.debug(f"Move successful: {self.poles}")
            return True, "Move successful"
        
        logging.debug(f"Move invalid: {reason}")
        return False, reason

    def is_solved(self):
        full_poles = 0
        total_rings = 0
        colors_seen = set()

        for pole in self.poles:
            if pole:
                if len(pole) == self.max_rings:
                    first_color = pole[0]
                    if all(ring == first_color for ring in pole):
                        if first_color in colors_seen:
                            return False
                        colors_seen.add(first_color)
                        full_poles += 1
                        total_rings += len(pole)
                    else:
                        return False
                else:
                    return False

        return full_poles == 4 and total_rings == 16

def heuristic(state):
    score = 0
    for pole in state.poles:
        if pole:
            colors = set(pole)
            if len(pole) == 4 and len(colors) == 1:
                score -= 10
            else:
                score += len(colors) - 1
    return score

def find_solution(initial_state):
    visited = set()
    pq = [(0, 0, initial_state)]

    while pq:
        _, moves, current = heapq.heappop(pq)
        
        if current.is_solved():
            return current.moves

        state_hash = str(current.poles)
        if state_hash in visited:
            continue

        visited.add(state_hash)

        for from_pole in range(6):
            for to_pole in range(6):
                if from_pole != to_pole:
                    is_valid, _ = current.is_valid_move(from_pole, to_pole)
                    if is_valid:
                        next_state = deepcopy(current)
                        ring_to_move = next_state.poles[from_pole][-1]
                        next_state.poles[from_pole].pop()
                        next_state.poles[to_pole].append(ring_to_move)
                        next_state.moves.append((from_pole, to_pole))
                        priority = moves + 1 + heuristic(next_state)
                        heapq.heappush(pq, (priority, moves + 1, next_state))

    return None

def get_next_hint(state):
    best_score = float('inf')
    best_move = None

    for from_pole in range(6):
        for to_pole in range(6):
            if from_pole != to_pole:
                is_valid, _ = state.is_valid_move(from_pole, to_pole)
                if is_valid:
                    next_state = deepcopy(state)
                    ring_to_move = next_state.poles[from_pole][-1]
                    next_state.poles[from_pole].pop()
                    next_state.poles[to_pole].append(ring_to_move)
                    next_state.moves.append((from_pole, to_pole))
                    score = heuristic(next_state)
                    if score < best_score:
                        best_score = score
                        best_move = (from_pole, to_pole)

    return best_move

def draw_game(state, selected_pole):
    try:
        logging.debug("Drawing game state")
        screen.fill(COLORS['white'])

        for i in range(6):
            pole_x = 50 + i * POLE_SPACING
            color = COLORS['yellow'] if i == selected_pole else COLORS['gray']
            pygame.draw.rect(screen, color, (pole_x, POLE_TOP_Y, POLE_WIDTH, POLE_HEIGHT))
            
            for j, ring in enumerate(state.poles[i]):
                ring_y = POLE_BASE_Y - (j + 1) * RING_HEIGHT
                pygame.draw.rect(screen, COLORS[ring], (pole_x - 30, ring_y, RING_WIDTH, RING_HEIGHT))

        for i in range(6):
            pole_x = 50 + i * POLE_SPACING
            text = font.render(str(i), True, COLORS['black'])
            screen.blit(text, (pole_x + 5, POLE_BASE_Y + 10))

        moves_text = font.render(f"Moves: {len(state.moves)}/{state.max_moves}", True, COLORS['black'])
        screen.blit(moves_text, (10, 10))

        controls_text = font.render("Controls: 0-5 to select, H for hint, R to reset, Q to quit", True, COLORS['black'])
        screen.blit(controls_text, (10, WINDOW_HEIGHT - 40))

        pygame.display.flip()
        logging.debug("Game state drawn successfully")
    except Exception as e:
        logging.error(f"Error in draw_game: {e}")
        raise

def main():
    game_state = GameState()
    selected_pole = None
    running = True
    hint_message = "Select a pole (0-5) to move rings from"

    while running:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pass  # Không thoát khi đóng cửa sổ
                elif event.type == pygame.KEYDOWN:
                    logging.debug(f"Key pressed: {event.key}")
                    
                    pole = None
                    if event.key == pygame.K_0 or event.key == pygame.K_KP0:
                        pole = 0
                    elif event.key == pygame.K_1 or event.key == pygame.K_KP1:
                        pole = 1
                    elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                        pole = 2
                    elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                        pole = 3
                    elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                        pole = 4
                    elif event.key == pygame.K_5 or event.key == pygame.K_KP5:
                        pole = 5
                    elif event.key == pygame.K_q:
                        logging.debug("Quit key pressed")
                        running = False
                        break
                    elif event.key == pygame.K_h:
                        hint = get_next_hint(game_state)
                        if hint:
                            from_pole, to_pole = hint
                            hint_message = f"Hint: Move from pole {from_pole} to pole {to_pole}"
                        else:
                            hint_message = "No valid moves available!"
                    elif event.key == pygame.K_r:
                        game_state = GameState()
                        selected_pole = None
                        hint_message = "Game reset! Select a pole (0-5) to move rings from."

                    if pole is not None:
                        logging.debug(f"Selected pole: {pole}")
                        if selected_pole is None:
                            if game_state.poles[pole]:
                                selected_pole = pole
                                hint_message = f"Selected pole {pole}. Now select destination pole (0-5)."
                            else:
                                hint_message = "No rings to move from this pole! Select another pole."
                        else:
                            success, reason = game_state.make_move(selected_pole, pole)
                            if success:
                                hint_message = f"Moved from pole {selected_pole} to pole {pole}"
                            else:
                                hint_message = f"Invalid move: {reason}"
                            selected_pole = None

            if not running:
                break

            draw_game(game_state, selected_pole)

            if hint_message:
                hint_text = font.render(hint_message, True, COLORS['black'])
                screen.blit(hint_text, (10, 50))
                pygame.display.update()

            if len(game_state.moves) >= game_state.max_moves and not game_state.is_solved():
                lose_text = font.render("You Lose! Exceeded maximum moves.", True, COLORS['black'])
                screen.blit(lose_text, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(2000)
                game_state = GameState()
                selected_pole = None
                hint_message = "Game reset! Select a pole (0-5) to move rings from."
                
            if game_state.is_solved():
                win_text = font.render("You Win!", True, COLORS['green'])
                screen.blit(win_text, (WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(3000)  # Hiển thị "You Win!" trong 3 giây (3000ms)
                game_state = GameState()  # Chuyển sang màn mới
                selected_pole = None
                hint_message = "New game started! Select a pole (0-5) to move rings from."

            pygame.time.delay(30)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            pygame.quit()
            raise

    pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Error in program: {e}")
        pygame.quit()
        sys.exit()