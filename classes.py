import pygame, csv

from constants import *
from pygame import Surface
from pygame.sprite import Sprite, Group


class Scene(Group):
    """A class that manages which level the game is currently on."""

    game = None  # this class variable will be the game which contains the scene
    current = None  # this class variable will be the current level the game is on


class Level(Scene):
    """A class that loads the level data from a csv file and creates the level. It is a Group that consists of all entities in the level."""

    def __init__(self, level_no, rows=ROWS, cols=COLS):
        super().__init__()
        self.level_no = level_no
        self.data = Level.get_data(level_no, rows, cols)
        self.reset()

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

    def reset(self):
        self.level_length = len(self.data[0])
        # iterate through each value in level data file
        for iy, row in enumerate(self.data):
            for ix, tile in enumerate(row):
                if tile >= 0:
                    x, y = ix * TILE_SIZE, iy * TILE_SIZE
                    if tile >= 0 and tile <= 8:
                        self.add(
                            Tile(x, y, tile)
                        )  # a pygame Group has an add method that adds a sprite to the group
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
    """A class that represents a sprite with a position."""

    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = image.get_rect().move(x, y)


class Tile(PositionedSprite):
    """A class that represents a tile in the game."""

    tiles = Group()  # class attribute to keep track of all tiles

    def __init__(self, x, y, tile):
        super().__init__(x, y, Scene.game.tile_imgs[tile])
        self.tiles.add(self)


class Player(PositionedSprite):
    """A class that represents the player. It is a subclass of PositionedSprite."""

    def __init__(self, x, y):
        super().__init__(x, y, Scene.game.player_img)
        self.x_speed, self.y_speed = 0, 0
        self.health = 100
        self.in_air = True
        Player.player = self  # class attribute to keep track of the player

    def move(self):
        # apply gravity
        self.y_speed += GRAVITY

        # how much the player will move if nothing goes wrong
        dx, dy = self.x_speed, self.y_speed

        obstacles = Group(
            Tile.tiles, Enemy.enemies
        )  # create a pygame group of all obstacles to check for collisions with the spritecollideany method

        # check for collisions with obstacles in the x direction
        self.rect.x += dx  # try to move the player in the x direction
        if pygame.sprite.spritecollideany(self, obstacles):
            self.rect.x -= dx
            dx = 0  # if we collide, don't move the player
        else:
            self.rect.x -= dx

        # check for collisions with obstacles in the y direction
        self.rect.y += dy  # try to move the player in the y direction
        if spr := pygame.sprite.spritecollideany(self, obstacles):
            self.rect.y -= dy
            if self.y_speed < 0:  # when ascending,
                self.y_speed = 0  # if we collide, stop ascending
                dy = (
                    spr.rect.bottom - self.rect.top
                )  # move the player's position to the bottom of the obstacle
            elif self.y_speed >= 0:  # when descending,
                self.y_speed = 0  # if we collide, stop descending
                self.in_air = False  # the player is no longer in the air
                dy = (
                    spr.rect.top - self.rect.bottom
                )  # move the player's position to the top of the obstacle
        else:
            self.rect.y -= dy

        # check if fallen off the map
        if self.rect.top > BACK_SCREEN_HEIGHT:
            self.health = 0

        # check if going off the edges of the screen
        if self.rect.left + dx < 0 or self.rect.right + dx > BACK_SCREEN_WIDTH:
            dx = 0

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        return False

    def jump(self):
        if not self.in_air:
            self.y_speed = -15
            self.in_air = True

    def update(self):
        if bullet := pygame.sprite.spritecollideany(self, Bullet.bullets):
            bullet.kill()
            self.health -= 5
        if self.health <= 0:
            self.kill()


class Enemy(PositionedSprite):
    """A class that represents an enemy. It is a subclass of PositionedSprite."""

    enemies = Group()  # class attribute to keep track of all enemies

    def __init__(self, x, y, direction=1):
        super().__init__(x, y, Scene.game.enemy_img)
        self.enemies.add(self)
        self.direction = direction
        self.ammo = ENEMY_AMMO
        self.shoot_cooldown = 0

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = ENEMY_COOLDOWN  # reset cooldown
            Bullet(
                self.rect.centerx + (0.75 * self.rect.size[0] * self.direction),
                self.rect.centery,
                self.direction,
            )  # spawn bullet
            # reduce ammo
            self.ammo -= 1

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        to_player = pygame.Vector2(Player.player.rect.center) - pygame.Vector2(
            self.rect.center
        )

        # determine if player is in range, and if so, shoot
        # determine the direction to shoot
        if to_player.length() < ENEMY_RANGE:
            if to_player.x < 0:
                self.direction = -1
            elif to_player.x > 0:
                self.direction = 1
            self.shoot()


class ItemBox(PositionedSprite):
    """A class that represents an item box. It is a subclass of PositionedSprite."""

    def __init__(self, kind, x, y):
        self.kind = kind
        super().__init__(x, y, Scene.game.itembox_imgs[kind])


class Bullet(PositionedSprite):
    """A class that represents a bullet. It is a subclass of PositionedSprite."""

    bullets = Group()  # class attribute to keep track of all bullets

    def __init__(self, x, y, direction):
        super().__init__(x, y, Scene.game.bullet_img)
        self.x_speed = BULLET_SPEED * direction
        self.direction = direction
        self.rect.center = (x, y)
        self.bullets.add(self)
        Scene.current.add(self)

    def update(self):
        # move bullet
        self.rect.x += self.x_speed

        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > BACK_SCREEN_WIDTH:
            self.kill()

        # check if bullet has hit anything
        if pygame.sprite.spritecollideany(self, Tile.tiles):
            self.kill()


