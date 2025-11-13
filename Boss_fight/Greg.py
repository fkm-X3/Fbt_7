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
YELLOW_RGB = (255, 255, 0)
YELLOW_HEX = "#FFFF00"
# Special Attack Colors (MUST be defined for both Pygame and CustomTkinter)
PURPLE_TUPLE = (128, 0, 128) # For Pygame drawing
PURPLE_HEX = "#800080"      # For CustomTkinter styling

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

# --- AI BASIC ATTACK CONSTANTS (New for Contact Damage) ---
AI_BASIC_ATTACK_RANGE = 70      # The distance at which the AI initiates a basic attack
AI_BASIC_WINDUP_MS = 300        # Black flash duration before attack (The "tell")
AI_BASIC_ACTIVE_MS = 100        # Duration the attack hitbox is active
AI_BASIC_COOLDOWN_MS = 500      # Cooldown after an active attack
# ---------------------------------

# --- CHARGE ATTACK CONSTANTS ---
CHARGE_SPEED = 15              # Speed during charge
CHARGE_INITIATE_CHANCE = 0.001 # Chance per frame to start windup (0.1%)
CHARGE_FLASH_CYCLES = 2        # Number of times to flash black (RED->BLACK->RED->BLACK->RED)
FLASH_DURATION_MS = 200        # Duration of each color state change (milliseconds)
ENDLAG_DURATION_MS = 2000      # 2 seconds of cooldown after charge
# -------------------------------

# Player Attack Damage
ATTACK_DAMAGE = 20

# --- SPECIAL ATTACK CONSTANTS ---
SPECIAL_ATTACK_DAMAGE = 25
HITBOX_DURATION_MS = 500       # 0.5 seconds (Visual linger)
SPECIAL_ATTACK_COOLDOWN_MS = 3000 # 3.0 seconds
# --------------------------------

# Player States
blue_active = True
red_active = True

# Player Health
blue_health = 100
red_health = 100

# AI State Definitions
ATTACK_RANGE = 100
DEFENSIVE_RANGE = 400           # Original range, now overridden by health check
MAINTAIN_RANGE_MIN = 150
MAINTAIN_RANGE_MAX = 350        # Used as the "far away" condition for retreat
PLAYER_ATTACK_RANGE = CUBE_SIZE * 1.5 # (Original basic attack range, now unused for SPACE)
RETREAT_HEALTH_THRESHOLD = 25   # Red cube retreats only below this HP

RED_CUBE_MODE = "Maintain"      # Initial standard mode

# Font
font = pygame.font.Font(None, 36)

# Game state variables (shared between Pygame and Tkinter)
game_state = {
    'blue_active': blue_active,
    'red_active': red_active,
    'blue_health': blue_health,
    'red_health': red_health,
    'blue_x': blue_x,
    'blue_y': blue_y,
    'red_x': red_x,           
    'red_y': red_y,          
    'attack_damage': ATTACK_DAMAGE, 
    'move_speed': MOVE_SPEED,       
    'game_over': False,
    'red_cube_mode': RED_CUBE_MODE, # AI Mode (e.g., Maintain, Charge)
    # --- CHARGE STATE VARIABLES ---
    'charge_state': 'Idle',       # 'Idle', 'Windup', 'Charging', 'Endlag'
    'flash_timer': 0,             # Timer for managing flash duration
    'flash_count': 0,             # How many flashes have occurred
    'charge_dx': 0,               # Locked X-direction for charge
    'charge_dy': 0,               # Locked Y-direction for charge
    'endlag_timer': 0.0,          # Timer for the 2-second cooldown after charge

    # --- NEW BASIC ATTACK STATE VARIABLES (for contact damage) ---
    'ai_basic_attack_state': 'Ready', # 'Ready', 'Windup', 'Active', 'Cooldown'
    'ai_basic_attack_timer': 0.0,

    # --- NEW SPECIAL ATTACK STATE VARIABLES ---
    'purple_hitbox_active': False,
    'purple_hitbox_rect': None,    # Stores the pygame.Rect object for drawing
    'hitbox_timer': 0,             # Tracks remaining time for the hitbox to linger
    'last_direction': 'right',     # Tracks the direction blue was moving
    'special_attack_cooldown_timer': 0, # Tracks remaining time for the 3s cooldown
}


