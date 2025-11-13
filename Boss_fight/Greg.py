import pygame
import random
import customtkinter as ctk
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cube Combat")

# --- CustomTkinter Appearance Settings ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
# ----------------------------------------

# Colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0) # Added for flashing effect
WHITE = (255, 255, 255)
CYAN = (0, 255, 255) # For the 4th Beam flash
# Special Attack Colors (MUST be defined for both Pygame and CustomTkinter)
PURPLE_TUPLE = (128, 0, 128) # For Pygame drawing
PURPLE_HEX = "#800080"      # For CustomTkinter styling
# AI Special Attack Color - YELLOW NO LONGER USED
# ----------------------------------------

# Cube Size
CUBE_SIZE = 50

# Player Positions (Initial)
blue_x = 20
blue_y = HEIGHT // 2 - CUBE_SIZE // 2
red_x = WIDTH - CUBE_SIZE - 20
red_y = HEIGHT // 2 - CUBE_SIZE // 2

# Player Movement Speed
MOVE_SPEED = 5
# AI Movement Speed (Slightly slower for balance)
AI_MOVE_SPEED = 3

# --- AI CONSTANTS AND THRESHOLDS ---
ATTACK_RANGE = 100
MAINTAIN_RANGE_MIN = 150
MAINTAIN_RANGE_MAX = 350        # Used as the "far away" condition for retreat
RETREAT_HEALTH_THRESHOLD = 25   # Red cube retreats only below this HP
# -----------------------------------------------------------


# --- CHARGE ATTACK CONSTANTS ---
CHARGE_SPEED = 15              # Speed during charge (Damage occurs during this phase)
CHARGE_INITIATE_CHANCE = 0.001 # Chance per frame to start windup (0.1%)
CHARGE_FLASH_CYCLES = 2        # Number of times to flash black (RED->BLACK->RED->BLACK->RED)
FLASH_DURATION_MS = 200        # Duration of each color state change (milliseconds)
ENDLAG_DURATION_MS = 2000      # 2 seconds of cooldown after charge
CHARGE_ATTACK_DAMAGE = 25      # Damage applied upon contact during Charging state
# -------------------------------

# --- AI BEAM WINDUP CONSTANTS (Slash logic removed) ---
# 3 blinks + 1 cyan flash
AI_SLASH_FLASH_CYCLES = 3       
AI_FLASH_DURATION_MS = 150      
AI_BEAM_RANGE = 300             # Range is irrelevant, but kept as a constant
AI_BEAM_WIDTH = 10              
AI_BEAM_LENGTH = 700            
AI_BEAM_SPEED = 0.1             
# -------------------------------------

# Player Attack Damage 
ATTACK_DAMAGE = 20

# --- BLUE CUBE (PLAYER) SPECIAL ATTACK CONSTANTS ---
SPECIAL_ATTACK_DAMAGE = 25
HITBOX_DURATION_MS = 500       
SPECIAL_ATTACK_COOLDOWN_MS = 3000 
# --------------------------------

# --- RED CUBE (AI) SPECIAL ATTACK CONSTANTS ---
AI_SPECIAL_ATTACK_DAMAGE = 30 # Used only for Beam
AI_SPECIAL_HITBOX_DURATION_MS = 600
AI_SPECIAL_ATTACK_COOLDOWN_MS = 4000 
AI_SPECIAL_ATTACK_RANGE = 200        # AI will trigger if the player is within this range
# ----------------------------------------------------

# Player States (Initial)
INITIAL_BLUE_ACTIVE = True
INITIAL_RED_ACTIVE = True
INITIAL_BLUE_HEALTH = 100
INITIAL_RED_HEALTH = 100
INITIAL_RED_CUBE_MODE = "Maintain"

# Font
font = pygame.font.Font(None, 36)