class Camera:
    """
    A class that represents the camera. It is used to keep track of the player's position and to move the background accordingly.
    There are two screens: the screen, which is the pygame screen, and the backscreen, which is the background.
    Here, the what the camera shows will be what is displayed on the pygame screen.
    """

    def __init__(self, x, y, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        self.rect = pygame.Rect(x, y, width, height)

    def move(self):
        self.rect.center = Player.player.rect.center  # move camera to player's position

    def get_rects(self):
        """
        This function returns two rectangles:
        one that is the intersection of the camera and the backscreen, and
        one that is the intersection of the camera and the screen.
        The first rectangle is what we want to show,
        and the second rectangle is where we want to show it on the camera.
        """
        r = min(self.rect.right, BACK_SCREEN_WIDTH)
        b = min(self.rect.bottom, BACK_SCREEN_HEIGHT)
        l = max(self.rect.left, 0)
        t = max(self.rect.top, 0)
        rect1 = pygame.Rect((l, t), (r - l, b - t))
        rect2 = pygame.Rect((l - self.rect.left, t - self.rect.top), (r - l, b - t))
        return rect1, rect2

    def get_surface(self, backscreen, rect1, rect2):
        """
        We want to blit the first rectangle on to the second rectangle, and return the resulting surface
        """
        surface = Surface(self.rect.size).convert_alpha()
        surface.blit(
            backscreen.subsurface(rect1), rect2
        )  # the subsurface takes a rectangle as an argument, and returns a surface that is the intersection of the surface and the rectangle
        return surface


class Button:
    """A class that represents a button."""

    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(
            image, (int(width * scale), int(height * scale))
        )
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action


class Game:
    """class of the game"""

    def __init__(self):
        pygame.init()

        # create screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.backscreen = pygame.Surface((BACK_SCREEN_WIDTH, BACK_SCREEN_HEIGHT))
        pygame.display.set_caption("Shooter")

        # load data and create buttons
        self.load_data()
        self.create_btns()

        # create clock
        self.clock = pygame.time.Clock()

        # initialize game variables
        level = 1
        self.start = False
        Scene.game = self
        Scene.current = Level(level)
        self.camera = Camera(0, 0)

        # define font
        self.font = pygame.font.SysFont("Futura", 30)

    def load_data(self):
        self.start_img = pygame.image.load("img/start_btn.png").convert_alpha()
        self.exit_img = pygame.image.load("img/exit_btn.png").convert_alpha()
        self.restart_img = pygame.image.load("img/restart_btn.png").convert_alpha()

        self.player_img = pygame.image.load("img/player/Idle/0.png").convert_alpha()
        self.enemy_img = pygame.image.load("img/enemy/Idle/0.png").convert_alpha()
        self.bullet_img = pygame.image.load("img/icons/bullet.png").convert_alpha()
        self.itembox_imgs = {
            "Health": pygame.image.load("img/icons/health_box.png").convert_alpha(),
            "Ammo": pygame.image.load("img/icons/ammo_box.png").convert_alpha(),
            "Grenade": pygame.image.load("img/icons/grenade_box.png").convert_alpha(),
        }
        self.tile_imgs = {}
        for i in range(TILE_TYPES):
            self.tile_imgs[i] = pygame.image.load(f"img/tile/{i}.png").convert_alpha()

    def create_btns(self):
        self.start_button = Button(
            SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, self.start_img, 1
        )
        self.exit_button = Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, self.exit_img, 1
        )
        self.restart_button = Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 - 50, self.restart_img, 2
        )

    def draw_text(self, text, font, text_col, x, y):
        img = font.render(text, True, text_col)
        self.screen.blit(img, (x, y))

    def event(self):
        for event in pygame.event.get():
            # quit game
            if event.type == pygame.QUIT:
                self.run = False
            # keyboard presses
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    Player.player.x_speed = -10
                if event.key == pygame.K_d:
                    Player.player.x_speed = 10
                if event.key == pygame.K_w:
                    Player.player.jump()
                if event.key == pygame.K_ESCAPE:
                    self.run = False

            # keyboard button released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    Player.player.x_speed = 0
                if event.key == pygame.K_d:
                    Player.player.x_speed = 0

    def draw_menu(self):
        self.screen.fill(BG)
        # add buttons
        if self.start_button.draw(self.screen):
            self.start = True
        if self.exit_button.draw(self.screen):
            self.run = False

    def draw(self):
        self.camera.move()
        rect1, rect2 = self.camera.get_rects()
        # update background
        self.backscreen.fill(BG, rect1)
        # draw world map
        Scene.current.draw(self.backscreen)
        Scene.current.update()

        if Player.player.alive():
            if Player.player.in_air:
                Player.player.jump()
            level_complete = Player.player.move()
            # check if Player.player has completed the level
            if level_complete:
                level += 1
                if level <= MAX_LEVELS:
                    Scene.current = Level(level)

            self.screen.blit(
                self.camera.get_surface(self.backscreen, rect1, rect2),
                pygame.Rect((0, 0), self.camera.rect.size),
            )

        else:
            if self.restart_button.draw(self.screen):
                Scene.current.reset()

    def main_loop(self):
        self.run = True
        while self.run:
            self.clock.tick(FPS)

            self.event()

            if not self.start:
                self.draw_menu()

            else:
                self.draw()

            pygame.display.update()

        pygame.quit()
