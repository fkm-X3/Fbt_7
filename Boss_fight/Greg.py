import pygame
import random
import tkinter as tk
from tkinter import ttk
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cube Combat")

# Colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW_RGB = (255, 255, 0) # Pygame Color
YELLOW_HEX = "#FFFF00"      # Tkinter Color

# Cube Size
CUBE_SIZE = 50

# Player Positions (Initial)
blue_x = 20  # Left side
blue_y = HEIGHT // 2 - CUBE_SIZE // 2
red_x = WIDTH - CUBE_SIZE - 20  # Right side
red_y = HEIGHT // 2 - CUBE_SIZE // 2

# Player Movement Speed
MOVE_SPEED = 5
# AI Movement Speed (Slightly slower for balance)
AI_MOVE_SPEED = 3

# Player States
blue_active = True
red_active = True

# Player Health
blue_health = 100
red_health = 100

# Player Attack Damage
ATTACK_DAMAGE = 20

# AI State Definitions
# These distances define the boundaries for the Red Cube's behavior
ATTACK_RANGE = 100  # Go for the kill if distance is less than this
DEFENSIVE_RANGE = 400 # Run away if distance is greater than this
CLOSING_RANGE = 250   # Stay out of a hypothetical medium attack range (between 100 and 250)
RED_CUBE_MODE = "Closing Distance" # Initial mode

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
    'red_cube_mode': RED_CUBE_MODE # AI Mode
}


# Function to draw a cube
def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

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


# --- AI MOVEMENT LOGIC ---
def calculate_distance(x1, y1, x2, y2):
    """Calculates the Euclidean distance between the centers of two cubes."""
    center1_x, center1_y = x1 + CUBE_SIZE / 2, y1 + CUBE_SIZE / 2
    center2_x, center2_y = x2 + CUBE_SIZE / 2, y2 + CUBE_SIZE / 2
    return math.hypot(center2_x - center1_x, center2_y - center1_y)

def move_ai(mode, target_x, target_y, current_x, current_y, speed):
    """Calculates the new position based on the AI mode."""
    dx, dy = 0, 0
    distance = calculate_distance(current_x, current_y, target_x, target_y)

    # State Transition Logic (simple distance checks)
    if distance < ATTACK_RANGE:
        mode = "Attack"
    elif distance > DEFENSIVE_RANGE:
        mode = "Defensive"
    elif distance > CLOSING_RANGE:
        mode = "Closing Distance" # Move slightly closer
    elif distance < CLOSING_RANGE and distance > ATTACK_RANGE:
         mode = "Closing Distance" # Move slightly away to maintain distance
    else:
        # If in perfect range, just idle slightly
        mode = "Closing Distance" 

    
    # Movement Logic based on Mode
    if mode == "Attack":
        # Move directly toward the target
        dx = target_x - current_x
        dy = target_y - current_y

    elif mode == "Defensive":
        # Move directly away from the target
        dx = current_x - target_x
        dy = current_y - target_y

    elif mode == "Closing Distance":
        # Try to maintain a comfortable distance (CLOSING_RANGE)
        if distance > CLOSING_RANGE:
            # Move towards the target to close the gap
            dx = target_x - current_x
            dy = target_y - current_y
        else:
            # Move slightly away to maintain the distance (Jitter)
            dx = current_x - target_x
            dy = current_y - target_y
            
    # Normalize movement vector to ensure consistent speed
    if dx != 0 or dy != 0:
        angle = math.atan2(dy, dx)
        move_x = speed * math.cos(angle)
        move_y = speed * math.sin(angle)
        
        # Apply slight randomness to avoid perfect prediction
        move_x += random.uniform(-1, 1) * 0.5
        move_y += random.uniform(-1, 1) * 0.5
    else:
        move_x, move_y = random.uniform(-1, 1), random.uniform(-1, 1)

    # Apply movement and keep within bounds
    new_x = max(0, min(current_x + move_x, WIDTH - CUBE_SIZE))
    new_y = max(0, min(current_y + move_y, HEIGHT - CUBE_SIZE))

    return new_x, new_y, mode
# --- END AI MOVEMENT LOGIC ---


# Tkinter Setup
root = tk.Tk()
root.title("Cube Combat Control Panel")

# The tk.StringVar must be initialized AFTER tk.Tk()
tk_mode_text = tk.StringVar(value=f"Red Cube Mode: {game_state['red_cube_mode']}")

