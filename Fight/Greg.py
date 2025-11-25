# currently 1748 lines in this file :sob:

import pygame
import random
import sys
import math
import os
import re

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
GREEN = (0, 200, 0)
BRIGHT_GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BROWN = (139, 69, 19)
PINK = (255, 192, 203)
DARK_BLUE = (0, 0, 139)

PURPLE_TUPLE = (128, 0, 128) 

CUBE_SIZE = 50

CUBE_COLOR_MAP = {
    'blue': BLUE,
    'red': RED,
    'green': GREEN,
    'pink': PINK,
    'brown': BROWN,
    'dark blue': DARK_BLUE,

    '<undefined>': GRAY, 
}

all_cubes_data = []

def parse_cubes_file(file_content):
    """Parses the content of cubes.txt into a structured list of dictionaries."""

    content = file_content.replace('attacks:', 'attack:').replace('attack:', 'attacks:')

    cube_blocks = re.split(r'cube \d+ stats:', content, flags=re.IGNORECASE)[1:]

    cubes_list = []
    current_cube = {}

    def clean_value(value):
        """Helper to remove parenthetical notes from attack names."""
        return value.strip().replace('(windup)', '').replace('(bar)', '').replace('(inversts enemy\'s controls 3 seconds)', '').replace('(invert controls during pull 3 sec)', '').strip()

    for i, block in enumerate(cube_blocks):
        cube_index = i + 1

        lines = block.strip().split('\n')

        current_cube = {'id': cube_index}

        for line in lines:
            line = line.strip()

            if line.startswith('short_hand:'):
                current_cube['short_hand'] = line.split(':', 1)[1].strip()
            elif line.startswith('name:'):
                current_cube['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('color:'):
                current_cube['color'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('attacks:'):
                attacks_str = line.split(':', 1)[1].strip()
                attacks = [clean_value(a) for a in attacks_str.split(',')]
                current_cube['attacks'] = ", ".join(attacks)
            elif line.startswith('max hp:'):
                current_cube['max hp'] = line.split(':', 1)[1].strip()

        if 'name' not in current_cube:
            current_cube['name'] = f"Cube {current_cube['id']}"

        if 'color' not in current_cube:
            current_cube['color'] = '<undefined>'

        if 'max hp' not in current_cube:
            if cube_index in [5, 6]:
                current_cube['max hp'] = '75' 

        cubes_list.append(current_cube)

    return cubes_list

SAVE_DIR = "Save_file"
CUBES_FILE_PATH = os.path.join(SAVE_DIR, "cubes.txt")
STATS_FILE = os.path.join(SAVE_DIR, "stats.txt")
DEBUG_FILE = os.path.join(SAVE_DIR, "debug.txt")
ACHIEVEMENTS_FILE_PATH = os.path.join(SAVE_DIR, "achievements.txt") 
is_debug_mode = False 

def load_cubes_file_content(filepath):
    """Attempts to read the content of the cubes stats file."""
    if not os.path.exists(filepath):
        print(f"Error: Cube stats file not found at {filepath}")
        return ""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading cube stats file: {e}")
        return ""

CUBES_FILE_CONTENT = load_cubes_file_content(CUBES_FILE_PATH)

if CUBES_FILE_CONTENT:
    all_cubes_data = parse_cubes_file(CUBES_FILE_CONTENT)
else:
    all_cubes_data = []
    print("WARNING: No cube data loaded. 'Collected Cubes' scene will be empty.")

all_achievements_data = []

def parse_achievements_file(file_content):
    """ParsES the content of achievements.txt into a structured list of dictionaries."""

    achievements_list = []
    current_achievement = {}

    blocks = re.split(r'(achiev[e]?[mn]e?nt \d+)', file_content, flags=re.IGNORECASE)

    for i in range(1, len(blocks), 2): 

        title_line = blocks[i].strip() 
        content = blocks[i+1].strip() 

        id_match = re.search(r'(\d+)', title_line)
        if not id_match:
            print(f"Warning: Skipping malformed achievement title: {title_line}")
            continue
        current_achievement['id'] = int(id_match.group(1))

        lines = content.split('\n')

        if lines and lines[0].strip().startswith('"'):
            current_achievement['name'] = lines[0].strip().strip('"')
        else:

            current_achievement['name'] = f"Achievement {current_achievement['id']}"

        for line in lines[1:]: 
            line = line.strip()

            if line.startswith('des:'):

                current_achievement['description'] = line.split(':', 1)[1].strip().strip('"')
            elif line.startswith('unlocks:'):

                current_achievement['unlocks'] = line.split(':', 1)[1].strip().strip('"')

            elif line.startswith('status:'):
                status_value = line.split(':', 1)[1].strip().lower()
                current_achievement['unlocked'] = (status_value == 'unlocked')

        current_achievement.setdefault('description', 'No description provided.')
        current_achievement.setdefault('unlocks', 'Nothing.')
        current_achievement.setdefault('unlocked', False) 

        achievements_list.append(current_achievement.copy())
        current_achievement = {} 

    return achievements_list

def load_achievements_file_content(filepath):
    """Attempts to read the content of the achievements file."""
    if not os.path.exists(filepath):
        print(f"Error: Achievement file not found at {filepath}")
        return ""
    try:
        with open(filepath, 'r') as f:

            content = f.read()
            return content
    except Exception as e:
        print(f"Error reading achievement file: {e}")
        return ""

ACHIEVEMENTS_FILE_CONTENT = load_achievements_file_content(ACHIEVEMENTS_FILE_PATH)

if ACHIEVEMENTS_FILE_CONTENT:
    all_achievements_data = parse_achievements_file(ACHIEVEMENTS_FILE_CONTENT)
else:
    print("WARNING: No achievement data loaded.")

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
AI_SLASH_FLASH_CYCLES = 4       
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
PARRY_WINDOW_DURATION_MS = 200 

P2_CHARGE_FLASH_CYCLES = 3 
P2_BOUNDARY_DAMAGE = 25
P2_BOUNDARY_STUN_MS = 3000 

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
    'parry_timer': 0.0,
}

game_state = initial_game_state.copy()

current_scene = "menu" 
selected_cube_data = None 
selected_mode = None 

initial_char_select_state = {
    'p1_selection_id': None,
    'p2_selection_id': None,
    'current_player': 'P1', 
    'message': "",
    'cube_rects': [] 
}
character_select_state = initial_char_select_state.copy()

def load_stats():
    """Reads kill counts from stats.txt or initializes them."""
    stats = {'red_kills': 0, 'blue_kills': 0}
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 1:
                    red_line = lines[0].strip()
                    if ":" in red_line:
                        stats['red_kills'] = int(red_line.split(':')[1].strip())
                if len(lines) >= 2:
                    blue_line = lines[1].strip()
                    if ":" in blue_line:
                        stats['blue_kills'] = int(blue_line.split(':')[1].strip())
        except (IOError, ValueError) as e:
            print(f"Error loading stats file, using defaults: {e}")

            os.makedirs(SAVE_DIR, exist_ok=True)
    return stats

def save_stats(stats):
    """Writes kill counts to stats.txt in the required format."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    try:
        with open(STATS_FILE, 'w') as f:
            f.write(f"red cube killed: {stats['red_kills']}\n")
            f.write(f"blue cube killed: {stats['blue_kills']}\n")
    except IOError as e:
        print(f"Error saving stats file: {e}")

cube_stats = load_stats()

def draw_text(text, font_size, color, x, y, align='center'):
    """Draws text using a specified font size with alignment."""
    text_font = pygame.font.Font(None, font_size)
    text_surface = text_font.render(text, True, color)
    text_rect = text_surface.get_rect()

    if align == 'center':
        text_rect.center = (x, y)
    elif align == 'left':
        text_rect.topleft = (x, y)
    elif align == 'right':
        text_rect.topright = (x, y)

    screen.blit(text_surface, text_rect)

def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

def get_red_cube_color(state):
    """
    Determines the color of the Red Cube based on its charge and special attack states.
    In PvP, this also covers P2's special attack windup.
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

        if selected_mode == 'ai':
            if state['flash_count'] % 2 != 0: 
                return BLACK

        elif selected_mode == 'pvp':
            if state['flash_count'] <= P2_CHARGE_FLASH_CYCLES * 2 and state['flash_count'] % 2 != 0: 
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
    """Draws P1 and P2/AI health bars and kill counts."""

    blue_health_ratio = max(0, game_state['blue_health'] / 100)
    red_health_ratio = max(0, game_state['red_health'] / 100)

    MAX_BAR_WIDTH = 200

    blue_bar_width = int(MAX_BAR_WIDTH * blue_health_ratio)
    red_bar_width = int(MAX_BAR_WIDTH * red_health_ratio)

    blue_bar_rect_outline = pygame.Rect(WIDTH - MAX_BAR_WIDTH - 10, 10, MAX_BAR_WIDTH, 20)
    blue_health_rect = pygame.Rect(WIDTH - MAX_BAR_WIDTH - 10, 10, blue_bar_width, 20)

    red_bar_rect_outline = pygame.Rect(10, 10, MAX_BAR_WIDTH, 20)
    red_health_rect = pygame.Rect(10, 10, red_bar_width, 20)

    pygame.draw.rect(screen, (100, 100, 100), blue_bar_rect_outline, 1)
    pygame.draw.rect(screen, (100, 100, 100), red_bar_rect_outline, 1)

    pygame.draw.rect(screen, BLUE, blue_health_rect)
    pygame.draw.rect(screen, RED, red_health_rect)

    blue_health_text = font.render(f"P1 (Blue): {max(0, game_state['blue_health'])}", True, WHITE)
    red_label = "P2 (Red)" if selected_mode == 'pvp' else "AI (Red)"
    red_health_text = font.render(f"{red_label}: {max(0, game_state['red_health'])}", True, WHITE)

    screen.blit(blue_health_text, (WIDTH - MAX_BAR_WIDTH - 10, 35))
    screen.blit(red_health_text, (10, 35))

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

    if mode not in ["Parried (Stun)", "Charge (Endlag)", "Charge (Windup)", "Beam (Windup)"]:

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

def do_special_attack_blue():
    """Triggers the blue cube's special purple hitbox attack."""

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

    if not is_debug_mode:
        game_state['special_attack_cooldown_timer'] = SPECIAL_ATTACK_COOLDOWN_MS
    else:
        game_state['special_attack_cooldown_timer'] = 1 

def do_special_attack_red():
    """Triggers the red cube's special cyan beam attack (P2)."""

    if not game_state['blue_active']:
        return
    if not game_state['red_active']:
        return

    if not is_debug_mode and game_state['ai_special_attack_cooldown_timer'] > 0:
        return 

    if game_state['ai_attack_state'] == 'Idle' and game_state['charge_state'] == 'Idle':
        initiate_ai_special_attack_windup_red()

def initiate_ai_special_attack_windup_red():
    """Transitions the Red Cube into the Special Windup state (always leads to Beam)."""

    game_state['ai_attack_state'] = 'SpecialWindup' 
    game_state['flash_count'] = 0

    game_state['flash_timer'] = AI_FLASH_DURATION_MS 
    game_state['red_cube_mode'] = "Beam (Windup)" 

    if selected_mode == 'pvp':
        direction = game_state['ai_last_direction']
        if direction == 'left':
            game_state['ai_beam_angle'] = math.pi 
        elif direction == 'right':
            game_state['ai_beam_angle'] = 0 
        elif direction == 'up':
            game_state['ai_beam_angle'] = -math.pi / 2 
        elif direction == 'down':
            game_state['ai_beam_angle'] = math.pi / 2 

    else:
        target_x, target_y = game_state['blue_x'], game_state['blue_y']
        red_center_x = game_state['red_x'] + CUBE_SIZE / 2
        red_center_y = game_state['red_y'] + CUBE_SIZE / 2

        dx = target_x + CUBE_SIZE / 2 - red_center_x
        dy = target_y + CUBE_SIZE / 2 - red_center_y

        game_state['ai_beam_angle'] = math.atan2(dy, dx)

def execute_ai_special_attack_red():
    """
    Triggers the P2 beam attack. Handles visual display and collision check.
    (This function is ONLY for P2, AI uses execute_ai_special_attack)
    """

    game_state['ai_cyan_beam_active'] = True
    game_state['ai_hitbox_timer'] = AI_SPECIAL_HITBOX_DURATION_MS

    beam_surface, beam_rect = get_ai_beam_rect()
    blue_cube_rect = pygame.Rect(game_state['blue_x'], game_state['blue_y'], CUBE_SIZE, CUBE_SIZE)

    if game_state['blue_active'] and beam_rect.colliderect(blue_cube_rect):
        if not is_debug_mode:
            game_state['blue_health'] -= AI_SPECIAL_ATTACK_DAMAGE
            print(f"Red Cube Beam hit! Damage: {AI_SPECIAL_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")
        else:
            print("Red Cube Beam hit! (Debug Invincible)")

    game_state['ai_special_attack_cooldown_timer'] = AI_SPECIAL_ATTACK_COOLDOWN_MS

    game_state['ai_attack_state'] = 'Idle'
    game_state['red_cube_mode'] = "Maintain" 

def initiate_parry():
    """
    Initiates the Blue Cube's parry.
    Checks if it successfully parried an attack windup.
    """
    if not game_state['blue_active'] or game_state['game_over']:
        return

    charge_windup_success_count = (P2_CHARGE_FLASH_CYCLES * 2) + 1 if selected_mode == 'pvp' else (CHARGE_FLASH_CYCLES * 2)

    charge_windup_success = (
        game_state['charge_state'] == 'Windup' and 
        game_state['flash_count'] == charge_windup_success_count and 
        game_state['flash_timer'] > 0 
    )

    special_windup_success = (
        game_state['ai_attack_state'] == 'SpecialWindup' and
        game_state['flash_count'] == (AI_SLASH_FLASH_CYCLES * 2) and 
        game_state['flash_timer'] > 0
    )

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
    Triggers the AI beam attack. Handles visual display and collision check.
    (This function is ONLY for AI)
    """

    game_state['ai_cyan_beam_active'] = True
    game_state['ai_hitbox_timer'] = AI_SPECIAL_HITBOX_DURATION_MS

    angle = game_state['ai_beam_angle']

    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2

    beam_start_x = red_center_x + (CUBE_SIZE / 2) * math.cos(angle)
    beam_start_y = red_center_y + (CUBE_SIZE / 2) * math.sin(angle)
    beam_end_x = red_center_x + AI_BEAM_LENGTH * math.cos(angle)
    beam_end_y = red_center_y + AI_BEAM_LENGTH * math.sin(angle)

    blue_cube_rect = pygame.Rect(game_state['blue_x'], game_state['blue_y'], CUBE_SIZE, CUBE_SIZE)

    if game_state['blue_active'] and blue_cube_rect.clipline(beam_start_x, beam_start_y, beam_end_x, beam_end_y):
        if not is_debug_mode:
            game_state['blue_health'] -= AI_SPECIAL_ATTACK_DAMAGE
            print(f"Red Cube Beam hit! Damage: {AI_SPECIAL_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")
        else:
            print("Red Cube Beam hit! (Debug Invincible)")

    game_state['ai_special_attack_cooldown_timer'] = AI_SPECIAL_ATTACK_COOLDOWN_MS

    game_state['ai_attack_state'] = 'Idle'
    game_state['red_cube_mode'] = "Maintain" 

def draw_cube_preview(x, y, color_name, size=30):
    """Draws a cube preview with an optional outline."""

    color = CUBE_COLOR_MAP.get(color_name.lower(), GRAY) 

    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, color, rect)

    pygame.draw.rect(screen, WHITE, rect, 2) 

    return rect

def draw_cube_detail_panel(cube_data):
    """Draws the detailed stats panel for the selected cube."""

    PANEL_WIDTH = 300
    PANEL_HEIGHT = HEIGHT - 120 
    PANEL_X = WIDTH - PANEL_WIDTH - 20
    PANEL_Y = 80

    pygame.draw.rect(screen, DARK_GRAY, (PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT), border_radius=10)
    pygame.draw.rect(screen, WHITE, (PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT), 3, border_radius=10)

    start_x = PANEL_X + 20
    current_y = PANEL_Y + 20

    panel_title = cube_data.get('name', f"Cube {cube_data['id']}").title()
    draw_text(f"{panel_title} - Details", 36, WHITE, PANEL_X + PANEL_WIDTH // 2, current_y)
    current_y += 50

    preview_size = 80
    preview_x = PANEL_X + PANEL_WIDTH // 2 - preview_size // 2
    draw_cube_preview(preview_x, current_y, cube_data['color'], size=preview_size)
    current_y += preview_size + 20

    draw_text(f"Color: {cube_data['color'].capitalize()}", 28, WHITE, start_x, current_y, align='left')
    current_y += 30

    draw_text(f"Max HP: {cube_data.get('max hp', 'N/A')}", 28, WHITE, start_x, current_y, align='left')
    current_y += 40

    draw_text("Attacks:", 30, CYAN, start_x, current_y, align='left')
    current_y += 30

    attacks_text = cube_data.get('attacks', 'None')

    if ',' in attacks_text:
        attacks_list = [a.strip() for a in attacks_text.split(',')]
    else:
        attacks_list = [attacks_text.strip()]

    for attack in attacks_list:
        if current_y < PANEL_Y + PANEL_HEIGHT - 30: 
            draw_text(f"- {attack}", 24, GRAY, start_x + 10, current_y, align='left')
            current_y += 25

def achievements_scene():
    """Renders the list of achievements and their status."""

    global current_scene, running

    mouse_x, mouse_y = pygame.mouse.get_pos()
    click = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                click = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            current_scene = "menu"
            return

    screen.fill(BLACK) 

    WARNING_Y = 20
    SECTION_TITLE_Y = 80 
    LIST_START_Y = 140 

    draw_text("DEMO FEATURE: WIP", 30, RED, WIDTH // 2, WARNING_Y)

    draw_text("--- ACHIEVEMENTS ---", 36, WHITE, WIDTH // 2, SECTION_TITLE_Y)

    button_width, button_height = 150, 40
    back_x = 70
    back_y = SECTION_TITLE_Y 
    back_rect = pygame.Rect(back_x - button_width // 2, back_y - button_height // 2, button_width, button_height)

    button_color = DARK_GRAY
    if back_rect.collidepoint((mouse_x, mouse_y)):
        button_color = GRAY
        if click: 
            current_scene = "menu"
            return 

    pygame.draw.rect(screen, button_color, back_rect, border_radius=5)
    draw_text("Back (ESC)", 28, BLACK, back_x, back_y)

    current_y = LIST_START_Y
    start_x = 50
    item_height = 75

    for achievement in all_achievements_data:

        box_rect = pygame.Rect(start_x, current_y, WIDTH - 100, item_height)

        box_color = GREEN if achievement['unlocked'] else DARK_GRAY
        pygame.draw.rect(screen, box_color, box_rect, border_radius=5)

        text_color = BLACK if achievement['unlocked'] else WHITE

        draw_text(f"#{achievement['id']} - {achievement['name']}", 30, text_color, start_x + 10, current_y + 10, align='left')
        draw_text(f"Des: {achievement['description']}", 24, text_color, start_x + 10, current_y + 35, align='left')
        draw_text(f"Unlocks: {achievement['unlocks']}", 24, text_color, start_x + 10, current_y + 55, align='left')

        status_text = "UNLOCKED" if achievement['unlocked'] else "LOCKED"
        status_color = BLACK if achievement['unlocked'] else RED
        draw_text(status_text, 30, status_color, WIDTH - 60, current_y + item_height // 2, align='right')

        current_y += item_height + 10

    pygame.display.flip()

def mode_select_menu():
    global current_scene, running, selected_mode, character_select_state

    mouse_x, mouse_y = pygame.mouse.get_pos() 
    click = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                click = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            current_scene = "menu"
            return

    screen.fill(BLACK) 

    draw_text("SELECT GAME MODE", 72, WHITE, WIDTH // 2, HEIGHT // 4)

    button_width, button_height = 350, 60
    center_x = WIDTH // 2

    ai_y = HEIGHT // 2
    player_y = ai_y + button_height + 30 
    back_y = player_y + button_height + 30

    ai_rect = pygame.Rect(center_x - button_width // 2, ai_y - button_height // 2, button_width, button_height)

    button_color = RED 
    if ai_rect.collidepoint((mouse_x, mouse_y)):
        button_color = (255, 100, 100) 
        if click:
            selected_mode = 'ai'
            current_scene = "game"
            reset_game_state(keep_stats=True) 
            return 

    pygame.draw.rect(screen, button_color, ai_rect, border_radius=10)
    draw_text("PLAYER vs. AI", 36, BLACK, center_x, ai_y) 

    player_rect = pygame.Rect(center_x - button_width // 2, player_y - button_height // 2, button_width, button_height)

    button_color = BLUE
    if player_rect.collidepoint((mouse_x, mouse_y)):
        button_color = CYAN
        if click:
            selected_mode = 'pvp' 
            current_scene = "character_select" 
            character_select_state = initial_char_select_state.copy() 
            return 

    pygame.draw.rect(screen, button_color, player_rect, border_radius=10)
    draw_text("PLAYER vs. PLAYER", 36, BLACK, center_x, player_y)

    back_rect = pygame.Rect(center_x - button_width // 2, back_y - button_height // 2, button_width, button_height)

    button_color = DARK_GRAY
    if back_rect.collidepoint((mouse_x, mouse_y)):
        button_color = GRAY
        if click:
            current_scene = "menu"
            return 

    pygame.draw.rect(screen, button_color, back_rect, border_radius=10)
    draw_text("BACK", 36, BLACK, center_x, back_y)

    pygame.display.flip()

def character_select_scene():
    """Renders the PvP character selection screen."""
    global current_scene, running, character_select_state

    mouse_x, mouse_y = pygame.mouse.get_pos()
    click = False

    GRID_START_X = 50
    GRID_START_Y = 150
    CUBE_DISPLAY_SIZE = 80
    PADDING = 25
    COLUMNS = 4 

    button_width, button_height = 250, 60
    start_game_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT - 80, button_width, button_height)

    character_select_state['cube_rects'] = [] 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                click = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            current_scene = "mode_select" 
            character_select_state = initial_char_select_state.copy() 
            return

    screen.fill(BLACK) 

    draw_text("CHARACTER SELECT", 60, WHITE, WIDTH // 2, 40)

    instruction_text = ""
    instruction_color = WHITE
    if character_select_state['current_player'] == 'P1':
        instruction_text = "PLAYER 1: CHOOSE YOUR CUBE"
        instruction_color = BLUE
    elif character_select_state['current_player'] == 'P2':
        instruction_text = "PLAYER 2: CHOOSE YOUR CUBE"
        instruction_color = RED
    elif character_select_state['current_player'] == 'START':
        instruction_text = "BOTH PLAYERS SELECTED"
        instruction_color = GREEN

    draw_text(instruction_text, 40, instruction_color, WIDTH // 2, 90)

    hovered_cube_index = -1
    for i, cube in enumerate(all_cubes_data):
        col = i % COLUMNS
        row = i // COLUMNS

        x_pos = GRID_START_X + col * (CUBE_DISPLAY_SIZE + PADDING)
        y_pos = GRID_START_Y + row * (CUBE_DISPLAY_SIZE + PADDING)

        cube_rect = draw_cube_preview(x_pos, y_pos, cube['color'], size=CUBE_DISPLAY_SIZE)
        character_select_state['cube_rects'].append(cube_rect)

        if cube_rect.collidepoint((mouse_x, mouse_y)):
            hovered_cube_index = i

        border_width = 5

        if cube['id'] == character_select_state['p1_selection_id']:
            pygame.draw.rect(screen, BLUE, cube_rect, border_width, border_radius=5)

        elif cube['id'] == character_select_state['p2_selection_id']:
            pygame.draw.rect(screen, RED, cube_rect, border_width, border_radius=5)

        elif i == hovered_cube_index:
             pygame.draw.rect(screen, GRAY, cube_rect, border_width, border_radius=5)

    if click:
        clicked_on_cube = False
        for i, rect in enumerate(character_select_state['cube_rects']):
            if rect.collidepoint((mouse_x, mouse_y)):
                clicked_on_cube = True
                selected_cube = all_cubes_data[i]

                is_taken = False
                if character_select_state['current_player'] == 'P1':
                    is_taken = (selected_cube['id'] == character_select_state['p2_selection_id'])
                elif character_select_state['current_player'] == 'P2':
                     is_taken = (selected_cube['id'] == character_select_state['p1_selection_id'])

                if not is_taken:

                    if selected_cube['id'] > 2:
                        character_select_state['message'] = "First 2 cubes work but rest are only placeholders"
                    else:

                        character_select_state['message'] = "" 

                    if character_select_state['current_player'] == 'P1':
                        character_select_state['p1_selection_id'] = selected_cube['id']
                        character_select_state['current_player'] = 'P2'
                    elif character_select_state['current_player'] == 'P2':
                        character_select_state['p2_selection_id'] = selected_cube['id']
                        character_select_state['current_player'] = 'START' 

                break 

        if character_select_state['current_player'] == 'START':
            if start_game_rect.collidepoint((mouse_x, mouse_y)):

                current_scene = "game"
                reset_game_state(keep_stats=True) 
                return

    if character_select_state['message']:
        draw_text(character_select_state['message'], 28, RED, WIDTH // 2, HEIGHT - 120)

    if character_select_state['current_player'] == 'START':
        button_color = DARK_GRAY
        if start_game_rect.collidepoint((mouse_x, mouse_y)):
            button_color = GRAY

        pygame.draw.rect(screen, button_color, start_game_rect, border_radius=10)
        draw_text("START GAME", 36, BLACK, start_game_rect.centerx, start_game_rect.centery)

    pygame.display.flip()

def main_menu():
    global current_scene, running

    mouse_x, mouse_y = pygame.mouse.get_pos()
    click = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                click = True

    screen.fill(BLACK) 

    draw_text("CUBE COMBAT", 72, RED, WIDTH // 2, HEIGHT // 5)

    button_width, button_height = 250, 60
    center_x = WIDTH // 2

    start_y = HEIGHT // 2 - 50
    collected_y = start_y + button_height + 30 
    achievements_y = collected_y + button_height + 30 
    quit_y = achievements_y + button_height + 30

    start_rect = pygame.Rect(center_x - button_width // 2, start_y - button_height // 2, button_width, button_height)

    button_color = GREEN
    if start_rect.collidepoint((mouse_x, mouse_y)):
        button_color = BRIGHT_GREEN
        if click:
            current_scene = "mode_select" 
            return 

    pygame.draw.rect(screen, button_color, start_rect, border_radius=10)
    draw_text("START GAME", 36, BLACK, center_x, start_y)

    collected_rect = pygame.Rect(center_x - button_width // 2, collected_y - button_height // 2, button_width, button_height)

    button_color = BLUE
    if collected_rect.collidepoint((mouse_x, mouse_y)):
        button_color = CYAN
        if click:
            current_scene = "collected_cubes" 
            return 

    pygame.draw.rect(screen, button_color, collected_rect, border_radius=10)
    draw_text("COLLECTED CUBES", 36, BLACK, center_x, collected_y)

    achievements_rect = pygame.Rect(center_x - button_width // 2, achievements_y - button_height // 2, button_width, button_height)

    button_color = PINK 
    if achievements_rect.collidepoint((mouse_x, mouse_y)):
        button_color = (255, 100, 150) 
        if click:
            current_scene = "achievements" 
            return 

    pygame.draw.rect(screen, button_color, achievements_rect, border_radius=10)
    draw_text("ACHIEVEMENTS", 36, BLACK, center_x, achievements_y)

    quit_rect = pygame.Rect(center_x - button_width // 2, quit_y - button_height // 2, button_width, button_height)

    button_color = DARK_GRAY
    if quit_rect.collidepoint((mouse_x, mouse_y)):
        button_color = GRAY
        if click:
            running = False
            return 

    pygame.draw.rect(screen, button_color, quit_rect, border_radius=10)
    draw_text("QUIT", 36, BLACK, center_x, quit_y)

    pygame.display.flip()

def collected_cubes_scene():
    """Renders the list of collected cubes in a grid and a detailed stats panel."""

    global current_scene, running, selected_cube_data

    mouse_x, mouse_y = pygame.mouse.get_pos()
    click = False

    GRID_START_X = 50
    GRID_START_Y = 100
    CUBE_DISPLAY_SIZE = 60
    PADDING = 20
    COLUMNS = 3

    cube_rects = [] 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                click = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            current_scene = "menu"
            selected_cube_data = None 
            return

    screen.fill(BLACK) 
    draw_text("COLLECTED CUBES", 50, WHITE, WIDTH // 2, 40)

    button_width, button_height = 150, 40
    back_x = 70
    back_y = 40
    back_rect = pygame.Rect(back_x - button_width // 2, back_y - button_height // 2, button_width, button_height)

    button_color = DARK_GRAY
    if back_rect.collidepoint((mouse_x, mouse_y)):
        button_color = GRAY
        if click: 
            current_scene = "menu"
            selected_cube_data = None
            return 

    pygame.draw.rect(screen, button_color, back_rect, border_radius=5)
    draw_text("Back (ESC)", 28, BLACK, back_x, back_y)

    for i, cube in enumerate(all_cubes_data):
        col = i % COLUMNS
        row = i // COLUMNS

        x_pos = GRID_START_X + col * (CUBE_DISPLAY_SIZE + PADDING)
        y_pos = GRID_START_Y + row * (CUBE_DISPLAY_SIZE + PADDING)

        cube_rect = draw_cube_preview(x_pos, y_pos, cube['color'], size=CUBE_DISPLAY_SIZE)
        cube_rects.append(cube_rect)

        if selected_cube_data and cube['id'] == selected_cube_data['id']:
            pygame.draw.rect(screen, BRIGHT_GREEN, cube_rect, 5, border_radius=5)

    if click:
        clicked_on_panel = False

        if selected_cube_data:
            PANEL_WIDTH = 300
            PANEL_X = WIDTH - PANEL_WIDTH - 20
            panel_rect = pygame.Rect(PANEL_X, 80, PANEL_WIDTH, HEIGHT - 120)
            if panel_rect.collidepoint((mouse_x, mouse_y)):
                clicked_on_panel = True

        if not clicked_on_panel:
            clicked_on_cube = False
            for i, rect in enumerate(cube_rects):
                if rect.collidepoint((mouse_x, mouse_y)):
                    selected_cube_data = all_cubes_data[i]
                    print(f"Selected Cube {selected_cube_data['id']}")
                    clicked_on_cube = True
                    break

            if not clicked_on_cube:
                selected_cube_data = None

    if selected_cube_data:
        draw_cube_detail_panel(selected_cube_data)
    else:

        draw_text("Click a Cube to View Details", 36, DARK_GRAY, WIDTH * 0.7, HEIGHT // 2)

    pygame.display.flip()

def reset_game_state(keep_stats=True):
    """
    Resets all game variables to their initial state.
    """

    global game_state

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

def handle_player_movement(cube_color, keys, current_move_speed):
    """Handles movement for a single player."""

    if cube_color == 'blue':

        if game_state['game_over']:
             return

        dx, dy = 0, 0
        if keys[pygame.K_a]:
            dx -= current_move_speed
            game_state['last_direction'] = 'left' 
        if keys[pygame.K_d]:
            dx += current_move_speed
            game_state['last_direction'] = 'right' 
        if keys[pygame.K_w]:
            dy -= current_move_speed
            game_state['last_direction'] = 'up'
        if keys[pygame.K_s]:
            dy += current_move_speed
            game_state['last_direction'] = 'down'

        game_state['blue_x'] += dx
        game_state['blue_y'] += dy

        game_state['blue_x'] = max(0, min(game_state['blue_x'], WIDTH - CUBE_SIZE))
        game_state['blue_y'] = max(0, min(game_state['blue_y'], HEIGHT - CUBE_SIZE))

    elif cube_color == 'red' and selected_mode == 'pvp':

        ai_is_stuck = game_state['red_cube_mode'] in ["Parried (Stun)", "Charge (Endlag)", "Charge (Windup)", "Beam (Windup)"]
        if ai_is_stuck or game_state['game_over']:
             return 

        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx -= current_move_speed
            game_state['ai_last_direction'] = 'left' 
        if keys[pygame.K_RIGHT]:
            dx += current_move_speed
            game_state['ai_last_direction'] = 'right' 
        if keys[pygame.K_UP]:
            dy -= current_move_speed
            game_state['ai_last_direction'] = 'up'
        if keys[pygame.K_DOWN]:
            dy += current_move_speed
            game_state['ai_last_direction'] = 'down'

        game_state['red_x'] += dx
        game_state['red_y'] += dy

        game_state['red_x'] = max(0, min(game_state['red_x'], WIDTH - CUBE_SIZE))
        game_state['red_y'] = max(0, min(game_state['red_y'], HEIGHT - CUBE_SIZE))

def initiate_red_cube_charge_pvp():
    """Triggers the Red Cube's charge attack in PvP mode."""
    if not game_state['blue_active']:
        return

    if not game_state['red_active'] or game_state['charge_state'] != 'Idle' or game_state['ai_attack_state'] != 'Idle':
        return 

    game_state['charge_state'] = 'Windup'
    game_state['flash_count'] = 0
    game_state['flash_timer'] = FLASH_DURATION_MS 

    red_x, red_y = game_state['red_x'], game_state['red_y']

    direction = game_state['ai_last_direction']
    angle = 0.0
    if direction == 'left':
        angle = math.pi 
    elif direction == 'right':
        angle = 0 
    elif direction == 'up':
        angle = -math.pi / 2 
    elif direction == 'down':
        angle = math.pi / 2 

    game_state['charge_dx'] = math.cos(angle)
    game_state['charge_dy'] = math.sin(angle)

    game_state['red_cube_mode'] = "Charge (Windup)" 
    print("Player 2 initiated Charge Windup.")

running = True
clock = pygame.time.Clock()

while running:

    dt = clock.tick(60) 

    if current_scene == "menu":
        main_menu()
        continue

    if current_scene == "mode_select": 
        mode_select_menu()
        continue

    if current_scene == "character_select":
        character_select_scene()
        continue

    if current_scene == "collected_cubes":
        collected_cubes_scene()
        continue

    if current_scene == "achievements": 
        achievements_scene()
        continue

    is_debug_mode = check_debug_file() 

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if game_state['blue_active'] and not game_state['game_over']:
                if event.key == pygame.K_SPACE: 
                    do_special_attack_blue()
                if event.key == pygame.K_f: 
                    initiate_parry()

            if selected_mode == 'pvp' and game_state['red_active'] and not game_state['game_over']:
                if event.key == pygame.K_l: 
                    do_special_attack_red()
                if event.key == pygame.K_k: 
                    initiate_red_cube_charge_pvp()

            if event.key == pygame.K_r and game_state['game_over']:
                print("Restarting Game...")
                reset_game_state(keep_stats=True) 

            if event.key == pygame.K_ESCAPE and not game_state['game_over']:
                 current_scene = 'menu'
                 selected_mode = None 
                 reset_game_state(keep_stats=True) 
                 print("Returning to Main Menu.")

    if game_state['game_over']:
        screen.fill(WHITE)
        draw_health_bars()

        winner = "Red Cube" if game_state['blue_health'] <= 0 else "Blue Cube"
        winner_color = RED if game_state['blue_health'] <= 0 else BLUE

        message = f"{winner} Wins! Press R to Restart"

        game_over_text = font.render(message, True, winner_color)
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
        pygame.display.flip()
        continue 

    current_move_speed = game_state.get('move_speed', MOVE_SPEED)
    if game_state['blue_active']:
        handle_player_movement('blue', keys, current_move_speed)
    if selected_mode == 'pvp' and game_state['red_active']:
        handle_player_movement('red', keys, current_move_speed)

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

    if game_state['special_attack_cooldown_timer'] > 0:
        if not is_debug_mode:
            game_state['special_attack_cooldown_timer'] -= dt
        else:
            game_state['special_attack_cooldown_timer'] = 1 
        if game_state['special_attack_cooldown_timer'] < 0:
            game_state['special_attack_cooldown_timer'] = 0

    if game_state['ai_special_attack_cooldown_timer'] > 0:
        if not is_debug_mode:
            game_state['ai_special_attack_cooldown_timer'] -= dt
        else:
            game_state['ai_special_attack_cooldown_timer'] = 1 
        if game_state['ai_special_attack_cooldown_timer'] < 0:
            game_state['ai_special_attack_cooldown_timer'] = 0

    if game_state['red_active']:

        if selected_mode == 'ai':
            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            distance_to_player = calculate_distance(game_state['red_x'], game_state['red_y'], target_x, target_y)

            ai_is_stuck = game_state['red_cube_mode'] in ["Parried (Stun)", "Charge (Endlag)", "Charge (Windup)", "Beam (Windup)"]

            if game_state['ai_attack_state'] == 'Idle' and not ai_is_stuck:

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

                    flash_end_count = (CHARGE_FLASH_CYCLES * 2)
                    if game_state['flash_timer'] <= 0:
                        game_state['flash_count'] += 1

                        if game_state['flash_count'] > flash_end_count:
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

        elif selected_mode == 'pvp':

            if game_state['ai_attack_state'] == 'SpecialWindup': 

                game_state['flash_timer'] -= dt

                if game_state['flash_timer'] <= 0:
                    game_state['flash_count'] += 1

                    if game_state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2) + 1:
                        execute_ai_special_attack_red() 
                    else:
                        game_state['flash_timer'] = AI_FLASH_DURATION_MS 

                game_state['red_cube_mode'] = "Beam (Windup)" 

            elif game_state['charge_state'] == 'Windup': 

                game_state['flash_timer'] -= dt

                flash_end_count = (P2_CHARGE_FLASH_CYCLES * 2) 
                if game_state['flash_timer'] <= 0:
                    game_state['flash_count'] += 1

                    if game_state['flash_count'] > flash_end_count:
                        game_state['charge_state'] = 'Charging'
                        game_state['red_cube_mode'] = "Charge"
                    else:
                        game_state['flash_timer'] = FLASH_DURATION_MS 

                game_state['red_cube_mode'] = "Charge (Windup)" 

            elif game_state['charge_state'] == 'Charging': 
                game_state['red_cube_mode'] = "Charge"

                move_x = game_state['charge_dx'] * (CHARGE_SPEED * 1.5)
                move_y = game_state['charge_dy'] * (CHARGE_SPEED * 1.5)
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

                    if not is_debug_mode:
                        game_state['red_health'] -= P2_BOUNDARY_DAMAGE
                        print(f"Red Cube hit boundary! Damage: {P2_BOUNDARY_DAMAGE}. Red Health: {max(0, game_state['red_health'])}")

                    game_state['charge_state'] = 'Endlag' 
                    game_state['endlag_timer'] = P2_BOUNDARY_STUN_MS 
                    game_state['red_cube_mode'] = "Charge (Endlag)"

            elif game_state['charge_state'] == 'Endlag':

                game_state['endlag_timer'] -= dt 
                if game_state['endlag_timer'] <= 0:
                    game_state['charge_state'] = 'Idle'
                    game_state['red_cube_mode'] = "Maintain" 
                else:
                    game_state['red_cube_mode'] = "Charge (Endlag)" 

        if game_state['ai_cyan_beam_active']:
            game_state['ai_hitbox_timer'] -= dt

            if selected_mode == 'ai':
                if game_state['ai_hitbox_timer'] <= 0:
                    game_state['ai_cyan_beam_active'] = False
                    game_state['ai_beam_angle'] = 0.0

            elif selected_mode == 'pvp':
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

    is_charging = game_state['charge_state'] == 'Charging'

    if is_charging:

        if (game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
            game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
            game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
            game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):

            if game_state['blue_active'] and game_state['blue_health'] > 0:
                if not is_debug_mode:

                    game_state['blue_health'] = 0 
                    print(f"Red Cube Charge hit! INSTA-KILL! Blue Health: {max(0, game_state['blue_health'])}")
                else:
                    print("Red Cube Charge hit! (Debug Invincible)")

                game_state['charge_state'] = 'Endlag' 
                game_state['endlag_timer'] = ENDLAG_DURATION_MS 
                game_state['red_cube_mode'] = "Charge (Endlag)"

    if game_state['blue_health'] <= 0:
        if game_state['blue_active']:
            print("Blue Cube Defeated!")
            cube_stats['red_kills'] += 1 
            save_stats(cube_stats)
        game_state['blue_active'] = False
        game_state['game_over'] = True

    if game_state['red_health'] <= 0:
        if game_state['red_active']:
            print("Red Cube Defeated!")
            cube_stats['blue_kills'] += 1 
            save_stats(cube_stats)

            if is_debug_mode and selected_mode == 'ai': 
                print("Debug Mode: Red Cube Respawning...")
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

    screen.fill(WHITE) 

    if game_state['blue_active']:
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