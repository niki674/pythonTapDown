import pygame as pg
import pytmx
import json
import random

pg.init()

pg.mixer.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
RESOLUTIONS = ((250, 250), (400, 300), (500, 350), (600, 400), (750, 480), (900, 600), (1100, 600), (1300, 700), (1500, 800))

MENU_NAV_XPAD = 90
MENU_NAV_YPAD = 130

BUTTON_WIDTH = 80
BUTTON_HEIGHT = 80

ICON_SIZE = 80
PADDING = 10

FPS = 80
TILE_SIZE = 1.5

font = pg.font.Font(None, 40)


class Player(pg.sprite.Sprite):
    def __init__(self, map_width, map_height):
        super(Player, self).__init__()

        self.load_animation()

        self.current_animation = self.idle_animation_right
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.spawn = (200, 200)
        self.rect.center = self.spawn

        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = 1.2

        self.speed = 4

        self.map_width = map_width
        self.map_height = map_height

        self.interval = 100
        self.timer = pg.time.get_ticks()

        self._fly_mode = False

        self.damage_timer = pg.time.get_ticks()
        self.damage_interval = 2000

    def load_animation(self):
        tile_size, tile_scale = 32, TILE_SIZE

        self.idle_animation_right = []

        spritesheet = pg.image.load('resourses/images/Idle_(32 x 32).png')

        tile_numbers = 5
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.running_animation_right = []

        spritesheet = pg.image.load('resourses/images/Running_(32 x 32).png')

        tile_numbers = 6
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.running_animation_right.append(image)

        self.running_animation_left = [pg.transform.flip(image, True, False) for image in self.running_animation_right]

    def update(self, platforms):
        keys = pg.key.get_pressed()
        if keys[pg.K_d]:
            if self.current_animation != self.running_animation_right:
                self.current_animation = self.running_animation_right
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_x = self.speed
        elif keys[pg.K_a]:
            if self.current_animation != self.running_animation_left:
                self.current_animation = self.running_animation_left
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_x = -self.speed
        else:
            if self.current_animation == self.running_animation_right and (not(keys[pg.K_w] or keys[pg.K_s])):
                self.current_animation = self.idle_animation_right
                self.current_image = 0
            elif self.current_animation == self.running_animation_left and (not(keys[pg.K_w] or keys[pg.K_s])):
                self.current_animation = self.idle_animation_left
                self.current_image = 0
            self.velocity_x = self.velocity_x / self.friction
            self.velocity_y = self.velocity_y / self.friction
            if self.velocity_x ** 2 < 1:
                self.velocity_x = 0

        if keys[pg.K_w]:
            if self.current_animation == self.idle_animation_left:
                self.current_animation = self.running_animation_left
                self.current_image = 0
                self.timer -= self.interval
            elif self.current_animation == self.idle_animation_right:
                self.current_animation = self.running_animation_right
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_y = -self.speed
        elif keys[pg.K_s]:
            if self.current_animation == self.idle_animation_left:
                self.current_animation = self.running_animation_left
                self.current_image = 0
                self.timer -= self.interval
            elif self.current_animation == self.idle_animation_right:
                self.current_animation = self.running_animation_right
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_y = self.speed
        else:
            if self.current_animation == self.running_animation_right and (not(keys[pg.K_d] or keys[pg.K_a])):
                self.current_animation = self.idle_animation_right
                self.current_image = 0
            elif self.current_animation == self.running_animation_left and (not(keys[pg.K_d] or keys[pg.K_a])):
                self.current_animation = self.idle_animation_left
                self.current_image = 0
            self.velocity_y = self.velocity_y / self.friction
            if self.velocity_y ** 2 < 1:
                self.velocity_y = 0

        new_x = self.rect.x + self.velocity_x
        if 0 <= new_x and self.map_width - self.rect.width >= new_x:
            self.rect.x = new_x

        new_y = self.rect.y + self.velocity_y
        if 0 <= new_y and self.map_height - self.rect.height >= new_y:
            self.rect.y = new_y

        for platform in platforms:
            if platform.rect.collidepoint(self.rect.midbottom):
                self.velocity_y = 0
                self.rect.bottom = platform.rect.top

            if platform.rect.collidepoint(self.rect.midtop):
                self.velocity_y = 0
                self.rect.top = platform.rect.bottom

            if platform.rect.collidepoint(self.rect.midright):
                self.velocity_x = 0
                self.rect.right = platform.rect.left
            if platform.rect.collidepoint(self.rect.midleft):
                self.velocity_x = 0
                self.rect.left = platform.rect.right

        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()


