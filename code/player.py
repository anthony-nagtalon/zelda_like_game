from tkinter.ttk import Style
import pygame
from settings import *
from support import import_folder
from debug import debug

class Player(pygame.sprite.Sprite):
  def __init__(self, pos, groups, obstacle_sprites, create_attack, destroy_attack, create_magic):
    super().__init__(groups)
    self.image = pygame.image.load('../graphics/test/player.png').convert_alpha()
    self.rect = self.image.get_rect(topleft = pos)
    self.hitbox = self.rect.inflate(0, -26)

    self.import_player_assets()
    self.status = 'down'
    self.frame_index = 0
    self.animation_speed=0.15

    self.direction = pygame.math.Vector2()
    self.attacking = False
    self.attack_cd = 400
    self.attack_time = None

    self.obstacle_sprites = obstacle_sprites

    self.create_attack = create_attack
    self.destroy_attack = destroy_attack
    self.weapon_index = 0
    self.weapon = list(weapon_data.keys())[self.weapon_index]
    self.can_switch_weapon = True
    self.weapon_switch_time = None
    self.switch_duration_cooldown = 200

    self.create_magic = create_magic
    self.magic_index = 0
    self.magic = list(magic_data.keys())[self.magic_index]
    self.can_switch_magic = True
    self.magic_switch_time = None

    self.stats = {'health': 100, 'mp': 60, 'attack': 10, 'magic': 4, 'speed': 5}
    self.health = self.stats['health']
    self.mp = self.stats['mp']
    self.exp = 123
    self.speed = self.stats['speed']

  def import_player_assets(self):
    character_path = '../graphics/player'
    self.animations = {
      'up': [],
      'down': [],
      'left': [],
      'right': [],
      'up_idle': [],
      'down_idle': [],
      'left_idle': [],
      'right_idle': [],
      'up_attack': [],
      'down_attack': [],
      'left_attack': [],
      'right_attack': []
    }

    for animation in self.animations.keys():
      full_path = character_path + '/' + animation
      self.animations[animation] = import_folder(full_path)

  def input(self):
    if not self.attacking:
      keys_pressed = pygame.key.get_pressed()

      if keys_pressed[pygame.K_UP]:
        self.direction.y = -1
        self.status = 'up'
      elif keys_pressed[pygame.K_DOWN]:
        self.direction.y = 1
        self.status = 'down'
      else:
        self.direction.y = 0
      
      if keys_pressed[pygame.K_LEFT]:
        self.direction.x = -1
        self.status = 'left'
      elif keys_pressed[pygame.K_RIGHT]:
        self.direction.x = 1
        self.status = 'right'
      else:
        self.direction.x = 0

      if keys_pressed[pygame.K_SPACE]:
        self.attacking = True
        self.attack_time = pygame.time.get_ticks()
        self.create_attack()

      if keys_pressed[pygame.K_LCTRL]:
        self.attacking = True
        self.attack_time = pygame.time.get_ticks()
        style = list(magic_data.keys())[self.magic_index]
        strength = list(magic_data.values())[self.magic_index]['strength'] + self.stats['magic']
        cost = list(magic_data.values())[self.magic_index]['cost']
        self.create_magic(style, strength, cost)
      
      if keys_pressed[pygame.K_q] and self.can_switch_weapon:
        self.can_switch_weapon = False
        self.weapon_switch_time = pygame.time.get_ticks()
        if self.weapon_index < len(list(weapon_data.keys())) - 1:
          self.weapon_index += 1
        else:
          self.weapon_index = 0
        self.weapon = list(weapon_data.keys())[self.weapon_index]

      if keys_pressed[pygame.K_e] and self.can_switch_magic:
        self.can_switch_magic = False
        self.magic_switch_time = pygame.time.get_ticks()
        if self.magic_index < len(list(magic_data.keys())) - 1:
          self.magic_index += 1
        else:
          self.magic_index = 0
        self.magic = list(magic_data.keys())[self.magic_index]

  def get_status(self):
    if self.direction.x == 0 and self.direction.y == 0:
      if not 'idle' in self.status and not 'attack' in self.status:
        self.status = self.status + '_idle'

    if self.attacking:
      self.direction.x = 0
      self.direction.y = 0
      if not 'attack' in self.status:
        if 'idle' in self.status:
          self.status = self.status.replace('_idle', '_attack')
        else:
          self.status = self.status + '_attack'
    else:
      if '_attack' in self.status:
        self.status = self.status.replace('_attack', '_idle')

  def move(self, speed):
    if self.direction.magnitude() != 0:
      self.direction = self.direction.normalize()

    self.hitbox.x += self.direction.x * speed
    self.collision('horizontal')
    self.hitbox.y += self.direction.y * speed
    self.collision('vertical')
    self.rect.center = self.hitbox.center
  
  def collision(self, direction):
    if direction == 'horizontal':
      for sprite in self.obstacle_sprites:
        if sprite.hitbox.colliderect(self.hitbox):
          if self.direction.x > 0:
            self.hitbox.right = sprite.hitbox.left
          if self.direction.x < 0:
            self.hitbox.left = sprite.hitbox.right

    if direction == 'vertical':
      for sprite in self.obstacle_sprites:
        if sprite.hitbox.colliderect(self.hitbox):
          if self.direction.y > 0:
            self.hitbox.bottom = sprite.hitbox.top
          if self.direction.y < 0:
            self.hitbox.top = sprite.hitbox.bottom

  def cooldowns(self):
    current_time = pygame.time.get_ticks()
    if self.attacking:
      if current_time - self.attack_time >= self.attack_cd:
        self.attacking = False
        self.destroy_attack()

    if not self.can_switch_weapon:
      if current_time - self.weapon_switch_time >= self.switch_duration_cooldown:
        self.can_switch_weapon = True

    if not self.can_switch_magic:
      if current_time - self.magic_switch_time >= self.switch_duration_cooldown
        self.can_switch_magic = True

  def animate(self):
    animation = self.animations[self.status]

    self.frame_index += self.animation_speed
    if self.frame_index >= len(animation):
      self.frame_index = 0

    self.image = animation[int(self.frame_index)]
    self.rect = self.image.get_rect(center = self.hitbox.center)

  def update(self):
    self.input()
    self.cooldowns()
    self.get_status()
    self.animate()
    self.move(self.speed)