# Create a frame to hold the control panel widgets
control_panel_frame = tk.Frame(root)
control_panel_frame.pack(padx=10, pady=10)

# Add control panel buttons
def toggle_blue_active():
    game_state['blue_active'] = not game_state['blue_active']
    print(f"Blue Active: {game_state['blue_active']}")

def increase_attack():
    game_state['attack_damage'] = game_state.get('attack_damage', ATTACK_DAMAGE) + 5
    print(f"Attack Damage: {game_state['attack_damage']}")

def decrease_speed():
    game_state['move_speed'] = max(1, game_state.get('move_speed', MOVE_SPEED) - 1)
    print(f"Move Speed: {game_state['move_speed']}")

blue_button = tk.Button(control_panel_frame, text="Toggle Blue Active", command=toggle_blue_active)
blue_button.pack(fill='x', pady=2)

attack_button = tk.Button(control_panel_frame, text="Increase Attack Damage", command=increase_attack)
attack_button.pack(fill='x', pady=2)

speed_button = tk.Button(control_panel_frame, text="Decrease Move Speed", command=decrease_speed)
speed_button.pack(fill='x', pady=2)

# TKINTER DEBUGGING LABEL
# --- FIX: Changed bg=YELLOW to bg=YELLOW_HEX ---
status_label = tk.Label(control_panel_frame, textvariable=tk_mode_text, bg=YELLOW_HEX, fg='black', font=('Arial', 10, 'bold'))
status_label.pack(fill='x', pady=5)


# Game Loop
running = True
clock = pygame.time.Clock()
game_over = False

while running:
    # 1. Process Pygame Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # 2. Process Tkinter Events 
    try:
        root.update()
    except tk.TclError:
        running = False
        break
    
    # 3. Game Logic Update
    
    # Player Movement (Blue Cube)
    keys = pygame.key.get_pressed()
    
    current_move_speed = game_state.get('move_speed', MOVE_SPEED)

    if game_state['blue_active']:
        if keys[pygame.K_LEFT]:
            game_state['blue_x'] -= current_move_speed
        if keys[pygame.K_RIGHT]:
            game_state['blue_x'] += current_move_speed
        if keys[pygame.K_UP]:
            game_state['blue_y'] -= current_move_speed
        if keys[pygame.K_DOWN]:
            game_state['blue_y'] += current_move_speed

        # Keep cubes within screen bounds
        game_state['blue_x'] = max(0, min(game_state['blue_x'], WIDTH - CUBE_SIZE))
        game_state['blue_y'] = max(0, min(game_state['blue_y'], HEIGHT - CUBE_SIZE))

    # Player Attack (Blue Cube)
    current_attack_damage = game_state.get('attack_damage', ATTACK_DAMAGE)

    if keys[pygame.K_SPACE]:
        if game_state['blue_active']:
            game_state['red_health'] -= current_attack_damage
            print("Blue Cube Attacks!")

    # Red Cube Movement (AI Controlled)
    if game_state['red_active'] and not game_state['game_over']:
        
        target_x, target_y = game_state['blue_x'], game_state['blue_y']
        
        # Calculate new position and mode using the AI function
        new_red_x, new_red_y, new_mode = move_ai(
            game_state['red_cube_mode'], 
            target_x, 
            target_y, 
            game_state['red_x'], 
            game_state['red_y'], 
            AI_MOVE_SPEED
        )
        
        game_state['red_x'] = new_red_x
        game_state['red_y'] = new_red_y
        game_state['red_cube_mode'] = new_mode
        
        # Update Tkinter label with the current AI mode
        tk_mode_text.set(f"Red Cube Mode: {new_mode}")


    # Collision Detection
    if (game_state['blue_x'] < game_state['red_x'] + CUBE_SIZE and
        game_state['blue_x'] + CUBE_SIZE > game_state['red_x'] and
        game_state['blue_y'] < game_state['red_y'] + CUBE_SIZE and
        game_state['blue_y'] + CUBE_SIZE > game_state['red_y']):
        
        # Red cube attacks blue cube upon collision
        game_state['blue_health'] -= ATTACK_DAMAGE 
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
    
    if game_state['red_active']:
        draw_cube(game_state['red_x'], game_state['red_y'], RED)
    
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
    clock.tick(60)

pygame.quit()
sys.exit()