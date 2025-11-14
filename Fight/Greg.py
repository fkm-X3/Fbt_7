import pygame
import random
import sys
import math
import os

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cube Combat")

BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0) 
WHITE = (255, 255, 255)
CYAN = (0, 255, 255) 

PURPLE_TUPLE = (128, 0, 128) 

CUBE_SIZE = 50

blue_x = 20
blue_y = HEIGHT // 2 - CUBE_SIZE // 2
red_x = WIDTH - CUBE_SIZE - 20
red_y = HEIGHT // 2 - CUBE_SIZE // 2

MOVE_SPEED = 5

AI_MOVE_SPEED = 3

ATTACK_RANGE = 100
MAINTAIN_RANGE_MIN = 150
MAINTAIN_RANGE_MAX = 350        
RETREAT_HEALTH_THRESHOLD = 25   

CHARGE_SPEED = 15              
CHARGE_INITIATE_CHANCE = 0.001 
CHARGE_FLASH_CYCLES = 2        
FLASH_DURATION_MS = 200        
ENDLAG_DURATION_MS = 2000      
CHARGE_ATTACK_DAMAGE = 25      

AI_SLASH_FLASH_CYCLES = 3       
AI_FLASH_DURATION_MS = 150      
AI_BEAM_RANGE = 300             
AI_BEAM_WIDTH = 10              
AI_BEAM_LENGTH = 700            
AI_BEAM_SPEED = 0.1             

ATTACK_DAMAGE = 20

SPECIAL_ATTACK_DAMAGE = 25
HITBOX_DURATION_MS = 500       
SPECIAL_ATTACK_COOLDOWN_MS = 3000 

AI_SPECIAL_ATTACK_DAMAGE = 30 
AI_SPECIAL_HITBOX_DURATION_MS = 600
AI_SPECIAL_ATTACK_COOLDOWN_MS = 4000 
AI_SPECIAL_ATTACK_RANGE = 200        

INITIAL_BLUE_ACTIVE = True
INITIAL_RED_ACTIVE = True
INITIAL_BLUE_HEALTH = 100
INITIAL_RED_HEALTH = 100
INITIAL_RED_CUBE_MODE = "Maintain"

PARRY_WINDOW_DURATION_MS = 200 # Duration for the parry effect

font = pygame.font.Font(None, 36)

initial_game_state = {
    'blue_active': INITIAL_BLUE_ACTIVE,
    'red_active': INITIAL_RED_ACTIVE,
    'blue_health': INITIAL_BLUE_HEALTH,
    'red_health': INITIAL_RED_HEALTH,
    'blue_x': blue_x,
    'blue_y': blue_y,
    'red_x': red_x,           
    'red_y': red_y,          
    'attack_damage': ATTACK_DAMAGE, 
    'move_speed': MOVE_SPEED,       
    'game_over': False,
    'red_cube_mode': INITIAL_RED_CUBE_MODE, 

    'charge_state': 'Idle',       
    'flash_timer': 0,             
    'flash_count': 0,             
    'charge_dx': 0,               
    'charge_dy': 0,               
    'endlag_timer': 0.0,          

    'purple_hitbox_active': False,
    'purple_hitbox_rect': None,    
    'hitbox_timer': 0,             
    'last_direction': 'right',     
    'special_attack_cooldown_timer': 0,

    'ai_cyan_beam_active': False,     
    'ai_beam_angle': 0.0,             
    'ai_hitbox_timer': 0,
    'ai_last_direction': 'left', 
    'ai_special_attack_cooldown_timer': 0,
    'ai_attack_state': 'Idle',    
    
    'parry_active': False,
}

game_state = initial_game_state.copy()

STATS_FILE = "stats.txt" # Constant for the stats file
# NEW: Debug file constant
DEBUG_FILE = "debug.txt"
is_debug_mode = False # Global flag for debug mode

