import pygame
import os
import random
import csv
import button
from constants import *
from sprites import *

pygame.init()


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter")

# set framerate
clock = pygame.time.Clock()
FPS = 60

# define game variables
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False


# define player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


# load images
# button images
start_img = pygame.image.load("img/start_btn.png").convert_alpha()
exit_img = pygame.image.load("img/exit_btn.png").convert_alpha()
restart_img = pygame.image.load("img/restart_btn.png").convert_alpha()
# background
pine1_img = pygame.image.load("img/Background/pine1.png").convert_alpha()
pine2_img = pygame.image.load("img/Background/pine2.png").convert_alpha()
mountain_img = pygame.image.load("img/Background/mountain.png").convert_alpha()
sky_img = pygame.image.load("img/Background/sky_cloud.png").convert_alpha()
# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f"img/Tile/{x}.png")
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
# bullet
bullet_img = pygame.image.load("img/icons/bullet.png").convert_alpha()
# grenade
grenade_img = pygame.image.load("img/icons/grenade.png").convert_alpha()
# pick up boxes
health_box_img = pygame.image.load("img/icons/health_box.png").convert_alpha()
ammo_box_img = pygame.image.load("img/icons/ammo_box.png").convert_alpha()
grenade_box_img = pygame.image.load("img/icons/grenade_box.png").convert_alpha()
item_boxes = {
    "Health": health_box_img,
    "Ammo": ammo_box_img,
    "Grenade": grenade_box_img,
}


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(
            mountain_img,
            (
                (x * width) - bg_scroll * 0.6,
                SCREEN_HEIGHT - mountain_img.get_height() - 300,
            ),
        )
        screen.blit(
            pine1_img,
            (
                (x * width) - bg_scroll * 0.7,
                SCREEN_HEIGHT - pine1_img.get_height() - 150,
            ),
        )
        screen.blit(
            pine2_img,
            ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()),
        )


# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data


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

# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


# create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
# load in level data and create world
with open(f"world_data\level{level}_data.csv", newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)


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
        draw_bg()
        # draw world map
        world.draw()
        # show player health
        health_bar.draw(player.health)
        # show ammo
        draw_text("AMMO: ", FONT, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (90 + (x * 10), 40))
        # show grenades
        draw_text("GRENADES: ", FONT, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (135 + (x * 15), 60))

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # update and draw groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()
        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # update player actions
        if player.alive:
            # shoot bullets
            if shoot:
                player.shoot()
            # throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(
                    player.rect.centerx
                    + (0.5 * player.rect.size[0] * player.direction),
                    player.rect.top,
                    player.direction,
                )
                grenade_group.add(grenade)
                # reduce grenades
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)  # 2: jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1: run
            else:
                player.update_action(0)  # 0: idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if player has completed the level
            if level_complete:
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    # load in level data and create world
                    with open(
                        f"world_data\level{level}_data.csv", newline=""
                    ) as csvfile:
                        reader = csv.reader(csvfile, delimiter=",")
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
        else:
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = reset_level()
                # load in level data and create world
                with open(f"world_data\level{level}_data.csv", newline="") as csvfile:
                    reader = csv.reader(csvfile, delimiter=",")
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)

    for event in pygame.event.get():
        # quit game
        if event.type == pygame.QUIT:
            run = False
        # keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False

        # keyboard button released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False

    pygame.display.update()

pygame.quit()
