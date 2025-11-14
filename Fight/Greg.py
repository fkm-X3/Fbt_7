import pygame
import random
import customtkinter as ctk
import sys
import math
import os # NEW: Required for file existence check

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cube Combat")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0) 
WHITE = (255, 255, 255)
CYAN = (0, 255, 255) 

PURPLE_TUPLE = (128, 0, 128) 
PURPLE_HEX = "#800080"      

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
}

game_state = initial_game_state.copy()

STATS_FILE = "stats.txt" # Constant for the stats file

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

def draw_health_bars():

    blue_health_ratio = max(0, game_state['blue_health'] / 100)
    red_health_ratio = max(0, game_state['red_health'] / 100)

    MAX_BAR_WIDTH = 200

    blue_bar_width = int(MAX_BAR_WIDTH * blue_health_ratio)
    red_bar_width = int(MAX_BAR_WIDTH * red_health_ratio)

    blue_health_rect = pygame.Rect(WIDTH - MAX_BAR_WIDTH - 10, 10, blue_bar_width, 20)

    red_health_rect = pygame.Rect(10, 10, red_bar_width, 20)

    pygame.draw.rect(screen, (100, 100, 100), (WIDTH - MAX_BAR_WIDTH - 10, 10, MAX_BAR_WIDTH, 20), 1)
    pygame.draw.rect(screen, (100, 100, 100), (10, 10, MAX_BAR_WIDTH, 20), 1)

    pygame.draw.rect(screen, BLUE, blue_health_rect)
    pygame.draw.rect(screen, RED, red_health_rect)

    blue_health_text = font.render(f"Blue: {max(0, game_state['blue_health'])}", True, WHITE)
    red_health_text = font.render(f"Red: {max(0, game_state['red_health'])}", True, WHITE)

    screen.blit(blue_health_text, (WIDTH - MAX_BAR_WIDTH - 10, 35))
    screen.blit(red_health_text, (10, 35))

def calculate_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between the centers of two cubes."""
    center1_x, center1_y = x1 + CUBE_SIZE / 2, y1 + CUBE_SIZE / 2
    center2_x, center2_y = x2 + CUBE_SIZE / 2, y2 + CUBE_SIZE / 2
    return math.hypot(center2_x - center1_x, center2_y - center1_y)

def move_ai(mode, target_x, target_y, current_x, current_y, speed, red_health):
    """Calculates the new position based on the standard AI modes."""
    dx, dy = 0, 0
    distance = calculate_distance(current_x, current_y, target_x, target_y)

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

    new_x = max(0, min(current_x + move_x, WIDTH - CUBE_SIZE))
    new_y = max(0, min(current_y + move_y, HEIGHT - CUBE_SIZE))

    return new_x, new_y, mode

def check_hitbox_collision(hitbox_rect, target_x, target_y):
    """Checks if the target cube is inside the generated hitbox."""
    if not hitbox_rect:
        return False

    target_rect = pygame.Rect(target_x, target_y, CUBE_SIZE, CUBE_SIZE)

    return hitbox_rect.colliderect(target_rect)

def do_special_attack():
    """Triggers the blue cube's special purple hitbox attack."""

    if game_state['special_attack_cooldown_timer'] > 0:
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

    game_state['special_attack_cooldown_timer'] = SPECIAL_ATTACK_COOLDOWN_MS

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
    Triggers the beam attack (now the only special attack). Handles visual display and collision check.
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
        game_state['blue_health'] -= AI_SPECIAL_ATTACK_DAMAGE
        print(f"Red Cube Beam hit! Damage: {AI_SPECIAL_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")

    game_state['ai_special_attack_cooldown_timer'] = AI_SPECIAL_ATTACK_COOLDOWN_MS

    game_state['ai_attack_state'] = 'Idle'
    game_state['red_cube_mode'] = "Maintain" 

root = ctk.CTk()
root.title("Cube Combat Control Panel")

# Set fixed size for the CTk window and prevent resizing
root.geometry("300x500")
root.resizable(False, False)

tk_mode_text = ctk.StringVar(value=f"Red Cube Mode: {game_state['red_cube_mode']}")
tk_cooldown_text = ctk.StringVar(value="Slash: READY (SPACE)")
tk_red_health = ctk.StringVar(value=f"Red Health: {game_state['red_health']}")
tk_blue_pos = ctk.StringVar(value=f"Blue Pos: ({game_state['blue_x']:.0f}, {game_state['blue_y']:.0f})")
tk_red_pos = ctk.StringVar(value=f"Red Pos: ({game_state['red_x']:.0f}, {game_state['red_y']:.0f})")

# NEW: Stat variables for display
tk_red_kills = ctk.StringVar(value=f"Red Kills: {cube_stats['red_kills']}")
tk_blue_kills = ctk.StringVar(value=f"Blue Kills: {cube_stats['blue_kills']}")

