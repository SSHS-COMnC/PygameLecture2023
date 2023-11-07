from typing import Any, Self
import pygame, csv

from constants import *
from pygame import Surface
from pygame.sprite import Sprite, Group
from abc import ABCMeta, abstractmethod


def sign(num: int):
    """부호함수. 양수: 1, 음수: -1, 0: 0"""
    if num > 1:
        return 1
    elif num < 1:
        return -1
    else:
        return 0


class Scene(Group, metaclass=ABCMeta):
    current: Self

    @abstractmethod
    def reset(self):
        ...


class Level(Scene):
    def get_data(level_no, rows, cols):
        data = []
        for row in range(rows):
            r = [-1] * cols
            data.append(r)
        with open(f"world_data\level{level_no}_data.csv", newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    data[x][y] = int(tile)
        return data

    def __init__(self, level_no, rows=ROWS, cols=COLS):
        super().__init__()
        self.level_no = level_no
        self.data = Level.get_data(level_no, rows, cols)
        self.reset()

    def reset(self):
        self.level_length = len(self.data[0])
        # iterate through each value in level data file
        for iy, row in enumerate(self.data):
            for ix, tile in enumerate(row):
                if tile >= 0:
                    x, y = ix * TILE_SIZE, iy * TILE_SIZE
                    if tile >= 0 and tile <= 8:
                        self.add(Tile(x, y, tile))
                    elif tile == 15:  # create player
                        player = Player(x, y)
                        self.add(player)
                        # health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # create enemies
                        self.add(Enemy(x, y))
                    elif tile == 17:  # create ammo box
                        self.add(ItemBox("Ammo", x, y))
                    elif tile == 18:  # create grenade box
                        self.add(ItemBox("Grenade", x, y))
                    elif tile == 19:  # create health box
                        self.add(ItemBox("Health", x, y))
                    # elif tile == 20:  # create exit
                    #     self.add(Exit(x, y))


class PositionedSprite(Sprite):
    def __init__(self, x, y, image: Surface) -> None:
        super().__init__()
        self.image = image
        self.rect = image.get_rect().move(x, y)

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, val):
        self.rect.x = val

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, val):
        self.rect.y = val


class Tile(PositionedSprite):
    tiles = Group()

    def __init__(self, x, y, tile) -> None:
        super().__init__(x, y, image_bank[f"tile/{tile}"])
        self.tiles.add(self)


class Soldier(PositionedSprite):
    def __init__(self, x, y, image: Surface) -> None:
        super().__init__(x, y, image)


class Player(Soldier):
    player: Self

    def __init__(self, x, y) -> None:
        super().__init__(x, y, image_bank["player/Idle/0"])
        self.x_speed, self.y_speed = 0, 0
        self.health = 100
        self.in_air = True
        self.dead = False
        Player.player = self

    def move(self) -> bool:
        # apply gravity
        self.y_speed += GRAVITY

        dx, dy = self.x_speed, self.y_speed

        obstacles = Group(*Tile.tiles, *Enemy.enemies)

        self.x += dx
        if pygame.sprite.spritecollideany(self, obstacles):
            self.x -= dx
            dx = 0
        else:
            self.x -= dx

        self.y += dy
        if spr := pygame.sprite.spritecollideany(self, obstacles):
            self.y -= dy
            spr: PositionedSprite
            if self.y_speed < 0:
                self.y_speed = 0
                dy = spr.rect.bottom - self.rect.top
            elif self.y_speed >= 0:
                self.y_speed = 0
                self.in_air = False
                dy = spr.rect.top - self.rect.bottom
        else:
            self.y -= dy

        # check if fallen off the map
        if self.rect.bottom > MAP_HEIGHT:
            self.health = 0

        # check if going off the edges of the screen
        if self.rect.left + dx < 0 or self.rect.right + dx > MAP_WIDTH:
            dx = 0

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        return False

    def jump(self):
        if self.in_air == False:
            self.y_speed = -15
            self.in_air = True

    def update(self) -> None:
        if bullet := pygame.sprite.spritecollideany(self, Bullet.bullets):
            bullet: Bullet
            bullet.kill()
            self.health -= 5


class Enemy(Soldier):
    enemies = Group()

    def __init__(self, x, y, direction=1) -> None:
        super().__init__(x, y, image_bank["enemy/Idle/0"])
        self.enemies.add(self)
        self.direction = direction
        self.ammo = 20
        self.shoot_cooldown = 0

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 60
            Bullet(
                self.rect.centerx + (0.75 * self.rect.size[0] * self.direction),
                self.rect.centery,
                self.direction,
            )
            # reduce ammo
            self.ammo -= 1

    def update(self) -> None:
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        to_player: pygame.Vector2 = pygame.Vector2(
            Player.player.rect.center
        ) - pygame.Vector2(self.rect.center)
        if to_player.length() < 100:
            if to_player.x < 0:
                self.direction = -1
            elif to_player.x > 0:
                self.direction = 1
            self.shoot()


class ItemBox(PositionedSprite):
    def __init__(self, kind, x, y) -> None:
        self.kind = kind
        super().__init__(x, y, image_bank[f"icons/{kind}_box"])


class Bullet(PositionedSprite):
    bullets = Group()

    def __init__(self, x, y, direction) -> None:
        super().__init__(x, y, image_bank["icons/bullet"])
        self.x_speed = 2 * direction
        self.direction = direction
        self.rect.center = (x, y)
        self.bullets.add(self)
        Scene.current.add(self)

    def update(self):
        # move bullet
        self.x += self.x_speed

        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > MAP_WIDTH:
            self.kill()

        if pygame.sprite.spritecollideany(self, Tile.tiles):
            self.kill()


class Camera:
    def __init__(self, x, y, width, height) -> None:
        self.rect = pygame.Rect(x, y, width, height)

    def move(self):
        self.rect.center = Player.player.rect.center

    def get_rects(self):
        r = min(self.rect.right, MAP_WIDTH)
        b = min(self.rect.bottom, MAP_HEIGHT)
        l = max(self.rect.left, 0)
        t = max(self.rect.top, 0)
        rect = pygame.Rect((l - self.rect.left, t - self.rect.top), (r - l, b - t))
        rect1 = pygame.Rect(l, t, r - l, b - t)
        return rect, rect1

    def get_surface(self, backscreen: Surface, rect, rect1):
        surface = Surface(self.rect.size).convert_alpha()
        surface.blit(backscreen.subsurface(rect1), rect)
        return surface