# Initial Game state variables (shared between Pygame and Tkinter)
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
    
    # --- CHARGE STATE VARIABLES ---
    'charge_state': 'Idle',       
    'flash_timer': 0,             
    'flash_count': 0,             
    'charge_dx': 0,               
    'charge_dy': 0,               
    'endlag_timer': 0.0,          

    # --- BLUE CUBE SPECIAL ATTACK STATE VARIABLES (Purple) ---
    'purple_hitbox_active': False,
    'purple_hitbox_rect': None,    
    'hitbox_timer': 0,             
    'last_direction': 'right',     
    'special_attack_cooldown_timer': 0,

    # --- RED CUBE SPECIAL ATTACK STATE VARIABLES (Only Beam) ---
    # Slash variables removed: ai_yellow_hitbox_active, ai_yellow_hitbox_rect
    'ai_cyan_beam_active': False,     
    'ai_beam_angle': 0.0,             
    'ai_hitbox_timer': 0,
    'ai_last_direction': 'left', 
    'ai_special_attack_cooldown_timer': 0,
    'ai_attack_state': 'Idle',    # 'Idle', 'SpecialWindup'
}

# Use a deep copy to ensure the game_state is a mutable dictionary separate from the initial template
game_state = initial_game_state.copy()


# Function to draw a cube
def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

# Function to determine the Red Cube's display color (for flashing)
def get_red_cube_color(state):
    """
    Determines the color of the Red Cube based on its charge and special attack states.
    """
    
    # Priority 1: Special Attack Windup (now always the Beam pattern)
    if state['ai_attack_state'] == 'SpecialWindup':
        # Check for the final CYAN flash state (flash_count > 6)
        if state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2): 
            return CYAN
            
        # Flash black on odd flash counts (up to 6)
        if state['flash_count'] % 2 != 0: 
             return BLACK
        return RED # Otherwise show RED during windup

    # Priority 2: Endlag (Stun) - Always BLACK
    if state['charge_state'] == 'Endlag':
        return BLACK
    
    # Priority 3: Charge Windup - Flashing BLACK/RED
    if state['charge_state'] == 'Windup':
        # Flash black on odd flash counts
        if state['flash_count'] % 2 != 0: 
             return BLACK
        return RED # Otherwise show RED during charge windup
        
    # Default color
    return RED


# Function to draw health bars
def draw_health_bars():
    # Use 100 as the maximum health for percentage calculation
    blue_health_ratio = max(0, game_state['blue_health'] / 100)
    red_health_ratio = max(0, game_state['red_health'] / 100)
    
    # Health bar widths (Max width 200 for clarity)
    MAX_BAR_WIDTH = 200
    
    blue_bar_width = int(MAX_BAR_WIDTH * blue_health_ratio)
    red_bar_width = int(MAX_BAR_WIDTH * red_health_ratio)

    # Position blue bar (right side)
    blue_health_rect = pygame.Rect(WIDTH - MAX_BAR_WIDTH - 10, 10, blue_bar_width, 20)
    # Position red bar (left side)
    red_health_rect = pygame.Rect(10, 10, red_bar_width, 20)
    
    # Draw background bar (optional, but shows max health)
    pygame.draw.rect(screen, (100, 100, 100), (WIDTH - MAX_BAR_WIDTH - 10, 10, MAX_BAR_WIDTH, 20), 1)
    pygame.draw.rect(screen, (100, 100, 100), (10, 10, MAX_BAR_WIDTH, 20), 1)

    # Draw current health
    pygame.draw.rect(screen, BLUE, blue_health_rect)
    pygame.draw.rect(screen, RED, red_health_rect)

    # Display health values
    blue_health_text = font.render(f"Blue: {max(0, game_state['blue_health'])}", True, WHITE)
    red_health_text = font.render(f"Red: {max(0, game_state['red_health'])}", True, WHITE)
    # Adjust position for better visibility
    screen.blit(blue_health_text, (WIDTH - MAX_BAR_WIDTH - 10, 35))
    screen.blit(red_health_text, (10, 35))


