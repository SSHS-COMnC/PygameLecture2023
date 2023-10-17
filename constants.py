import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ImageBank(metaclass=Singleton):
    def __init__(self) -> None:
        self.images = {}

    def __getitem__(self, args):
        if not isinstance(args, str):
            key, *args = args
        else:
            key = args
            args = []
        if key in self.images:
            return self.images[key]
        else:
            if len(args) > 0 and args[0] != "":
                file_format = args[0]
            else:
                file_format = "png"
            image = pygame.image.load(f"img/{key}.{file_format}").convert_alpha()

            if len(args) > 1:
                scale = args[1]
                image = pygame.transform.scale_by(image, scale)
            self.images[key] = image
            return self.images[key]


image_bank = ImageBank()
