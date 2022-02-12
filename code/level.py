import enum
from tokenize import group
import pygame
from settings import *
from tile import Tile
from player import Player
from enemy import Enemy
from particles import AnimationPlayer
from debug import debug
from support import *
from random import choice, randint
from weapon import Weapon
from ui import UI

class Level:
  def __init__(self):

    # Get the Display Surface
    self.display_surface = pygame.display.get_surface()

    # Sprite Group Setup
    self.visible_sprites = YSortCameraGroup()
    self.obstacle_sprites = pygame.sprite.Group()

    self.current_attack = None
    self.attack_sprites = pygame.sprite.Group()
    self.attackable_sprites = pygame.sprite.Group()

    # Sprite Setup
    self.create_map()

    self.ui = UI()

    self.animation_player = AnimationPlayer()

  def create_attack(self):
    self.current_attack = Weapon(self.player, [self.visible_sprites, self.attack_sprites])

  def create_magic(self, style, strength, cost):
    pass

  def create_map(self):
    layouts = {
      'boundary': import_csv_layout('../map/map_FloorBlocks.csv'),
      'grass': import_csv_layout('../map/map_Grass.csv'),
      'large_object': import_csv_layout('../map/map_LargeObjects.csv'),
      'entities': import_csv_layout('../map/map_Entities.csv')
    }
    graphics = {
      'grass': import_folder('../graphics/grass'),
      'large_objects': import_folder('../graphics/objects')
    }

    for style, layout in layouts.items():
      for r_ind, row in enumerate(layout):
        for c_ind, tile in enumerate(row):
          if tile != '-1':
            x = c_ind * TILESIZE
            y = r_ind * TILESIZE
            if style == 'boundary':
              Tile((x, y), [self.obstacle_sprites], 'invisible')
            if style == 'grass':
              random_grass_image = choice(graphics['grass'])
              Tile(
                (x, y), 
                [self.visible_sprites, self.obstacle_sprites, self.attackable_sprites], 
                'grass', 
                random_grass_image
              )
            if style == 'large_object':
              surf = graphics['large_objects'][int(tile)]
              Tile((x, y), [self.visible_sprites, self.obstacle_sprites], 'large_object', surf)
            if style == 'entities':
              if tile == '394':
                self.player = Player(
                  (x, y), 
                  [self.visible_sprites], 
                  self.obstacle_sprites, 
                  self.create_attack, 
                  self.destroy_attack,
                  self.create_magic
                )
              else:
                if tile == '390': monster_name = 'bamboo'
                elif tile == '391': monster_name = 'spirit'
                elif tile == '392': monster_name = 'raccoon'
                else: monster_name = 'squid'
                Enemy(
                  monster_name, 
                  (x, y), 
                  [self.visible_sprites, self.attackable_sprites], 
                  self.obstacle_sprites,
                  self.damage_player,
                  self.trigger_death_particles
                )

  def destroy_attack(self):
    if self.current_attack:
      self.current_attack.kill()
    self.current_attack = None

  def player_attack_logic(self):
    if self.attack_sprites:
      for attack_sprite in self.attack_sprites:
        collision_sprites = pygame.sprite.spritecollide(attack_sprite, self.attackable_sprites, False)
        if collision_sprites:
          for target_sprite in collision_sprites:
            if target_sprite.sprite_type == 'grass':
              pos = target_sprite.rect.center
              offset = pygame.math.Vector2(0, 75)
              for leaf in range(randint(3, 6)):
                self.animation_player.create_grass_particles(pos - offset, [self.visible_sprites])
              target_sprite.kill()
            else:
              target_sprite.get_damage(self.player, attack_sprite.sprite_type)

  def damage_player(self, amount, attack_type):
    if self.player.vunerable:
      self.player.health -= amount
      self.player.vunerable = False
      self.player.hurt_time = pygame.time.get_ticks()
      self.animation_player.create_particles(attack_type, self.player.rect.center, [self.visible_sprites])

  def trigger_death_particles(self, pos, particle_type):
    self.animation_player.create_particles(particle_type, pos, [self.visible_sprites])

  def run(self):
    self.visible_sprites.custom_draw(self.player)
    self.visible_sprites.update()
    self.visible_sprites.enemy_update(self.player)
    self.player_attack_logic()
    self.ui.display(self.player)

class YSortCameraGroup(pygame.sprite.Group):
  def __init__(self):
    super().__init__()
    self.display_surface = pygame.display.get_surface()
    self.half_width = self.display_surface.get_size()[0] // 2
    self.half_height = self.display_surface.get_size()[1] // 2
    self.offset = pygame.math.Vector2()

    self.floor_surf = pygame.image.load('../graphics/tilemap/ground.png').convert()
    self.floor_rect = self.floor_surf.get_rect(topleft = (0, 0))

  def custom_draw(self, player):
    self.offset.x = player.rect.centerx - self.half_width
    self.offset.y = player.rect.centery - self.half_height

    floor_offset_pos = self.floor_rect.topleft - self.offset
    self.display_surface.blit(self.floor_surf, floor_offset_pos)

    for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
      offset_pos = sprite.rect.topleft - self.offset
      self.display_surface.blit(sprite.image, offset_pos)

  def enemy_update(self, player):
    enemy_sprites = [sprite for sprite in self.sprites() if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'enemy']
    for enemy in enemy_sprites:
      enemy.enemy_update(player)