# --- AI MOVEMENT LOGIC (STANDARD MODES ONLY) ---
def calculate_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between the centers of two cubes."""
    center1_x, center1_y = x1 + CUBE_SIZE / 2, y1 + CUBE_SIZE / 2
    center2_x, center2_y = x2 + CUBE_SIZE / 2, y2 + CUBE_SIZE / 2
    return math.hypot(center2_x - center1_x, center2_y - center1_y)

# Modified to accept red_health
def move_ai(mode, target_x, target_y, current_x, current_y, speed, red_health):
    """Calculates the new position based on the standard AI modes."""
    dx, dy = 0, 0
    distance = calculate_distance(current_x, current_y, target_x, target_y)

    # 1. State Transition Logic: Determine the AI's current goal (Standard Modes)
    
    # NEW RULE: Defensive Retreat only if health is below 25% AND far away
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

    
    # 2. Movement Calculation based on Mode
    if mode == "Attack" or mode == "Close Gap":
        # Move directly toward the target
        dx = target_x - current_x
        dy = target_y - current_y

    elif mode == "Defensive Retreat" or mode == "Back Off":
        # Move directly away from the target
        dx = current_x - target_x
        dy = current_y - target_y
        
    elif mode == "Maintain":
        # No purposeful movement
        dx, dy = 0, 0
        
    # 3. Apply Movement & Normalization
    
    # Normalize the vector to ensure consistent speed (unless in Maintain mode)
    move_x, move_y = 0, 0
    if dx != 0 or dy != 0:
        angle = math.atan2(dy, dx)
        move_x = speed * math.cos(angle)
        move_y = speed * math.sin(angle)
        
        # Track AI's direction for special attack
        if abs(move_x) > abs(move_y):
            game_state['ai_last_direction'] = 'right' if move_x > 0 else 'left'
        elif abs(move_y) > 0:
            game_state['ai_last_direction'] = 'down' if move_y > 0 else 'up'

    # Apply slight randomness (jitter)
    move_x += random.uniform(-1, 1) * 0.5
    move_y += random.uniform(-1, 1) * 0.5

    # Apply movement and keep within bounds
    new_x = max(0, min(current_x + move_x, WIDTH - CUBE_SIZE))
    new_y = max(0, min(current_y + move_y, HEIGHT - CUBE_SIZE))

    return new_x, new_y, mode
# --- END AI MOVEMENT LOGIC (STANDARD MODES ONLY) ---

# --- SPECIAL ATTACK LOGIC (Shared) ---

def check_hitbox_collision(hitbox_rect, target_x, target_y):
    """Checks if the target cube is inside the generated hitbox."""
    if not hitbox_rect:
        return False
    
    # Target cube's Rect
    target_rect = pygame.Rect(target_x, target_y, CUBE_SIZE, CUBE_SIZE)
    
    return hitbox_rect.colliderect(target_rect)

# --- BLUE CUBE (PLAYER) SPECIAL ATTACK ---

def do_special_attack():
    """Triggers the blue cube's special purple hitbox attack."""
    # Check cooldown
    if game_state['special_attack_cooldown_timer'] > 0:
        return 

    # 1. Calculate Hitbox Position (one cube length away from the blue cube)
    blue_x, blue_y = game_state['blue_x'], game_state['blue_y']
    direction = game_state['last_direction']
    
    offset = CUBE_SIZE # Hitbox starts where the blue cube ends
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
        return # Do nothing if no direction is set

    # Create the hitbox Rect
    hitbox_rect = pygame.Rect(hitbox_x, hitbox_y, CUBE_SIZE, CUBE_SIZE)
    
    # 2. Perform Collision Check (Damage is applied immediately upon attack initiation)
    if game_state['red_active'] and check_hitbox_collision(hitbox_rect, game_state['red_x'], game_state['red_y']):
        game_state['red_health'] -= SPECIAL_ATTACK_DAMAGE
        print(f"Blue Cube Slash hit! Damage: {SPECIAL_ATTACK_DAMAGE}. Red Health: {max(0, game_state['red_health'])}")
    
    # 3. Spawn the Hitbox (for visual linger effect)
    game_state['purple_hitbox_active'] = True
    game_state['purple_hitbox_rect'] = hitbox_rect
    game_state['hitbox_timer'] = HITBOX_DURATION_MS
    
    # 4. Start Cooldown
    game_state['special_attack_cooldown_timer'] = SPECIAL_ATTACK_COOLDOWN_MS

