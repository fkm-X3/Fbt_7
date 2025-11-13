import pygame
import random
import sys

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

# Cube Size
CUBE_SIZE = 50

# Player Positions (Initial)
blue_x = 20  # Left side
blue_y = HEIGHT // 2 - CUBE_SIZE // 2
red_x = WIDTH - CUBE_SIZE - 20  # Right side
red_y = HEIGHT // 2 - CUBE_SIZE // 2

# Player Movement Speed
MOVE_SPEED = 5

# Player States
blue_active = True
red_active = True

# Player Health
blue_health = 100
red_health = 100

# Player Attack Damage
ATTACK_DAMAGE = 20

# Font
font = pygame.font.Font(None, 36)

# Function to draw a cube
def draw_cube(x, y, color):
    pygame.draw.rect(screen, color, (x, y, CUBE_SIZE, CUBE_SIZE))

# Function to draw health bars
def draw_health_bars(blue_health, red_health):
    blue_health_bar = int(WIDTH * (blue_health / 100))
    red_health_bar = int(WIDTH * (red_health / 100))
    
    blue_health_rect = pygame.Rect(WIDTH - 100, 10, blue_health_bar, 20)
    red_health_rect = pygame.Rect(10, 10, red_health_bar, 20)

    pygame.draw.rect(screen, BLUE, blue_health_rect)
    pygame.draw.rect(screen, RED, red_health_rect)
    
    # Display health values
    blue_health_text = font.render(str(blue_health) + "%", True, WHITE)
    red_health_text = font.render(str(red_health) + "%", True, WHITE)
    screen.blit(blue_health_text, (WIDTH - 120, 10))
    screen.blit(red_health_text, (20, 10))

# Game Loop
running = True
clock = pygame.time.Clock()
game_over = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
    # Player Movement (Blue Cube)
    keys = pygame.key.get_pressed()
    if blue_active:
        if keys[pygame.K_LEFT]:
            blue_x -= MOVE_SPEED
        if keys[pygame.K_RIGHT]:
            blue_x += MOVE_SPEED
        if keys[pygame.K_UP]:
            blue_y -= MOVE_SPEED
        if keys[pygame.K_DOWN]:
            blue_y += MOVE_SPEED

        # Keep cubes within screen bounds
        blue_x = max(0, min(blue_x, WIDTH - CUBE_SIZE))
        blue_y = max(0, min(blue_y, HEIGHT - CUBE_SIZE))

    # Player Attack (Blue Cube)
    if keys[pygame.K_SPACE]:
        if blue_active:
            # Simple attack -  just damage the red cube
            red_health -= ATTACK_DAMAGE
            print("Blue Cube Attacks!")

    # Red Cube Movement (Basic Random Movement)
    if red_active:
        red_x += random.randint(-2, 2)
        red_y += random.randint(-2, 2)
        red_x = max(0, min(red_x, WIDTH - CUBE_SIZE))
        red_y = max(0, min(red_y, HEIGHT - CUBE_SIZE))

    # Collision Detection
    if (blue_x < red_x + CUBE_SIZE and
        blue_x + CUBE_SIZE > red_x and
        blue_y < red_y + CUBE_SIZE and
        blue_y + CUBE_SIZE > red_y):
        # Collision!  Reduce health
        blue_health -= ATTACK_DAMAGE
        print("Red Cube Attacks!")

    # Check for game over
    if blue_health <= 0:
        print("Blue Cube Defeated!")
        blue_active = False
        game_over = True
    if red_health <= 0:
        print("Red Cube Defeated!")
        red_active = False
        game_over = True

    # Draw everything
    screen.fill(WHITE)
    draw_cube(blue_x, blue_y, BLUE)
    draw_health_bars(blue_health, red_health)
    draw_cube(red_x, red_y, RED)

    if not game_over:
        pygame.display.flip()
    clock.tick(60)  # Limit frame rate to 60 FPS

pygame.quit()
sys.exit()