def load_stats():
    """Reads kill counts from stats.txt or initializes them."""
    stats = {'red_kills': 0, 'blue_kills': 0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 1:
                    # Line 1: "red cube killed: X"
                    red_line = lines[0].strip()
                    if ":" in red_line:
                        stats['red_kills'] = int(red_line.split(':')[1].strip())
                if len(lines) >= 2:
                    # Line 2: "blue cube killed: X"
                    blue_line = lines[1].strip()
                    if ":" in blue_line:
                        stats['blue_kills'] = int(blue_line.split(':')[1].strip())
        except (IOError, ValueError) as e:
            # If there's an error reading/parsing, we use the default 0s
            print(f"Error loading stats file, using defaults: {e}")
    return stats

def save_stats(stats):
    """Writes kill counts to stats.txt in the required format."""
    try:
        with open(STATS_FILE, 'w') as f:
            f.write(f"red cube killed: {stats['red_kills']}\n")
            f.write(f"blue cube killed: {stats['blue_kills']}\n")
    except IOError as e:
        print(f"Error saving stats file: {e}")

# Load stats on game start
cube_stats = load_stats()

def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

def get_red_cube_color(state):
    """
    Determines the color of the Red Cube based on its charge and special attack states.
    """

    if state['ai_attack_state'] == 'SpecialWindup':

        if state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2): 
            return CYAN

        if state['flash_count'] % 2 != 0: 
             return BLACK
        return RED 

    if state['charge_state'] == 'Endlag':
        return BLACK

    if state['charge_state'] == 'Windup':

        if state['flash_count'] % 2 != 0: 
             return BLACK
        return RED 

    return RED

def get_blue_cube_color(state):
    """
    Determines the color of the Blue Cube based on its parry state.
    """
    if state['parry_active']:
        return BLACK
    return BLUE

def draw_health_bars():

    blue_health_ratio = max(0, game_state['blue_health'] / 100)
    red_health_ratio = max(0, game_state['red_health'] / 100)

    MAX_BAR_WIDTH = 200

    blue_bar_width = int(MAX_BAR_WIDTH * blue_health_ratio)
    red_bar_width = int(MAX_BAR_WIDTH * red_health_ratio)

    # Health bar positions are swapped from the original, assuming blue is player (left) and red is AI (right)
    # Reverting to the original file's logic: Red bar is on the left, Blue bar is on the right
    blue_health_rect = pygame.Rect(WIDTH - MAX_BAR_WIDTH - 10, 10, blue_bar_width, 20)
    red_health_rect = pygame.Rect(10, 10, red_bar_width, 20)

    # Draw the background/outline
    pygame.draw.rect(screen, (100, 100, 100), (WIDTH - MAX_BAR_WIDTH - 10, 10, MAX_BAR_WIDTH, 20), 1)
    pygame.draw.rect(screen, (100, 100, 100), (10, 10, MAX_BAR_WIDTH, 20), 1)

    # Draw the filled health
    pygame.draw.rect(screen, BLUE, blue_health_rect)
    pygame.draw.rect(screen, RED, red_health_rect)

    # Health text
    blue_health_text = font.render(f"Blue: {max(0, game_state['blue_health'])}", True, WHITE)
    red_health_text = font.render(f"Red: {max(0, game_state['red_health'])}", True, WHITE)

    screen.blit(blue_health_text, (WIDTH - MAX_BAR_WIDTH - 10, 35))
    screen.blit(red_health_text, (10, 35))
    
    # NEW: Kill Stats Display
    red_kills_text = font.render(f"Red Kills: {cube_stats['red_kills']}", True, RED)
    blue_kills_text = font.render(f"Blue Kills: {cube_stats['blue_kills']}", True, BLUE)
    screen.blit(red_kills_text, (10, HEIGHT - 40))
    screen.blit(blue_kills_text, (WIDTH - 150, HEIGHT - 40))