# --- RED CUBE (AI) SPECIAL ATTACK (BEAM ONLY) ---

def check_ai_special_attack_trigger(distance_to_player):
    """Determines if the AI should try to use its special attack (Beam)."""
    # Must be ready (cooldown=0), idle (not stunned/charging), and within range
    if (game_state['ai_special_attack_cooldown_timer'] == 0 and
        game_state['charge_state'] == 'Idle' and
        game_state['ai_attack_state'] == 'Idle' and 
        distance_to_player < AI_SPECIAL_ATTACK_RANGE):
        
        # Add a random chance to trigger (e.g., 5% chance per frame in range)
        if random.random() < 0.05:
            return True
    return False

def initiate_ai_special_attack_windup():
    """Transitions the AI into the Special Windup state (always leads to Beam)."""
    
    game_state['ai_attack_state'] = 'SpecialWindup' # Unified Windup State
    game_state['flash_count'] = 0
    # Start timer for the first flash (Red state duration)
    game_state['flash_timer'] = AI_FLASH_DURATION_MS 
    game_state['red_cube_mode'] = "Beam (Windup)" # Display windup mode
    
    # Lock the target angle for the beam immediately
    target_x, target_y = game_state['blue_x'], game_state['blue_y']
    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2
    
    # Calculate angle from Red Cube center to Blue Cube center
    dx = target_x + CUBE_SIZE / 2 - red_center_x
    dy = target_y + CUBE_SIZE / 2 - red_center_y
    # Store initial angle, which will be dynamically updated in the loop
    game_state['ai_beam_angle'] = math.atan2(dy, dx)
    

