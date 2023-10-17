import pygame
import button
from constants import *
from sprites import *

pygame.init()


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter")

# set framerate
clock = pygame.time.Clock()
FPS = 60

level = 1
start_game = False


# define Player.player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


# define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# define font
font = pygame.font.SysFont("Futura", 30)


def draw_text(text, font: pygame.font.SysFont, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


start_img = pygame.image.load("img/start_btn.png").convert_alpha()
exit_img = pygame.image.load("img/exit_btn.png").convert_alpha()
restart_img = pygame.image.load("img/restart_btn.png").convert_alpha()

# create buttons
start_button = button.Button(
    SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1
)
exit_button = button.Button(
    SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1
)
restart_button = button.Button(
    SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2
)

Scene.current = Level(level)

run = True
while run:
    clock.tick(FPS)

    if start_game == False:
        # draw menu
        screen.fill(BG)
        # add buttons
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
    else:
        # update background
        screen.fill(BG)
        # draw world map
        Scene.current.draw(screen)
        # # show Player.player health
        # health_bar.draw(Player.player.health)
        # show ammo
        draw_text("AMMO: ", font, WHITE, 10, 35)

        # update Player.player actions
        if Player.player.alive:
            if Player.player.in_air:
                Player.player.jump()
            level_complete = Player.player.move()
            # check if Player.player has completed the level
            if level_complete:
                level += 1
                if level <= MAX_LEVELS:
                    Scene.current = Level(level)
        else:
            if restart_button.draw(screen):
                Scene.current.reset()

    for event in pygame.event.get():
        # quit game
        if event.type == pygame.QUIT:
            run = False
        # keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                Player.player.x_speed = -10
            if event.key == pygame.K_d:
                Player.player.x_speed = 10
            if event.key == pygame.K_w:
                Player.player.jump()
            if event.key == pygame.K_ESCAPE:
                run = False

        # keyboard button released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                Player.player.x_speed = 0
            if event.key == pygame.K_d:
                Player.player.x_speed = 0

    pygame.display.update()

pygame.quit()