control_panel_frame = ctk.CTkFrame(root)
control_panel_frame.pack(padx=10, pady=10)

def toggle_blue_active():
    game_state['blue_active'] = not game_state['blue_active']
    if game_state['blue_active']:
        blue_button.configure(text="Blue Active (ON)", fg_color="green")
    else:
        blue_button.configure(text="Blue Active (OFF)", fg_color="red")
    print(f"Blue Active: {game_state['blue_active']}")

def increase_attack():
    game_state['attack_damage'] = game_state.get('attack_damage', ATTACK_DAMAGE) + 5
    print(f"Attack Damage: {game_state['attack_damage']}")

def decrease_speed():
    game_state['move_speed'] = max(1, game_state.get('move_speed', MOVE_SPEED) - 1)
    print(f"Move Speed: {game_state['move_speed']}")

def reset_positions():
    game_state['blue_x'] = blue_x
    game_state['blue_y'] = blue_y
    game_state['red_x'] = red_x
    game_state['red_y'] = red_y
    print("Cube positions reset.")

def force_endlag():
    if game_state['charge_state'] != 'Endlag':
        game_state['charge_state'] = 'Endlag'
        game_state['endlag_timer'] = ENDLAG_DURATION_MS 
        game_state['red_cube_mode'] = "Charge (Endlag)" 
        print("Forced Red Cube into Endlag.")

def reset_game_state():
    """Resets all game variables to their initial state."""

    global game_state

    # Note: Kill stats are NOT reset here, they are persistent
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

    tk_mode_text.set(f"Red Cube Mode: {game_state['red_cube_mode']}")
    blue_button.configure(
        text=f"Blue Active ({'ON' if game_state['blue_active'] else 'OFF'})", 
        fg_color="green" if game_state['blue_active'] else "red"
    )

blue_button = ctk.CTkButton(
    control_panel_frame, 
    text=f"Blue Active ({'ON' if game_state['blue_active'] else 'OFF'})", 
    command=toggle_blue_active,
    fg_color="green" if game_state['blue_active'] else "red"
)
blue_button.pack(fill='x', pady=5, padx=10)

attack_button = ctk.CTkButton(
    control_panel_frame, 
    text="Increase Attack Damage (+5)", 
    command=increase_attack
)
attack_button.pack(fill='x', pady=5, padx=10)

speed_button = ctk.CTkButton(
    control_panel_frame, 
    text="Decrease Move Speed (-1)", 
    command=decrease_speed
)
speed_button.pack(fill='x', pady=5, padx=10)

reset_pos_button = ctk.CTkButton(
    control_panel_frame, 
    text="Reset Cube Positions", 
    command=reset_positions,
    fg_color="gray"
)
reset_pos_button.pack(fill='x', pady=5, padx=10)

endlag_button = ctk.CTkButton(
    control_panel_frame, 
    text="Force Red Cube Endlag", 
    command=force_endlag,
    fg_color="orange"
)
endlag_button.pack(fill='x', pady=5, padx=10)

status_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_mode_text, 
    fg_color="yellow", 
    text_color='black', 
    font=ctk.CTkFont(family='Arial', size=14, weight='bold'),
    corner_radius=6
)
status_label.pack(fill='x', pady=(10, 5), padx=10)

cooldown_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_cooldown_text, 
    fg_color="green", 
    text_color='white', 
    font=ctk.CTkFont(family='Arial', size=12, weight='bold'),
    corner_radius=6
)
cooldown_label.pack(fill='x', pady=(5, 10), padx=10)

red_health_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_red_health, 
    text_color='red', 
    corner_radius=6
)
red_health_label.pack(fill='x', pady=(5, 0), padx=10)

blue_pos_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_blue_pos, 
    text_color='blue', 
    corner_radius=6
)
blue_pos_label.pack(fill='x', pady=0, padx=10)

red_pos_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_red_pos, 
    text_color='red', 
    corner_radius=6
)
red_pos_label.pack(fill='x', pady=0, padx=10) # Removed bottom padding to add new labels

# NEW: Kill Stats Display
red_kills_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_red_kills, 
    text_color='red', 
    corner_radius=6
)
red_kills_label.pack(fill='x', pady=(5, 0), padx=10)

blue_kills_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_blue_kills, 
    text_color='blue', 
    corner_radius=6
)
blue_kills_label.pack(fill='x', pady=(0, 10), padx=10) # Added bottom padding here

running = True
clock = pygame.time.Clock()