def calculate_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between the centers of two cubes."""
    center1_x, center1_y = x1 + CUBE_SIZE / 2, y1 + CUBE_SIZE / 2
    center2_x, center2_y = x2 + CUBE_SIZE / 2, y2 + CUBE_SIZE / 2
    return math.hypot(center2_x - center1_x, center2_y - center1_y)

def move_ai(mode, target_x, target_y, current_x, current_y, speed, red_health):
    """Calculates the new position based on the standard AI modes."""
    dx, dy = 0, 0
    distance = calculate_distance(current_x, current_y, target_x, target_y)

    # Only calculate next mode if mode is NOT manually set 
    if mode not in ["Parried (Stun)", "Charge (Endlag)", "Charge (Windup)", "Charge", "Beam (Windup)"]:

        if red_health <= RETREAT_HEALTH_THRESHOLD and distance > MAINTAIN_RANGE_MAX:
            mode = "Defensive Retreat"
        elif distance < ATTACK_RANGE:
            mode = "Attack"
        elif distance > MAINTAIN_RANGE_MAX:
            mode = "Close Gap"
        elif distance < MAINTAIN_RANGE_MIN:
            mode = "Back Off"
        else:
            mode = "Maintain"

    if mode == "Attack" or mode == "Close Gap":

        dx = target_x - current_x
        dy = target_y - current_y

    elif mode == "Defensive Retreat" or mode == "Back Off":

        dx = current_x - target_x
        dy = current_y - target_y

    elif mode == "Maintain":

        dx, dy = 0, 0

    move_x, move_y = 0, 0
    if dx != 0 or dy != 0:
        angle = math.atan2(dy, dx)
        move_x = speed * math.cos(angle)
        move_y = speed * math.sin(angle)

        if abs(move_x) > abs(move_y):
            game_state['ai_last_direction'] = 'right' if move_x > 0 else 'left'
        elif abs(move_y) > 0:
            game_state['ai_last_direction'] = 'down' if move_y > 0 else 'up'

    move_x += random.uniform(-1, 1) * 0.5
    move_y += random.uniform(-1, 1) * 0.5
    
    # Only apply movement if the mode allows it
    if mode in ["Attack", "Close Gap", "Defensive Retreat", "Back Off"]:
        new_x = max(0, min(current_x + move_x, WIDTH - CUBE_SIZE))
        new_y = max(0, min(current_y + move_y, HEIGHT - CUBE_SIZE))
    else:
        new_x = current_x
        new_y = current_y

    return new_x, new_y, mode

def check_hitbox_collision(hitbox_rect, target_x, target_y):
    """Checks if the target cube is inside the generated hitbox."""
    if not hitbox_rect:
        return False

    target_rect = pygame.Rect(target_x, target_y, CUBE_SIZE, CUBE_SIZE)

    return hitbox_rect.colliderect(target_rect)

def do_special_attack():
    """Triggers the blue cube's special purple hitbox attack."""

    # NEW: Check for debug mode - ignore cooldown if active
    if not is_debug_mode and game_state['special_attack_cooldown_timer'] > 0:
        return 

    blue_x, blue_y = game_state['blue_x'], game_state['blue_y']
    direction = game_state['last_direction']

    offset = CUBE_SIZE 
    hitbox_x, hitbox_y = blue_x, blue_y

    if direction == 'right':
        hitbox_x = blue_x + offset
    elif direction == 'left':
        hitbox_x = blue_x - offset
    elif direction == 'up':
        hitbox_y = blue_y - offset
    elif direction == 'down':
        hitbox_y = blue_y + offset
    else: 
        return 

    hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, CUBE_SIZE, CUBE_SIZE)

    if game_state['red_active'] and check_hitbox_collision(hitbox_rect, game_state['red_x'], game_state['red_y']):
        game_state['red_health'] -= SPECIAL_ATTACK_DAMAGE
        print(f"Blue Cube Slash hit! Damage: {SPECIAL_ATTACK_DAMAGE}. Red Health: {max(0, game_state['red_health'])}")

    game_state['purple_hitbox_active'] = True
    game_state['purple_hitbox_rect'] = hitbox_rect
    game_state['hitbox_timer'] = HITBOX_DURATION_MS

    # Only set cooldown if debug mode is OFF
    if not is_debug_mode:
        game_state['special_attack_cooldown_timer'] = SPECIAL_ATTACK_COOLDOWN_MS
    else:
        game_state['special_attack_cooldown_timer'] = 1 # Set to a non-zero, non-blocking value for debug