# Function to draw a cube
def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

# Function to determine the Red Cube's display color (for flashing)
def get_red_cube_color(state):
    """Determines the color of the Red Cube based on its charge state and basic attack state."""
    
    # Priority 1: Endlag (Stun) - Always BLACK
    if state['charge_state'] == 'Endlag':
        return BLACK
    
    # Priority 2: Charge Windup - Flashing BLACK/RED
    if state['charge_state'] == 'Windup':
        # Flash black on odd flash counts
        if state['flash_count'] % 2 != 0: 
             return BLACK
        return RED # Otherwise show RED during charge windup
        
    # Priority 3: Basic Attack Windup (The new pre-attack flash)
    if state['ai_basic_attack_state'] == 'Windup':
        return BLACK # Flash black during windup duration

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

    # Apply slight randomness (jitter)
    move_x += random.uniform(-1, 1) * 0.5
    move_y += random.uniform(-1, 1) * 0.5

    # Apply movement and keep within bounds
    new_x = max(0, min(current_x + move_x, WIDTH - CUBE_SIZE))
    new_y = max(0, min(current_y + move_y, HEIGHT - CUBE_SIZE))

    return new_x, new_y, mode
# --- END AI MOVEMENT LOGIC (STANDARD MODES ONLY) ---

# --- SPECIAL ATTACK LOGIC ---

def check_hitbox_collision(hitbox_rect, red_x, red_y):
    """Checks if the red cube is inside the generated hitbox."""
    if not hitbox_rect:
        return False
    
    # Red cube's Rect
    red_rect = pygame.Rect(red_x, red_y, CUBE_SIZE, CUBE_SIZE)
    
    return hitbox_rect.colliderect(red_rect)

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
        print(f"Blue Cube SPECIAL ATTACK hit! Damage: {SPECIAL_ATTACK_DAMAGE}. Red Health: {max(0, game_state['red_health'])}")
    
    # 3. Spawn the Hitbox (for visual linger effect)
    game_state['purple_hitbox_active'] = True
    game_state['purple_hitbox_rect'] = hitbox_rect
    game_state['hitbox_timer'] = HITBOX_DURATION_MS
    
    # 4. Start Cooldown
    game_state['special_attack_cooldown_timer'] = SPECIAL_ATTACK_COOLDOWN_MS

# --- END SPECIAL ATTACK LOGIC ---


# CustomTkinter Setup
root = ctk.CTk()
root.title("Cube Combat Control Panel")

tk_mode_text = ctk.StringVar(value=f"Red Cube Mode: {game_state['red_cube_mode']}")
tk_cooldown_text = ctk.StringVar(value="Special Attack: READY (SPACE)")

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
game_over = False