while running:

    dt = clock.tick(60) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_state['blue_active'] and not game_state['game_over']:
            do_special_attack()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_state['game_over']:
            print("Restarting Game...")
            reset_game_state()

    try:
        # Re-apply the geometry setting in case other code tried to change it (though it shouldn't)
        # This is here for robustness, but `root.resizable(False, False)` is the primary fix.
        # root.geometry("300x500") 
        root.update()
    except Exception as e:
        running = False
        break

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

    if game_state['purple_hitbox_active']:
        game_state['hitbox_timer'] -= dt
        if game_state['hitbox_timer'] <= 0:
            game_state['purple_hitbox_active'] = False
            game_state['purple_hitbox_rect'] = None

    if game_state['special_attack_cooldown_timer'] > 0:
        game_state['special_attack_cooldown_timer'] -= dt
        if game_state['special_attack_cooldown_timer'] < 0:
            game_state['special_attack_cooldown_timer'] = 0

    if game_state['ai_cyan_beam_active']:
        game_state['ai_hitbox_timer'] -= dt

        if game_state['ai_hitbox_timer'] > 0:
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

    cooldown_time_s = game_state['special_attack_cooldown_timer'] / 1000

    if cooldown_time_s > 0:
        tk_cooldown_text.set(f"Slash: {cooldown_time_s:.1f}s CD")
        cooldown_label.configure(fg_color=PURPLE_HEX, text_color="white") 
    else:
        tk_cooldown_text.set("Slash: READY (SPACE)")
        cooldown_label.configure(fg_color="green", text_color="white") 

    if game_state['red_active']:

        target_x, target_y = game_state['blue_x'], game_state['blue_y']
        distance_to_player = calculate_distance(game_state['red_x'], game_state['red_y'], target_x, target_y)

        if game_state['ai_attack_state'] == 'Idle':

            if check_ai_special_attack_trigger(distance_to_player) and game_state['charge_state'] == 'Idle':
                initiate_ai_special_attack_windup()

        elif game_state['ai_attack_state'] == 'SpecialWindup': 

            game_state['flash_timer'] -= dt

            if game_state['flash_timer'] <= 0:
                game_state['flash_count'] += 1

                if game_state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2) + 1:

                    execute_ai_special_attack()
                else:

                    game_state['flash_timer'] = AI_FLASH_DURATION_MS

            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            red_center_x = game_state['red_x'] + CUBE_SIZE / 2
            red_center_y = game_state['red_y'] + CUBE_SIZE / 2
            dx = target_x + CUBE_SIZE / 2 - red_center_x
            dy = target_y + CUBE_SIZE / 2 - red_center_y
            game_state['ai_beam_angle'] = math.atan2(dy, dx) 

            game_state['red_cube_mode'] = "Beam (Windup)" 

        if game_state['ai_attack_state'] == 'Idle':

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
                    game_state['red_cube_mode'] = new_mode

            elif game_state['charge_state'] == 'Windup':

                game_state['flash_timer'] -= dt

                if game_state['flash_timer'] <= 0:
                    game_state['flash_count'] += 1

                    if game_state['flash_count'] > (CHARGE_FLASH_CYCLES * 2):
                        game_state['charge_state'] = 'Charging'
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

    tk_mode_text.set(f"Red Cube Mode: {game_state['red_cube_mode']}")
    tk_red_health.set(f"Red Health: {max(0, game_state['red_health'])}")
    tk_blue_pos.set(f"Blue Pos: ({game_state['blue_x']:.0f}, {game_state['blue_y']:.0f})")
    tk_red_pos.set(f"Red Pos: ({game_state['red_x']:.0f}, {game_state['red_y']:.0f})")

    is_charging = game_state['charge_state'] == 'Charging'

    if is_charging:

        if (game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
            game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
            game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
            game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):

            if game_state['blue_active'] and game_state['blue_health'] > 0:
                game_state['blue_health'] -= CHARGE_ATTACK_DAMAGE 
                print(f"Red Cube Charge hit! Damage: {CHARGE_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")

    if game_state['blue_health'] <= 0:
        if game_state['blue_active']:
            print("Blue Cube Defeated!")
            # NEW: Blue Cube is defeated, Red Cube wins
            cube_stats['red_kills'] += 1
            save_stats(cube_stats)
            tk_red_kills.set(f"Red Kills: {cube_stats['red_kills']}")
        game_state['blue_active'] = False
        game_state['game_over'] = True

    if game_state['red_health'] <= 0:
        if game_state['red_active']:
            print("Red Cube Defeated!")
            # NEW: Red Cube is defeated, Blue Cube wins
            cube_stats['blue_kills'] += 1
            save_stats(cube_stats)
            tk_blue_kills.set(f"Blue Kills: {cube_stats['blue_kills']}")
        game_state['red_active'] = False
        game_state['game_over'] = True

    screen.fill(WHITE)
    draw_cube(game_state['blue_x'], game_state['blue_y'], BLUE)
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