def initiate_parry():
    """
    Initiates the Blue Cube's parry.
    """
    if not game_state['blue_active'] or game_state['game_over']:
        return

    charge_windup_success = (
        game_state['charge_state'] == 'Windup' and 
        game_state['flash_count'] == (CHARGE_FLASH_CYCLES * 2) and # Final black flash count
        game_state['flash_timer'] > 0 # Currently in the final flash duration
    )

    special_windup_success = (
        game_state['ai_attack_state'] == 'SpecialWindup' and
        game_state['flash_count'] == (AI_SLASH_FLASH_CYCLES * 2) and # Final black flash count
        game_state['flash_timer'] > 0 # Currently in the final flash duration
    )

    # SUCCESSFUL PARRY
    if charge_windup_success or special_windup_success:
        print("Successful Parry! Red Cube stunned.")

        game_state['charge_state'] = 'Endlag'
        game_state['endlag_timer'] = ENDLAG_DURATION_MS * 2
        game_state['red_cube_mode'] = "Parried (Stun)"

        game_state['ai_attack_state'] = 'Idle'
        game_state['flash_count'] = 0
        game_state['flash_timer'] = 0

        game_state['parry_active'] = True
        game_state['parry_timer'] = PARRY_WINDOW_DURATION_MS 

    # FAILED PARRY
    else:
        print("Parry Attempt: Missed timing or no active windup.")
        game_state['parry_active'] = True
        game_state['parry_timer'] = PARRY_WINDOW_DURATION_MS // 2 

def check_ai_special_attack_trigger(distance_to_player):
    """Determines if the AI should try to use its special attack (Beam)."""

    if (game_state['ai_special_attack_cooldown_timer'] == 0 and
        game_state['charge_state'] == 'Idle' and
        game_state['ai_attack_state'] == 'Idle' and 
        distance_to_player < AI_SPECIAL_ATTACK_RANGE):

        if random.random() < 0.05:
            return True
    return False

def initiate_ai_special_attack_windup():
    """Transitions the AI into the Special Windup state (always leads to Beam)."""

    game_state['ai_attack_state'] = 'SpecialWindup' 
    game_state['flash_count'] = 0

    game_state['flash_timer'] = AI_FLASH_DURATION_MS 
    game_state['red_cube_mode'] = "Beam (Windup)" 

    target_x, target_y = game_state['blue_x'], game_state['blue_y']
    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2

    dx = target_x + CUBE_SIZE / 2 - red_center_x
    dy = target_y + CUBE_SIZE / 2 - red_center_y

    game_state['ai_beam_angle'] = math.atan2(dy, dx)

