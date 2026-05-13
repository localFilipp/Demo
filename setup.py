import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Cat game")

WIDTH, HEIGHT = 1000, 650
FPS = 60
PLAYER_VELOCITY = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites): #keerab spritei ühele v teisele poole vaatama
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))] # laeb kõik failid

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha() # laeb teele jääva image? ja paneb transparent backgroundi

        sprites = []

        for i in range(sprite_sheet.get_width() // width): # loob surfacei kus peal animatsioon liikuma hakkab ja mida omakorda liigutada saab
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            rect = pygame.Rect(i * width, 0, width, height) # i on surfacei asukoht ekraanil
            surface.blit(sprite_sheet, (0, 0), rect) # joonistab raamid?
            sprites.append(surface)

        if direction:
            all_sprites[image.replace(".png", "") + "_left"] = sprites
            all_sprites[image.replace(".png", "") + "_right"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "muru.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size) # 0 ja 0 näitavad bloki vasakut ülemist nurka
    surface.blit(image, (0, 0), rect)
    return surface

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    SPRITES = load_sprite_sheets("Characters", "kiisu", 64, 64, True)
    ANIMATION_DELAY = 5
    GRAVITY = 1

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.jump_count = 0
        self.fall_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY, self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "kiisu_idle"
        if self.x_vel != 0:
            sprite_sheet = "sprite_walk"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite) #self.mask ütleb kus kohas spritei pinnal on pikslid

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block,(0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        for animation in self.fire:
            self.fire[animation] = [
                pygame.transform.scale(sprite, (width * 2.5, height * 2.5))
                for sprite in self.fire[animation]
            ]
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Portal(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "portal")
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((0, 0, 255))
        self.mask = pygame.mask.from_surface(self.image)

def get_background(name):
    image = pygame.image.load(join("assets", "background", name))
    image = pygame.transform.scale(image, (100, 100))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, portal, offset_x, lives, heart_img):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    for i in range(lives):
        window.blit(heart_img, (20 + i * 35, 20))

    portal.draw(window, offset_x)
    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

        collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VELOCITY * 2)
    collide_right = collide(player, objects, PLAYER_VELOCITY * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VELOCITY)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VELOCITY)

    handle_vertical_collision(player, objects, player.y_vel)

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("pilved2.png")

    block_size = 64

    start_x = 100
    start_y = 100
    player = Player(start_x, start_y, 50, 50)
    lives = 3

    heart_img = pygame.image.load("assets/UI/PixelHeart.png").convert_alpha()
    heart_img = pygame.transform.scale(heart_img, (30, 30))

    #fire objects
    fire = Fire(300, HEIGHT - block_size - 64, 16, 32)
    fire1 = Fire(500, HEIGHT - block_size - 64, 16, 32)
    fire2 = Fire(1250, HEIGHT - block_size - 64 * 4, 16, 32)

    fire.on()
    fire1.on()
    fire2.on()

    portal = Portal(3050, HEIGHT - block_size - 64 * 3, 40, 64)

    floor = [
        Block(i * block_size, HEIGHT - block_size, block_size)
        for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)
        if not (10 <= i <= 25) and not (-10 <= i <= -1)
    ]
    objects = [
        *floor,
        Block(block_size * 3, HEIGHT - block_size * 4, block_size),
        Block(block_size * 4, HEIGHT - block_size * 4, block_size),
        Block(block_size * 11, HEIGHT - block_size * 4, block_size),
        Block(block_size * 14, HEIGHT - block_size * 5, block_size),
        Block(block_size * 18, HEIGHT - block_size * 4, block_size),
        Block(block_size * 19, HEIGHT - block_size * 4, block_size),
        Block(block_size * 20, HEIGHT - block_size * 4, block_size),
        Block(block_size * 24, HEIGHT - block_size * 6, block_size),
        Block(block_size * 34, HEIGHT - block_size * 2, block_size),
        Block(block_size * 38, HEIGHT - block_size * 1, block_size),
        Block(block_size * 43, HEIGHT - block_size * 3, block_size),
        Block(block_size * 46, HEIGHT - block_size * 3, block_size),
        Block(block_size * 47, HEIGHT - block_size * 3, block_size),
        Block(block_size * 48, HEIGHT - block_size * 3, block_size),
        fire,
        fire1,
        fire2,
    ]

    offset_x = 0
    scroll_area_width = 200

    run = True
    won = False
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        fire1.loop()
        fire2.loop()
        handle_move(player, objects)

        fires = [fire, fire1, fire2]

        for f in fires:
            if player.rect.colliderect(f.rect):
                lives -= 1

                player.rect.x = start_x
                player.rect.y = start_y

                player.x_vel = 0
                player.y_vel = 0
                player.fall_count = 0
                player.jump_count = 0

                offset_x = 0

                pygame.time.delay(100)

        if pygame.sprite.collide_mask(player, portal):
            print("MÄNG VÕIDETUD!")
            run = False

        if player.rect.top > HEIGHT:
            print("GAME OVER")
            run = False

        if lives <= 0:
            print("GAME OVER - no lives left")
            run = False

        draw(window, background, bg_image, player, objects, portal, offset_x, lives, heart_img)

        if won:
            font = pygame.font.SysFont("arial", 60)
            text = font.render("MÄNG VÕIDETUD!", True, (255, 255, 255))
            window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.update()

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit() #gello

if __name__ == '__main__':
    main(window)