while running:
    # Get Delta Time (dt) in milliseconds for consistent timing
    dt = clock.tick(60) 

    # 1. Process Pygame Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # New: Check for SPACE key down for the special attack
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and game_state['blue_active']:
            do_special_attack()
            
    # 2. Process CustomTkinter Events 
    try:
        root.update()
    except Exception as e:
        # print(f"Tkinter/CustomTkinter error: {e}") # Debugging
        running = False
        break
    
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
    
    # 1. Purple Hitbox Linger Timer
    if game_state['purple_hitbox_active']:
        game_state['hitbox_timer'] -= dt
        if game_state['hitbox_timer'] <= 0:
            game_state['purple_hitbox_active'] = False
            game_state['purple_hitbox_rect'] = None
    
    # 2. Special Attack Cooldown Timer
    if game_state['special_attack_cooldown_timer'] > 0:
        game_state['special_attack_cooldown_timer'] -= dt
        if game_state['special_attack_cooldown_timer'] < 0:
            game_state['special_attack_cooldown_timer'] = 0
            
    # 3. Update Tkinter Cooldown Label
    cooldown_time_s = game_state['special_attack_cooldown_timer'] / 1000
    
    if cooldown_time_s > 0:
        tk_cooldown_text.set(f"Special Attack: {cooldown_time_s:.1f}s CD")
        cooldown_label.configure(fg_color=PURPLE_HEX, text_color="white") 
    else:
        tk_cooldown_text.set("Special Attack: READY (SPACE)")
        cooldown_label.configure(fg_color="green", text_color="white") # Green when ready
    
    # --- END TIMERS AND COOLDOWN MANAGEMENT ---
    
    
    # --- RED CUBE MOVEMENT / AI LOGIC (STATE MACHINE) ---
    if game_state['red_active'] and not game_state['game_over']:
        
        target_x, target_y = game_state['blue_x'], game_state['blue_y']

        # --- AI BASIC ATTACK STATE MACHINE (New) ---
        # Basic attack is paused during the 2-second Charge Endlag state
        if game_state['charge_state'] != 'Endlag':
            
            # Distance to player (used for both movement and attack initiation)
            distance_to_player = calculate_distance(game_state['red_x'], game_state['red_y'], game_state['blue_x'], game_state['blue_y'])
            
            if game_state['ai_basic_attack_state'] == 'Ready':
                # Initiate basic attack windup if close enough
                if distance_to_player < AI_BASIC_ATTACK_RANGE:
                    game_state['ai_basic_attack_state'] = 'Windup'
                    game_state['ai_basic_attack_timer'] = AI_BASIC_WINDUP_MS
                    
            elif game_state['ai_basic_attack_state'] == 'Windup':
                game_state['ai_basic_attack_timer'] -= dt
                if game_state['ai_basic_attack_timer'] <= 0:
                    # After windup, enter the brief active hit window
                    game_state['ai_basic_attack_state'] = 'Active'
                    game_state['ai_basic_attack_timer'] = AI_BASIC_ACTIVE_MS
                    
            elif game_state['ai_basic_attack_state'] == 'Active':
                game_state['ai_basic_attack_timer'] -= dt
                # Collision check for damage is performed below in the main collision block
                if game_state['ai_basic_attack_timer'] <= 0:
                    # After hit window, enter cooldown
                    game_state['ai_basic_attack_state'] = 'Cooldown'
                    game_state['ai_basic_attack_timer'] = AI_BASIC_COOLDOWN_MS
                    
            elif game_state['ai_basic_attack_state'] == 'Cooldown':
                game_state['ai_basic_attack_timer'] -= dt
                if game_state['ai_basic_attack_timer'] <= 0:
                    game_state['ai_basic_attack_state'] = 'Ready'
        
        # --- CHARGE ATTACK LOGIC ---
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


    # Collision Detection (Red Cube attacking Blue Cube)
    # This is the physical contact damage between the two cubes
    
    # NEW LOGIC: Damage only applies if the AI's basic attack is in the 'Active' state, 
    # AND the AI is not stunned (Endlag), allowing for punishes.
    can_ai_deal_contact_damage = (
        game_state['ai_basic_attack_state'] == 'Active' and 
        game_state['charge_state'] != 'Endlag'
    )
    
    if (can_ai_deal_contact_damage and
        game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
        game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
        game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
        game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):
        
        # Only apply damage if blue cube is active and health > 0
        if game_state['blue_active'] and game_state['blue_health'] > 0:
            # Using the basic attack damage for contact
            game_state['blue_health'] -= game_state.get('attack_damage', ATTACK_DAMAGE) 
            print("Red Cube Attacks!")


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
    
    # Draw the lingering purple hitbox first (if active)
    if game_state['purple_hitbox_active'] and game_state['purple_hitbox_rect']:
        # Draw the purple rect using the Pygame tuple
        pygame.draw.rect(screen, PURPLE_TUPLE, game_state['purple_hitbox_rect'])
    
    if game_state['red_active']:
        # Use the dynamic color function here
        red_cube_color = get_red_cube_color(game_state)
        draw_cube(game_state['red_x'], game_state['red_y'], red_cube_color)
    
    if game_state['game_over']:
        # Display Game Over Message
        if game_state['blue_health'] <= 0:
            message = "Red Cube Wins!"
            color = RED
        else:
            message = "Blue Cube Wins!"
            color = BLUE
            
        game_over_text = font.render(message, True, color)
        text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(game_over_text, text_rect)
    
    pygame.display.flip()

pygame.quit()
sys.exit()