def get_ai_beam_rect():
    """
    Calculates the beam rectangle centered on the Red Cube and rotated towards the angle.
    Returns: A tuple (surface, rect) suitable for screen.blit()
    """
    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2

    angle_deg = math.degrees(game_state['ai_beam_angle'])

    surface_size = max(AI_BEAM_LENGTH, AI_BEAM_WIDTH) + 10 
    beam_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

    origin_offset = CUBE_SIZE / 2 
    unrotated_beam_rect = pygame.Rect(surface_size // 2 + origin_offset, surface_size // 2 - AI_BEAM_WIDTH // 2, AI_BEAM_LENGTH - origin_offset, AI_BEAM_WIDTH)
    pygame.draw.rect(beam_surface, CYAN, unrotated_beam_rect)

    rotated_surface = pygame.transform.rotate(beam_surface, -angle_deg)

    rotated_rect = rotated_surface.get_rect(center=(red_center_x, red_center_y))

    return rotated_surface, rotated_rect

def execute_ai_special_attack():
    """
    Triggers the beam attack. Handles visual display and collision check.
    """

    game_state['ai_cyan_beam_active'] = True
    game_state['ai_hitbox_timer'] = AI_SPECIAL_HITBOX_DURATION_MS

    angle = game_state['ai_beam_angle']

    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2

    beam_end_x = red_center_x + AI_BEAM_LENGTH * math.cos(angle)
    beam_end_y = red_center_y + AI_BEAM_LENGTH * math.sin(angle)

    x_min = min(red_center_x, beam_end_x) - CUBE_SIZE 
    x_max = max(red_center_x, beam_end_x) + CUBE_SIZE
    y_min = min(red_center_y, beam_end_y) - CUBE_SIZE
    y_max = max(red_center_y, beam_end_y) + CUBE_SIZE

    beam_bounding_rect = pygame.Rect(x_min, y_min, x_max - x_min, y_max - y_min)

    blue_cube_rect = pygame.Rect(game_state['blue_x'], game_state['blue_y'], CUBE_SIZE, CUBE_SIZE)

    if game_state['blue_active'] and beam_bounding_rect.colliderect(blue_cube_rect):
        # NEW: Check for debug mode - take no damage if active
        if not is_debug_mode:
            game_state['blue_health'] -= AI_SPECIAL_ATTACK_DAMAGE
            print(f"Red Cube Beam hit! Damage: {AI_SPECIAL_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")
        else:
            print("Red Cube Beam hit! (Debug Invincible)")


    game_state['ai_special_attack_cooldown_timer'] = AI_SPECIAL_ATTACK_COOLDOWN_MS

    game_state['ai_attack_state'] = 'Idle'
    game_state['red_cube_mode'] = "Maintain" 

def reset_game_state(keep_stats=True):
    """
    Resets all game variables to their initial state.
    If keep_stats is False, kill counts are also reset (e.g., on initial load).
    """

    global game_state

    # Don't reset kill stats unless explicitly told not to (only on initial load in a real game)
    if not keep_stats:
        global cube_stats
        cube_stats = {'red_kills': 0, 'blue_kills': 0}
        save_stats(cube_stats)


    game_state['blue_active'] = INITIAL_BLUE_ACTIVE
    game_state['red_active'] = INITIAL_RED_ACTIVE
    game_state['blue_health'] = INITIAL_BLUE_HEALTH
    game_state['red_health'] = INITIAL_RED_HEALTH
    game_state['blue_x'] = blue_x
    game_state['blue_y'] = blue_y
    game_state['red_x'] = red_x
    game_state['red_y'] = red_y
    game_state['game_over'] = False
    game_state['red_cube_mode'] = INITIAL_RED_CUBE_MODE

    game_state['charge_state'] = 'Idle'
    game_state['flash_timer'] = 0
    game_state['flash_count'] = 0
    game_state['endlag_timer'] = 0.0

    game_state['purple_hitbox_active'] = False
    game_state['purple_hitbox_rect'] = None
    game_state['hitbox_timer'] = 0
    game_state['special_attack_cooldown_timer'] = 0 
    game_state['last_direction'] = 'right'

    game_state['ai_cyan_beam_active'] = False 
    game_state['ai_beam_angle'] = 0.0         
    game_state['ai_hitbox_timer'] = 0
    game_state['ai_special_attack_cooldown_timer'] = 0
    game_state['ai_last_direction'] = 'left'
    game_state['ai_attack_state'] = 'Idle' 
    
    game_state['parry_active'] = False
    game_state['parry_timer'] = 0.0
    
    print("Game state reset.")

def check_debug_file():
    """Reads the debug.txt file and updates the global debug flag."""
    global is_debug_mode
    try:
        if os.path.exists(DEBUG_FILE):
            with open(DEBUG_FILE, 'r') as f:
                content = f.readline().strip().lower()
                is_debug_mode_new = content == "debug = true"
                if is_debug_mode_new != is_debug_mode:
                    is_debug_mode = is_debug_mode_new
                    print(f"Debug Mode Toggled: {is_debug_mode}")
                return is_debug_mode
        else:
            if is_debug_mode:
                is_debug_mode = False
                print("Debug Mode Toggled: False (File removed)")
            return False
    except Exception as e:
        if is_debug_mode:
            is_debug_mode = False
            print(f"Error reading debug file, disabling debug: {e}")
        return False


# --- Main Game Loop ---

running = True
clock = pygame.time.Clock()

while running:

    dt = clock.tick(60) 

    # NEW: Check the debug file at the start of every frame
    is_debug_mode = check_debug_file() 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and game_state['blue_active'] and not game_state['game_over']:
            if event.key == pygame.K_SPACE:
                do_special_attack()
            if event.key == pygame.K_f:
                initiate_parry()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_state['game_over']:
            print("Restarting Game...")
            reset_game_state()

    # REMOVED: root.update() and all CTk related code

    if game_state['game_over']:

        screen.fill(WHITE)
        draw_health_bars()

        if game_state['blue_health'] <= 0:
            message = "Red Cube Wins! Press R to Restart"
            color = RED
        else:
            message = "Blue Cube Wins! Press R to Restart"
            color = BLUE

        game_over_text = font.render(message, True, color)
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
        pygame.display.flip()
        continue 

    keys = pygame.key.get_pressed()
    current_move_speed = game_state.get('move_speed', MOVE_SPEED)

    # --- Blue Cube Movement and Timers ---
    if game_state['blue_active']:

        dx, dy = 0, 0

        if keys[pygame.K_LEFT]:
            dx -= current_move_speed
            game_state['last_direction'] = 'left' 
        if keys[pygame.K_RIGHT]:
            dx += current_move_speed
            game_state['last_direction'] = 'right' 

        if keys[pygame.K_UP]:
            dy -= current_move_speed
            game_state['last_direction'] = 'up'
        if keys[pygame.K_DOWN]:
            dy += current_move_speed
            game_state['last_direction'] = 'down'

        game_state['blue_x'] += dx
        game_state['blue_y'] += dy

        game_state['blue_x'] = max(0, min(game_state['blue_x'], WIDTH - CUBE_SIZE))
        game_state['blue_y'] = max(0, min(game_state['blue_y'], HEIGHT - CUBE_SIZE))

    if game_state.get('parry_active', False):
        game_state['parry_timer'] -= dt
        if game_state['parry_timer'] <= 0:
            game_state['parry_active'] = False
            game_state['parry_timer'] = 0.0

    if game_state['purple_hitbox_active']:
        game_state['hitbox_timer'] -= dt
        if game_state['hitbox_timer'] <= 0:
            game_state['purple_hitbox_active'] = False
            game_state['purple_hitbox_rect'] = None

    # NEW: Cooldown timer handling is modified for debug mode
    if game_state['special_attack_cooldown_timer'] > 0:
        if not is_debug_mode:
            game_state['special_attack_cooldown_timer'] -= dt
        else:
            # If debug, ensure the timer is practically zero but non-zero to satisfy the check in do_special_attack
            game_state['special_attack_cooldown_timer'] = 1 
            
        if game_state['special_attack_cooldown_timer'] < 0:
            game_state['special_attack_cooldown_timer'] = 0

    # --- AI Timers ---
    if game_state['ai_cyan_beam_active']:
        game_state['ai_hitbox_timer'] -= dt

        if game_state['ai_hitbox_timer'] > 0:
            # Beam continues to track the player during the active hitbox duration
            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            red_center_x = game_state['red_x'] + CUBE_SIZE / 2
            red_center_y = game_state['red_y'] + CUBE_SIZE / 2
            dx = target_x + CUBE_SIZE / 2 - red_center_x
            dy = target_y + CUBE_SIZE / 2 - red_center_y
            target_angle = math.atan2(dy, dx)
            game_state['ai_beam_angle'] = target_angle
        else:
            game_state['ai_cyan_beam_active'] = False
            game_state['ai_beam_angle'] = 0.0

    if game_state['ai_special_attack_cooldown_timer'] > 0:
        game_state['ai_special_attack_cooldown_timer'] -= dt
        if game_state['ai_special_attack_cooldown_timer'] < 0:
            game_state['ai_special_attack_cooldown_timer'] = 0

    # --- AI Logic (Red Cube) ---
    if game_state['red_active']:

        target_x, target_y = game_state['blue_x'], game_state['blue_y']
        distance_to_player = calculate_distance(game_state['red_x'], game_state['red_y'], target_x, target_y)

        ai_is_stuck = game_state['red_cube_mode'] in ["Parried (Stun)", "Charge (Endlag)", "Charge (Windup)", "Beam (Windup)"]

        if game_state['ai_attack_state'] == 'Idle' and not ai_is_stuck:

            if check_ai_special_attack_trigger(distance_to_player) and game_state['charge_state'] == 'Idle':
                initiate_ai_special_attack_windup()

        elif game_state['ai_attack_state'] == 'SpecialWindup' and not ai_is_stuck: 
            game_state['flash_timer'] -= dt

            if game_state['flash_timer'] <= 0:
                game_state['flash_count'] += 1

                if game_state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2) + 1:
                    execute_ai_special_attack()
                else:
                    game_state['flash_timer'] = AI_FLASH_DURATION_MS

            # Track player during windup
            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            red_center_x = game_state['red_x'] + CUBE_SIZE / 2
            red_center_y = game_state['red_y'] + CUBE_SIZE / 2
            dx = target_x + CUBE_SIZE / 2 - red_center_x
            dy = target_y + CUBE_SIZE / 2 - red_center_y
            game_state['ai_beam_angle'] = math.atan2(dy, dx) 

            game_state['red_cube_mode'] = "Beam (Windup)" 

        if game_state['ai_attack_state'] == 'Idle' and not ai_is_stuck:

            if game_state['charge_state'] == 'Idle':

                if random.random() < CHARGE_INITIATE_CHANCE:
                    game_state['charge_state'] = 'Windup'
                    game_state['flash_count'] = 0

                    game_state['flash_timer'] = FLASH_DURATION_MS 

                    dx = target_x - game_state['red_x']
                    dy = target_y - game_state['red_y']
                    angle = math.atan2(dy, dx)
                    game_state['charge_dx'] = math.cos(angle)
                    game_state['charge_dy'] = math.sin(angle)

                    game_state['red_cube_mode'] = "Charge (Windup)" 

                else:
                    new_red_x, new_red_y, new_mode = move_ai(
                        game_state['red_cube_mode'], 
                        target_x, 
                        target_y, 
                        game_state['red_x'], 
                        game_state['red_y'], 
                        AI_MOVE_SPEED,
                        game_state['red_health']
                    )
                    game_state['red_x'] = new_red_x
                    game_state['red_y'] = new_red_y
                    
                    if game_state['red_cube_mode'] != new_mode:
                        game_state['red_cube_mode'] = new_mode
                        

            elif game_state['charge_state'] == 'Windup':
                game_state['flash_timer'] -= dt

                if game_state['flash_timer'] <= 0:
                    game_state['flash_count'] += 1

                    if game_state['flash_count'] > (CHARGE_FLASH_CYCLES * 2):
                        game_state['charge_state'] = 'Charging'
                        game_state['red_cube_mode'] = "Charge"
                    else:
                        game_state['flash_timer'] = FLASH_DURATION_MS

                game_state['red_cube_mode'] = "Charge (Windup)"

            elif game_state['charge_state'] == 'Charging':
                game_state['red_cube_mode'] = "Charge"

                move_x = game_state['charge_dx'] * CHARGE_SPEED
                move_y = game_state['charge_dy'] * CHARGE_SPEED

                new_x = game_state['red_x'] + move_x
                new_y = game_state['red_y'] + move_y

                hit_boundary = False

                if new_x <= 0 or new_x >= WIDTH - CUBE_SIZE:
                    hit_boundary = True
                    new_x = max(0, min(new_x, WIDTH - CUBE_SIZE))

                if new_y <= 0 or new_y >= HEIGHT - CUBE_SIZE:
                    hit_boundary = True
                    new_y = max(0, min(new_y, HEIGHT - CUBE_SIZE))

                game_state['red_x'] = new_x
                game_state['red_y'] = new_y

                if hit_boundary:
                    game_state['charge_state'] = 'Endlag' 
                    game_state['endlag_timer'] = ENDLAG_DURATION_MS 
                    game_state['red_cube_mode'] = "Charge (Endlag)"

            elif game_state['charge_state'] == 'Endlag':
                game_state['endlag_timer'] -= dt 

                if game_state['endlag_timer'] <= 0:
                    game_state['charge_state'] = 'Idle'
                    game_state['red_cube_mode'] = "Maintain"
                else:
                    game_state['red_cube_mode'] = "Charge (Endlag)"

    # --- Collision Check (Red Cube Charge) ---
    is_charging = game_state['charge_state'] == 'Charging'

    if is_charging:

        if (game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
            game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
            game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
            game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):

            if game_state['blue_active'] and game_state['blue_health'] > 0:
                # NEW: Check for debug mode - take no damage if active
                if not is_debug_mode:
                    game_state['blue_health'] -= CHARGE_ATTACK_DAMAGE 
                    print(f"Red Cube Charge hit! Damage: {CHARGE_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")
                else:
                    print("Red Cube Charge hit! (Debug Invincible)")


    # --- Win Condition and Debug Respawn ---
    if game_state['blue_health'] <= 0:
        if game_state['blue_active']:
            print("Blue Cube Defeated!")
            # Blue Cube is defeated, Red Cube wins
            cube_stats['red_kills'] += 1
            save_stats(cube_stats)
        game_state['blue_active'] = False
        game_state['game_over'] = True

    if game_state['red_health'] <= 0:
        if game_state['red_active']:
            print("Red Cube Defeated!")
            # Red Cube is defeated, Blue Cube wins
            cube_stats['blue_kills'] += 1
            save_stats(cube_stats)
            
            # NEW: Red Cube Respawn in debug mode
            if is_debug_mode:
                print("Debug Mode: Red Cube Respawning...")
                # Reset only the Red Cube's state, but keep player health/position
                game_state['red_active'] = INITIAL_RED_ACTIVE
                game_state['red_health'] = INITIAL_RED_HEALTH
                game_state['red_x'] = red_x
                game_state['red_y'] = red_y
                game_state['red_cube_mode'] = INITIAL_RED_CUBE_MODE
                game_state['charge_state'] = 'Idle'
                game_state['ai_attack_state'] = 'Idle'
                game_state['ai_special_attack_cooldown_timer'] = 0
            else:
                game_state['red_active'] = False
                game_state['game_over'] = True


    # --- Drawing ---
    screen.fill(WHITE)

    blue_cube_color = get_blue_cube_color(game_state)
    draw_cube(game_state['blue_x'], game_state['blue_y'], blue_cube_color)
    
    draw_health_bars()

    if game_state['purple_hitbox_active'] and game_state['purple_hitbox_rect']:
        pygame.draw.rect(screen, PURPLE_TUPLE, game_state['purple_hitbox_rect'])

    if game_state['ai_cyan_beam_active']:
        beam_surface, beam_rect = get_ai_beam_rect()
        screen.blit(beam_surface, beam_rect)

    if game_state['red_active']:

        red_cube_color = get_red_cube_color(game_state)
        draw_cube(game_state['red_x'], game_state['red_y'], red_cube_color)

    pygame.display.flip()

pygame.quit()
sys.exit()