def get_ai_beam_rect():
    """
    Calculates the beam rectangle centered on the Red Cube and rotated towards the angle.
    Returns: A tuple (surface, rect) suitable for screen.blit()
    """
    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2
    # Convert angle to degrees for rotation (Pygame uses degrees, 0 is right, positive is CCW)
    angle_deg = math.degrees(game_state['ai_beam_angle'])
    
    # Create an unrotated surface for the beam
    # The surface needs to be large enough to hold the rotated beam
    surface_size = max(AI_BEAM_LENGTH, AI_BEAM_WIDTH) + 10 # Buffer
    beam_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
    
    # Draw the unrotated beam inside the surface (centered to allow rotation around its center)
    # Start the beam just outside the cube for a cleaner visual origin
    origin_offset = CUBE_SIZE / 2 
    unrotated_beam_rect = pygame.Rect(surface_size // 2 + origin_offset, surface_size // 2 - AI_BEAM_WIDTH // 2, AI_BEAM_LENGTH - origin_offset, AI_BEAM_WIDTH)
    pygame.draw.rect(beam_surface, CYAN, unrotated_beam_rect)
    
    # Rotate the surface around its center
    rotated_surface = pygame.transform.rotate(beam_surface, -angle_deg)
    
    # Get the bounding rect of the rotated surface and center it on the Red Cube's center
    rotated_rect = rotated_surface.get_rect(center=(red_center_x, red_center_y))
    
    return rotated_surface, rotated_rect

def execute_ai_special_attack():
    """
    Triggers the beam attack (now the only special attack). Handles visual display and collision check.
    """
    
    # 1. Activate Visual Linger
    game_state['ai_cyan_beam_active'] = True
    game_state['ai_hitbox_timer'] = AI_SPECIAL_HITBOX_DURATION_MS
    
    # 2. Collision Check: Simplified to check if the blue cube is within the beam's bounding area
    
    angle = game_state['ai_beam_angle']
    
    red_center_x = game_state['red_x'] + CUBE_SIZE / 2
    red_center_y = game_state['red_y'] + CUBE_SIZE / 2
    
    # Get the beam's end point
    beam_end_x = red_center_x + AI_BEAM_LENGTH * math.cos(angle)
    beam_end_y = red_center_y + AI_BEAM_LENGTH * math.sin(angle)
    
    # Create a bounding box for a rough collision check
    x_min = min(red_center_x, beam_end_x) - CUBE_SIZE 
    x_max = max(red_center_x, beam_end_x) + CUBE_SIZE
    y_min = min(red_center_y, beam_end_y) - CUBE_SIZE
    y_max = max(red_center_y, beam_end_y) + CUBE_SIZE
    
    beam_bounding_rect = pygame.Rect(x_min, y_min, x_max - x_min, y_max - y_min)

    blue_cube_rect = pygame.Rect(game_state['blue_x'], game_state['blue_y'], CUBE_SIZE, CUBE_SIZE)

    if game_state['blue_active'] and beam_bounding_rect.colliderect(blue_cube_rect):
        game_state['blue_health'] -= AI_SPECIAL_ATTACK_DAMAGE
        print(f"Red Cube Beam hit! Damage: {AI_SPECIAL_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")

    # 3. Start Cooldown
    game_state['ai_special_attack_cooldown_timer'] = AI_SPECIAL_ATTACK_COOLDOWN_MS
    
    # 4. Reset AI to Idle
    game_state['ai_attack_state'] = 'Idle'
    game_state['red_cube_mode'] = "Maintain" 

# --- END RED CUBE (AI) SPECIAL ATTACK ---


# CustomTkinter Setup
root = ctk.CTk()
root.title("Cube Combat Control Panel")

tk_mode_text = ctk.StringVar(value=f"Red Cube Mode: {game_state['red_cube_mode']}")
tk_cooldown_text = ctk.StringVar(value="Slash: READY (SPACE)")

control_panel_frame = ctk.CTkFrame(root)
control_panel_frame.pack(padx=10, pady=10)

# Add control panel buttons
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

# Function to reset the entire game state
def reset_game_state():
    """Resets all game variables to their initial state."""
    
    # Use global game_state and update its values
    global game_state
    
    # Reset all variables that change during gameplay
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
    
    # Reset charge state
    game_state['charge_state'] = 'Idle'
    game_state['flash_timer'] = 0
    game_state['flash_count'] = 0
    game_state['endlag_timer'] = 0.0

    # Reset Blue Cube special attack state
    game_state['purple_hitbox_active'] = False
    game_state['purple_hitbox_rect'] = None
    game_state['hitbox_timer'] = 0
    game_state['special_attack_cooldown_timer'] = 0 
    game_state['last_direction'] = 'right'
    
    # Reset Red Cube special attack state (Beam Only)
    # Slash variables removed
    game_state['ai_cyan_beam_active'] = False 
    game_state['ai_beam_angle'] = 0.0         
    game_state['ai_hitbox_timer'] = 0
    game_state['ai_special_attack_cooldown_timer'] = 0
    game_state['ai_last_direction'] = 'left'
    game_state['ai_attack_state'] = 'Idle' 
    
    # Update Tkinter controls
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

status_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_mode_text, 
    fg_color="yellow", 
    text_color='black', 
    font=ctk.CTkFont(family='Arial', size=14, weight='bold'),
    corner_radius=6
)
status_label.pack(fill='x', pady=(10, 5), padx=10)

# CustomTkinter label for special attack cooldown
cooldown_label = ctk.CTkLabel(
    control_panel_frame, 
    textvariable=tk_cooldown_text, 
    fg_color="green", 
    text_color='white', 
    font=ctk.CTkFont(family='Arial', size=12, weight='bold'),
    corner_radius=6
)
cooldown_label.pack(fill='x', pady=(5, 10), padx=10)


# Game Loop
running = True
clock = pygame.time.Clock()