class Platform(pg.sprite.Sprite):
    def __init__(self, image, coords, width, height):
        pg.sprite.Sprite.__init__(self)

        self.image = pg.transform.scale(image, (width * TILE_SIZE, height * TILE_SIZE))

        self.rect = self.image.get_rect()
        self.rect.topleft = coords


class Game:
    def __init__(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT

        self.resolution = 5
        SCREEN_WIDTH = RESOLUTIONS[self.resolution][0]
        SCREEN_HEIGHT = RESOLUTIONS[self.resolution][1]

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.setup()

    def setup(self):
        self.mode = 'game'
        pg.display.set_caption("Tap Down")
        self.clock = pg.time.Clock()
        self.is_running = False

        self.tmx_map = pytmx.load_pygame('resourses/maps/main.tmx')

        self.camera_x = 0
        self.camera_y = 0

        self.ghosts = pg.sprite.Group()
        self.all_platforms = pg.sprite.Group()
        self.platforms_1 = pg.sprite.Group()
        self.platforms_2 = pg.sprite.Group()

        self.map_width = self.tmx_map.width * self.tmx_map.tilewidth * TILE_SIZE
        self.map_height = self.tmx_map.height * self.tmx_map.tileheight * TILE_SIZE

        self.player = Player(self.map_width, self.map_height)

        for x, y, gid in self.tmx_map.get_layer_by_name('Слой тайлов 1'):
            tile = self.tmx_map.get_tile_image_by_gid(gid)
            if tile:
                platform = Platform(tile, (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE), self.tmx_map.tilewidth, self.tmx_map.tileheight)
                self.platforms_1.add(platform)
                self.all_platforms.add(platform)

        for x, y, gid in self.tmx_map.get_layer_by_name('Слой тайлов 2'):
            tile = self.tmx_map.get_tile_image_by_gid(gid)
            if tile:
                platform = Platform(tile, (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE), self.tmx_map.tilewidth, self.tmx_map.tileheight)
                self.platforms_2.add(platform)
                self.all_platforms.add(platform)

        for x, y, gid in self.tmx_map.get_layer_by_name('ghosts'):
            tile = self.tmx_map.get_tile_image_by_gid(gid)
            if tile:
                platform = Platform(tile, ((x - 1) * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE - tile.get_height() * TILE_SIZE - self.tmx_map.tileheight * TILE_SIZE), tile.get_width() * TILE_SIZE, tile.get_height() * TILE_SIZE)
                self.ghosts.add(platform)

        self.run()

    def run(self):
        self.is_running = True
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pg.quit()
        quit()

    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.is_running = False

    def update(self):
        if self.mode == 'game':
            self.player.update(self.platforms_2)

            self.camera_x = self.player.rect.centerx - SCREEN_WIDTH // 2
            self.camera_y = self.player.rect.centery - SCREEN_HEIGHT // 2

            self.camera_x = max(0, min(self.camera_x, self.map_width - SCREEN_WIDTH))
            self.camera_y = max(0, min(self.camera_y, self.map_height - SCREEN_HEIGHT))

    def draw(self):
        self.screen.fill("white")

        for sprite in self.all_platforms:
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))

        player_on_scene = False
        for sprite in self.ghosts:
            if not (player_on_scene) and sprite.rect.bottom >= self.player.rect.bottom:
                self.screen.blit(self.player.image, self.player.rect.move(-self.camera_x, -self.camera_y))
                player_on_scene = True
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))

        if not (player_on_scene):
            self.screen.blit(self.player.image, self.player.rect.move(-self.camera_x, -self.camera_y))

        pg.display.flip()


if __name__ == "__main__":
    game = Game()