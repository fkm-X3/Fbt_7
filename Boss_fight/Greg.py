import pygame
from pygame import key

pygame.init()

screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Greg Phase 1 Boss Fight")

running = True
clock = pygame.time.Clock()
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
font = pygame.font.SysFont("Arial", 24)

boss_health = 100
boss_max_health = 100
boss_health_bar_length = 400
boss_health_bar_height = 30
boss_health_bar_x = (screen_width - boss_health_bar_length) // 2
boss_health_bar_y = 20

Player_health = 20
Player_max_health = 20
Player_movement_speed = 5

def draw_boss_health_bar(health):
    health_ratio = health / boss_max_health
    pygame.draw.rect(screen, BLACK, (boss_health_bar_x - 2, boss_health_bar_y - 2, boss_health_bar_length + 4, boss_health_bar_height + 4))
    pygame.draw.rect(screen, (255, 0, 0), (boss_health_bar_x, boss_health_bar_y, boss_health_bar_length, boss_health_bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (boss_health_bar_x, boss_health_bar_y, boss_health_bar_length * health_ratio, boss_health_bar_height))

class Player(pygame.sprite.Sprite):
    def __init__(self, images, x, y):
        super().__init__()
        self.image = pygame.image.load(images).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.last_direction = "idle"  # Track last direction
        self.direction_images = {
            "idle": "images/Player/Player_Idle.png",
            "left": "images/Player/Player_left.png",
            "right": "images/Player/Player_right.png",
            "up": "images/Player/Player_up.png",
            "down": "images/Player/Player_down.png"
        }

    def update(self):
        moved = False
        if key[pygame.K_LEFT] or key[pygame.K_a]:
            self.rect.x -= Player_movement_speed
            self.last_direction = "left"
            moved = True
        if key[pygame.K_RIGHT] or key[pygame.K_d]:
            self.rect.x += Player_movement_speed
            self.last_direction = "right"
            moved = True
        if key[pygame.K_UP] or key[pygame.K_w]:
            self.rect.y -= Player_movement_speed
            self.last_direction = "up"
            moved = True
        if key[pygame.K_DOWN] or key[pygame.K_s]:
            self.rect.y += Player_movement_speed
            self.last_direction = "down"
            moved = True
        
        # Update sprite based on last direction
        image_path = self.direction_images[self.last_direction]
        self.image = pygame.image.load(image_path).convert_alpha()

player_sprite = Player("images/Player/Player_Idle.png", screen_width // 2, screen_height - 100)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(WHITE)
    draw_boss_health_bar(boss_health)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