while running:
    # Get Delta Time (dt) in milliseconds for consistent timing
    dt = clock.tick(60) 

    # 1. Process Pygame Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Check for SPACE key down for the special attack (Blue Cube)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_state['blue_active'] and not game_state['game_over']:
            do_special_attack()

        # Check for 'R' key down to restart the game
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_state['game_over']:
            print("Restarting Game...")
            reset_game_state()
            
    # 2. Process CustomTkinter Events 
    try:
        root.update()
    except Exception as e:
        running = False
        break
    
    # Check if the game is over before running core logic
    if game_state['game_over']:
        # Skip all game logic and just draw the game over screen
        screen.fill(WHITE)
        draw_health_bars()
        
        # Display Game Over Message
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

    
    # 3. Game Logic Update
    
    # Player Movement (Blue Cube) - NOW TRACKS LAST DIRECTION
    keys = pygame.key.get_pressed()
    current_move_speed = game_state.get('move_speed', MOVE_SPEED)

    if game_state['blue_active']:
        # Track movement delta
        dx, dy = 0, 0
        
        # Horizontal Movement: Last one processed is "most recent" direction
        if keys[pygame.K_LEFT]:
            dx -= current_move_speed
            game_state['last_direction'] = 'left' 
        if keys[pygame.K_RIGHT]:
            dx += current_move_speed
            game_state['last_direction'] = 'right' 
            
        # Vertical Movement: Last one processed is "most recent" direction
        if keys[pygame.K_UP]:
            dy -= current_move_speed
            game_state['last_direction'] = 'up'
        if keys[pygame.K_DOWN]:
            dy += current_move_speed
            game_state['last_direction'] = 'down'
            
        # Apply movement
        game_state['blue_x'] += dx
        game_state['blue_y'] += dy

        # Keep cubes within screen bounds
        game_state['blue_x'] = max(0, min(game_state['blue_x'], WIDTH - CUBE_SIZE))
        game_state['blue_y'] = max(0, min(game_state['blue_y'], HEIGHT - CUBE_SIZE))

    # --- TIMERS AND COOLDOWN MANAGEMENT ---
    
    # 1. Blue Cube Purple Hitbox Linger Timer
    if game_state['purple_hitbox_active']:
        game_state['hitbox_timer'] -= dt
        if game_state['hitbox_timer'] <= 0:
            game_state['purple_hitbox_active'] = False
            game_state['purple_hitbox_rect'] = None
    
    # 2. Blue Cube Special Attack Cooldown Timer
    if game_state['special_attack_cooldown_timer'] > 0:
        game_state['special_attack_cooldown_timer'] -= dt
        if game_state['special_attack_cooldown_timer'] < 0:
            game_state['special_attack_cooldown_timer'] = 0

    # 3. Red Cube Cyan Beam Linger Timer 
    if game_state['ai_cyan_beam_active']:
        game_state['ai_hitbox_timer'] -= dt
        # The beam angle is updated dynamically here to make it track the player
        if game_state['ai_hitbox_timer'] > 0:
            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            red_center_x = game_state['red_x'] + CUBE_SIZE / 2
            red_center_y = game_state['red_y'] + CUBE_SIZE / 2
            dx = target_x + CUBE_SIZE / 2 - red_center_x
            dy = target_y + CUBE_SIZE / 2 - red_center_y
            target_angle = math.atan2(dy, dx)
            
            # Simple angle update
            game_state['ai_beam_angle'] = target_angle
            
        else:
            game_state['ai_cyan_beam_active'] = False
            game_state['ai_beam_angle'] = 0.0

    # 4. Red Cube Special Attack Cooldown Timer
    if game_state['ai_special_attack_cooldown_timer'] > 0:
        game_state['ai_special_attack_cooldown_timer'] -= dt
        if game_state['ai_special_attack_cooldown_timer'] < 0:
            game_state['ai_special_attack_cooldown_timer'] = 0
            
    # 5. Update Tkinter Cooldown Label
    cooldown_time_s = game_state['special_attack_cooldown_timer'] / 1000
    
    if cooldown_time_s > 0:
        tk_cooldown_text.set(f"Slash: {cooldown_time_s:.1f}s CD")
        cooldown_label.configure(fg_color=PURPLE_HEX, text_color="white") 
    else:
        tk_cooldown_text.set("Slash: READY (SPACE)")
        cooldown_label.configure(fg_color="green", text_color="white") 
    
    # --- END TIMERS AND COOLDOWN MANAGEMENT ---
    
    
    # --- RED CUBE MOVEMENT / AI LOGIC (STATE MACHINE) ---
    if game_state['red_active']:
        
        target_x, target_y = game_state['blue_x'], game_state['blue_y']
        distance_to_player = calculate_distance(game_state['red_x'], game_state['red_y'], target_x, target_y)


        # --- AI BEAM ATTACK LOGIC (UNIFIED) ---
        
        if game_state['ai_attack_state'] == 'Idle':
            # Priority Check: AI Special Attack - Initiate Windup
            if check_ai_special_attack_trigger(distance_to_player) and game_state['charge_state'] == 'Idle':
                initiate_ai_special_attack_windup()
        
        elif game_state['ai_attack_state'] == 'SpecialWindup': # Unified Windup state for Beam
            # Cube does not move during windup
            game_state['flash_timer'] -= dt
            
            if game_state['flash_timer'] <= 0:
                game_state['flash_count'] += 1
                
                # Check for the completion of the 4th (Cyan) flash cycle
                # This happens at flash_count = 7 (after 3 black blinks = 6 state changes)
                if game_state['flash_count'] > (AI_SLASH_FLASH_CYCLES * 2) + 1:
                    # Windup is complete, execute the beam attack
                    execute_ai_special_attack()
                else:
                    # Continue flashing (Red, Black, Red, Black, Red, Black, Cyan)
                    game_state['flash_timer'] = AI_FLASH_DURATION_MS
            
            # The angle is dynamically updated during windup to home onto the player
            target_x, target_y = game_state['blue_x'], game_state['blue_y']
            red_center_x = game_state['red_x'] + CUBE_SIZE / 2
            red_center_y = game_state['red_y'] + CUBE_SIZE / 2
            dx = target_x + CUBE_SIZE / 2 - red_center_x
            dy = target_y + CUBE_SIZE / 2 - red_center_y
            game_state['ai_beam_angle'] = math.atan2(dy, dx) # Update angle
            
            game_state['red_cube_mode'] = "Beam (Windup)" 
        
        # --- END AI BEAM ATTACK LOGIC ---
        

        # --- CHARGE ATTACK LOGIC (Movement Control) ---
        # The Charge Attack logic is only processed if the AI is not in the middle of a special attack Windup
        if game_state['ai_attack_state'] == 'Idle':
            
            if game_state['charge_state'] == 'Idle':
                # 3.1. Idle State: Check for random charge initiation
                
                # Initiate Windup? 
                if random.random() < CHARGE_INITIATE_CHANCE:
                    game_state['charge_state'] = 'Windup'
                    game_state['flash_count'] = 0
                    
                    # Start timer for the first flash (Red state duration)
                    game_state['flash_timer'] = FLASH_DURATION_MS 
                    
                    # LOCK TARGET DIRECTION (calculate normalized vector)
                    dx = target_x - game_state['red_x']
                    dy = target_y - game_state['red_y']
                    angle = math.atan2(dy, dx)
                    game_state['charge_dx'] = math.cos(angle)
                    game_state['charge_dy'] = math.sin(angle)
                    
                    game_state['red_cube_mode'] = "Charge (Windup)" # Display windup mode
                
                else:
                    # Normal AI movement (Maintain, Attack, Retreat, etc.)
                    # Pass red_health to the AI decision function
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
                # 3.2. Windup State: Flashing 
                game_state['flash_timer'] -= dt
                
                if game_state['flash_timer'] <= 0:
                    game_state['flash_count'] += 1
                    
                    # Check if flashing is complete (2 black flashes = 5 state changes total)
                    if game_state['flash_count'] > (CHARGE_FLASH_CYCLES * 2):
                        game_state['charge_state'] = 'Charging'
                    else:
                        game_state['flash_timer'] = FLASH_DURATION_MS
                
                game_state['red_cube_mode'] = "Charge (Windup)"
                
            
            elif game_state['charge_state'] == 'Charging':
                # 3.3. Charging State: Locked Movement
                game_state['red_cube_mode'] = "Charge"
                
                # Apply movement using the locked vector and charge speed
                move_x = game_state['charge_dx'] * CHARGE_SPEED
                move_y = game_state['charge_dy'] * CHARGE_SPEED

                new_x = game_state['red_x'] + move_x
                new_y = game_state['red_y'] + move_y
                
                # Check for screen boundaries (stops charge but does not reverse direction)
                hit_boundary = False
                
                if new_x <= 0 or new_x >= WIDTH - CUBE_SIZE:
                    hit_boundary = True
                    new_x = max(0, min(new_x, WIDTH - CUBE_SIZE))
                
                if new_y <= 0 or new_y >= HEIGHT - CUBE_SIZE:
                    hit_boundary = True
                    new_y = max(0, min(new_y, HEIGHT - CUBE_SIZE))

                game_state['red_x'] = new_x
                game_state['red_y'] = new_y

                # If either boundary is hit, transition to ENDLAG
                if hit_boundary:
                    game_state['charge_state'] = 'Endlag' 
                    game_state['endlag_timer'] = ENDLAG_DURATION_MS # Start the 2-second timer
                    game_state['red_cube_mode'] = "Charge (Endlag)" 

            
            elif game_state['charge_state'] == 'Endlag':
                # 3.4. Endlag State: Stunned/Cooldown
                game_state['endlag_timer'] -= dt # Decrease timer by elapsed time
                
                # The cube does not move in this state
                
                if game_state['endlag_timer'] <= 0:
                    game_state['charge_state'] = 'Idle'
                    game_state['red_cube_mode'] = "Maintain" # Reset standard AI mode

    # --- END RED CUBE MOVEMENT / AI LOGIC ---

    # Update CustomTkinter label with the current AI mode
    tk_mode_text.set(f"Red Cube Mode: {game_state['red_cube_mode']}")


    # --- COLLISION DETECTION (Damage Application) ---

    # 1. Red Cube Charge Attack (Contact Damage to Blue Cube)
    # Player only takes damage when the Red Cube is actively charging.
    is_charging = game_state['charge_state'] == 'Charging'
    
    if is_charging:
        # Check for collision between Blue and Red Cubes
        if (game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
            game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
            game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
            game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):
        
            if game_state['blue_active'] and game_state['blue_health'] > 0:
                game_state['blue_health'] -= CHARGE_ATTACK_DAMAGE # Use a dedicated charge damage value
                print(f"Red Cube Charge hit! Damage: {CHARGE_ATTACK_DAMAGE}. Blue Health: {max(0, game_state['blue_health'])}")


    # 2. Blue Cube Special Attack (Purple Hitbox Damage to Red Cube)
    # Damage is handled on cast inside do_special_attack().

    # 3. Red Cube Beam Attack (Cyan Beam Damage to Blue Cube)
    # Damage is handled on execution inside execute_ai_special_attack().

    # --- END COLLISION DETECTION ---

    # Check for game over
    if game_state['blue_health'] <= 0:
        if game_state['blue_active']:
            print("Blue Cube Defeated!")
        game_state['blue_active'] = False
        game_state['game_over'] = True
        
    if game_state['red_health'] <= 0:
        if game_state['red_active']:
            print("Red Cube Defeated!")
        game_state['red_active'] = False
        game_state['game_over'] = True
        
    # 4. Draw everything
    screen.fill(WHITE)
    draw_cube(game_state['blue_x'], game_state['blue_y'], BLUE)
    draw_health_bars()
    
    # Draw the lingering blue cube purple hitbox first (if active)
    if game_state['purple_hitbox_active'] and game_state['purple_hitbox_rect']:
        pygame.draw.rect(screen, PURPLE_TUPLE, game_state['purple_hitbox_rect'])

    # Red cube yellow slash hitbox drawing logic removed
        
    # Draw the lingering red cube cyan beam (if active)
    if game_state['ai_cyan_beam_active']:
        beam_surface, beam_rect = get_ai_beam_rect()
        screen.blit(beam_surface, beam_rect)
    
    if game_state['red_active']:
        # Use the dynamic color function here
        red_cube_color = get_red_cube_color(game_state)
        draw_cube(game_state['red_x'], game_state['red_y'], red_cube_color)
    
    
    pygame.display.flip()

pygame.quit()
sys.exit()