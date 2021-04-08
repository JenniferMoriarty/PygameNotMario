# ======================================
# ==          I M P O R T S           ==
# ======================================
# Tell main where to find the libraries
# and other game code. It will search in
# this directory and in Thonny's directory.

#Import Pygame
import pygame
#Share all of Pygame's methods and variables
#so we can use them here without worrying about
#telling the code to look in pygame for them
#each time. I think. People online suggest that
#using the * function like this is generally bad
#practice because it makes confusing code when
#different files freely share their internal data.
from pygame.locals import *

# Import math functions
import math
import random

#Import functions that let us read and write
#to .tmx files, which are what Tiled Map Editor
#creates. If you don't have pytmx, it can be
#added from within Thonny under Tools->Manage Packages.
import pytmx
#Share one of pytmx's methods.Note that we're not using
#the * function this time, so the only methods that
#get imported are those we expressly name.
from pytmx.util_pygame import load_pygame

#Import other game files. These are in the same
#directory as Notmario and exist basically to help
#organize the code.
import methods
#Again, need to expressly share the methods to which
#we want to have access.
from methods import blit_all_tiles
from methods import get_tile_properties
from methods import play_sound

#This file contains CONSTANTS. Technically, Python does
#not have a "constant" variable type. But, we just use
#regular old variables and treat them as constants. To
#remind us not to change them, we name them in all caps.
import constants
#More bad practice importing all of constant
from constants import *

# ============================================
# ==             SPRITE SHEET               ==
# ============================================
# Pygame may not itself handle sprite sheets
# all that well. Found a function that does.
# documentation at https://www.pygame.org/wiki/Spritesheet

# NOTE: Probably should make a master sprite sheet rather than
# each object having their own.

class Sprite_Sheet(object):
    
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename)
        except pygame.error:
            print ("Unable to load spritesheet image:", filename)
            return
        
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface((rect.size),pygame.SRCALPHA).convert_alpha()
        image.set_alpha(255)
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates" 
        return [self.image_at(rect, colorkey) for rect in rects]

    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

# ============================================
# ==            SPRITE HANDLER              ==
# ============================================
# Creates and manages all sprites. Holds the lists
# of sprites in Pygame Groups.

class Sprite_Handler(object):
    
    def __init__(self):
        
        self.name = "Hello"
        self.player = Player(100,100,(0,0))
        
        # Enemies collide with player and are damaged by player projectiles, in general.
        self.enemy_list = pygame.sprite.Group()
        
        # Items collide with player and then die, modifying player inventory.
        self.item_list = pygame.sprite.Group()
        
        # Enemy projectiles collide with player, dealing damage.
        self.enemy_projectile_list = pygame.sprite.Group()
        
        # Player projectiles collide with enemies, dealing damage.
        self.player_projectile_list = pygame.sprite.Group()
        
        # Doodads don't collide with anything; used for effects, NPCs, etc.
        self.doodad_list = pygame.sprite.Group()
        
        # HUD Displays information
        self.hud = Hud()
        
    def player_enemy_collision_check(self):
        
        # Only check collisions if the player is not already doing a death
        # animation.
        if(self.player.state != DYING):
            self.enemy_hit_list = pygame.sprite.spritecollide(self.player, self.enemy_list, False)
            
            player_was_hit = False
            
            for enemy in self.enemy_hit_list:
                 if(enemy.state != DYING) and (enemy.state != DEAD):
                    if( (self.player.rect.y<enemy.rect.y)and(self.player.vector[1]>0)):
                         enemy.got_squished()
                         enemy_position = enemy.getpos()
                         enemy_x = enemy_position[0]
                         enemy_y = enemy_position[1]
                         explosion = Effect(enemy_x,enemy_y)
                         self.doodad_list.add(explosion)
                    else:
                        player_was_hit = True
                        
            if player_was_hit: self.player.take_damage()
                    
    def get_player(self):
        
        return self.player
    
    def update(self, tmxdata, keys):
        
        # Remove  sprites
        for enemy in self.enemy_list:
            if(enemy.state == DEAD): enemy.kill()
        for doodad in self.doodad_list:
            if(doodad.state == DEAD): doodad.kill()
        if(self.player.state == DEAD): self.player.kill()
        
        # Update remaining
        self.player.update(tmxdata, keys)
        self.enemy_list.update(tmxdata, keys)
        self.doodad_list.update()
        
        #Update 
        self.hud.update(self.player.get_hp())
        
        # Check to see if map needs to change.
        self.check_for_map_exit(tmxdata)
    
    def draw(self, map_image):
        
        self.enemy_list.draw(map_image)
        self.player.draw(map_image)
        self.doodad_list.draw(map_image)
    
    def draw_hud(self):
    
        return self.hud.draw()
        
    def get_player_pos(self):
        return self.player.getpos()
    
    # Function searches the Object layers of the TMXDATA you pass
    # and, if it finds any objects named "enemy," spawns an enemy
    # in that location.
    def spawn_sprites_from_map(self, tmxdata):
        
       for layer in tmxdata.visible_layers:
            if(isinstance(layer,pytmx.TiledTileLayer)):
                for tile_object in tmxdata.objects:
                    if (tile_object.name == "enemy_spawn"):
                        enemy = Enemy(tile_object.x,tile_object.y,(0,0))
                        self.enemy_list.add(enemy)

    # Clear all sprites other than players.
    def prepare_for_new_map(self):
        
        # Remove all non-player sprites
        self.enemy_list.empty()
        self.doodad_list.empty()
        
    def reset_player(self, tmxdata):
        self.player.hit_points = 4
        self.player_enters_map(tmxdata, RIGHT)
        self.player.state = self.player.STANDING
        
    # Find the entrance object and put player there.
    # If there isnt a player yet, make one at the spawn point.
    def player_enters_map(self, tmxdata, entrance_direction):

        for layer in tmxdata.visible_layers:
            if(isinstance(layer,pytmx.TiledTileLayer)):
                for tile_object in tmxdata.objects:
                    if (tile_object.name == "entrance"):
                        if(tile_object.properties['dir'] == "RIGHT" and entrance_direction == RIGHT):
                            self.player.setpos(tile_object.x,tile_object.y)
                        elif(tile_object.properties['dir'] == "LEFT" and entrance_direction == LEFT):
                            self.player.setpos(tile_object.x,tile_object.y)
                        elif(tile_object.properties['dir'] == "UP" and entrance_direction == UP):
                            self.player.setpos(tile_object.x,tile_object.y)  
                        elif(tile_object.properties['dir'] == "DOWN" and entrance_direction == DOWN):
                            self.player.setpos(tile_object.x,tile_object.y)
                        else: print("No appropriate landing direction found!")
                            
    def check_for_map_exit(self, tmxdata):
        
        # Look for the screen exit object
        for tile_object in tmxdata.objects:
            if(tile_object.name == 'exit'):
                player_rect = Rect(self.player.rect)
                exit_object_rect = Rect(tile_object.x,tile_object.y,tile_object.width,tile_object.height)
        
                # If the player is intersecting the exit object, need to load a new screen.
                if(pygame.Rect.colliderect(player_rect,exit_object_rect)):
                    print(tile_object.properties)
                    return tile_object.properties
                
        default_dict = {'dest':'none', 'dir':'none'}
        return default_dict

# ============================================
# ==             PLAYER CLASS               ==
# ============================================
# This class inherets from the pygame "sprite"
# class. Why? Because pygame gives us lots of
# really useful functions for using sprites
# and grouping them into lists for use in a game.
# See information on sprites at https://www.pygame.org/docs/tut/SpriteIntro.html
# and https://www.pygame.org/docs/ref/sprite.html

# Note: you will see ".self" all over the place. Why?
# Because we don't have to declare our class variables
# outside of the methods (hurrah!!!). That means the
# code needs to know, when we use a specific variable,
# whether the variable is limited to just that method
# or whether it needs to be stored with the object for
# all methods to use. We use "self." to tell the code
# that we're talking about a class-level variable and not
# a method-level one.
class Player(pygame.sprite.Sprite):
    
    # Initialization
    def __init__ (self,init_x,init_y,init_vector):
        
        # Call the init function of the sprite class from which this inherets.
        pygame.sprite.Sprite.__init__(self)
        
        # GRAPHICS SETUP ------------        
        # Instead of loading an image directly we will use the
        # spritesheet object, defined below. 
        self.my_sprite_sheet = Sprite_Sheet("Broman.png")
        # Now we will initially set the image of this sprite
        # to be the first image on the sprite sheet.
        # Why do we use two paratheses? Because the .image_at function
        # expects to get a single parameter: an array of 4 numbers.
        self.image = self.my_sprite_sheet.image_at((0,0,16,16))
        # Name. This game object needs a name so others can identify it.
        self.name = "player"
        
        self.hit_points = 4
        self.i_frames = 0
        self.i_blink_counter = 0
        self.i_blink = False
        
        # These variables handle jumping, which is more complicated than you'd think.
        self.has_jumped = False #This makes sure you only jump once; resets when you touch the ground.
        self.on_ground = True #This makes sure you can only jump on the ground.
        self.holding_jump = False #This allows the player some control over jump height

        
        # This will track the "state" of the object.
        # Different states will have different positions on the sprite sheet.
        # Use class-specific constants to make code easier to read.
        self.STANDING = 0
        self.WALKING = 1
        self.JUMPING = 3
        
        self.STANDING_START_FRAME = 0 * TILESIZE
        self.WALKING_START_FRAME = 0 * TILESIZE
        self.JUMPING_START_FRAME = 3 * TILESIZE
        self.DYING_START_FRAME = 4 * TILESIZE
        
        self.animation_behavior = self.STANDING
        
        # Internal behavior states.
        # These variables handle AI behavior.
        self.state = self.STANDING
        self.state_counter = 0
        
        # This will be used to determine what frame of animation
        # the object is currently displaying within that state.
        self.animation_frame = 0
        self.ANIMATION_SPEED = 15
        self.ANIMATION_WALKING_FRAMES = 2
        self.animation_delay = 0
        
        # Next, set the size and position of this object, which
        # is called it's "rect" based on the size of the image.
        # Rect objects actually have a ton of useful things we can use
        # that you normally would put in the code, like x, y, etc.
        # x,y,top, left, bottom, right,topleft, bottomleft, topright, bottomright,midtop, midleft, midbottom, midright,center, centerx, centery,size, width, height,w
        self.rect = pygame.Rect(init_x,init_y,TILESIZE,TILESIZE)
        
        # Sound effects
        self.sound_jump = pygame.mixer.Sound("Jump.wav")
        self.sound_death= pygame.mixer.Sound("Death.wav")
        
        # The direction this sprite is moving is stored in a vector.
        self.vector = list(init_vector)
        # The direction this sprite is FACING when not moving.
        self.facing = RIGHT

    # Class Accessor Methods
    #-----------------------
    # Returns an ordered pair that defines this object's top left
    # corner [0] = x and [1] = y
    def getpos(self):
        temp_x=self.rect.x
        temp_y=self.rect.y
        return [temp_x,temp_y]
    
    # Set the position of this object.
    def setpos(self,temp_x,temp_y):
        self.rect.x = temp_x
        self.rect.y = temp_y
        
    # Set the hit points of this object
    def get_hp(self):
        return self.hit_points
    
    # Returns the image of this object
    def draw(self, map_image):
        if(self.i_blink==False):
            map_image.blit(self.image,(self.rect.x,self.rect.y))
    
    # ----------------------
    # Class Methods
    # ----------------------
 
    def take_damage(self):
     
        if(self.i_frames<=0):
            print ("ouch!")
            #Knockback
            if(self.facing == RIGHT): self.vector[0] = -4
            elif(self.facing == LEFT): self.vector[0] = 4
            self.vector[1] = -2
            self.i_frames = 60
            self.i_blink_counter = 10
            self.hit_points -= 1
        if(self.hit_points <= 0): self.die()
        
    def die(self):
        self.state = DYING
        self.animation_behavior = DYING
        self.animation_frame = 0
        self.animation_delay = 0
        self.state_counter = 0
        
    def apply_input(self, keys):
           
        # Update behavior based on input
        if(keys[LEFT]) == True:
            self.vector[0] -= 0.2
        elif(keys[RIGHT]) == True:
            self.vector[0] += 0.2
        else:
            self.vector[0] = self.vector[0]*(0.9)
            if(abs(self.vector[0])<0.05): self.vector[0] = 0
            
        if(self.vector[0] < -2): self.vector[0] = -2       
        if(self.vector[0] > 2): self.vector[0] = 2
        
        # Jump is allowed only after you are on the ground and not jumping for a frame.
        if(self.on_ground == True and keys[JUMP] == False):
           self.has_jumped = False
        # Simple jump. You go higher if you hold the jump button.
        if(keys[JUMP]) == True:
            if(self.on_ground == True and self.has_jumped == False):
                play_sound(self.sound_jump)
                self.has_jumped = True
                self.holding_jump = True
                self.vector[1] = -3.5
                
        # Tell the object if you stopped holding the jump button after takeoff.
        else: self.holding_jump = False
        
        # If you're STILL holding it after takeoff, then counteract gravity a bit.
        if (self.holding_jump == True and self.on_ground == False):
            self.vector[1] -= GRAVITY_STRENGTH/2 #If you're still holding jump, counteract gravity a bit.
            
    def apply_gravity(self, tmxdata):
        # Apply gravity by seeing what is on the tile below the player.
        # This is checking the TMX map for custom booleans named "solid"
        # or "platform"
        tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+TILESIZE)
        tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+TILESIZE)
        tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+TILESIZE)
        if (
        tile_to_check1['solid'] == False and tile_to_check1['platform'] == False and
        tile_to_check2['solid'] == False and tile_to_check2['platform'] == False and
        tile_to_check3['solid'] == False and tile_to_check3['platform'] == False):
            self.on_ground = False
            self.vector[1]+= GRAVITY_STRENGTH
            if(self.vector[1]>4): self.vector[1]=TERMINAL_VELOCITY #speed limit

    def apply_map_solidity(self, tmxdata):
        # Check for map solidity and stop movement based on same.
        if (self.vector[0] < 0): #moving left
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+(TILESIZE/2))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+TILESIZE-1)
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[0]=0
        if (self.vector[0] > 0): #moving right
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+(TILESIZE/2))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+TILESIZE-1)
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[0]=0
        if (self.vector[1] < 0): #moving up.
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+(TILESIZE/4))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+(TILESIZE/4))
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[1]=0
                
        # Moving down is a little more complicated. We want to not fall through the floor, but also "snap to" the floor
        # when we land on it. We accomplish this by calculating how much the character needs to move to snap to the next
        # grid location. Note that this assumes solidity is only applicable in full TILESIZE tiles.
        if (self.state != DYING) and (self.state != DEAD): #If we're dying, go through floor.
            if (self.vector[1] > 0): #moving down
                tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+TILESIZE)
                tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+TILESIZE)
                tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+TILESIZE)
                if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True or
                    tile_to_check1['platform'] == True) or (tile_to_check2['platform'] == True) or (tile_to_check3['platform'] == True):
                     snap_to_grid = TILESIZE - (self.rect.y%TILESIZE)
                     self.rect.y += snap_to_grid
                     self.vector[1]=0
                     self.on_ground = True
                     
    def update_animation_state(self):
        # Using the sprites current situation, determine what the necessary
        # animation state is supposed to be.
        
        if(self.state == DYING) or (self.state == DEAD):
            self_animation_behavior = DYING
            if(self.state_counter == 0):
                self.vector[1]=-5
                play_sound(self.sound_death)
            self.state_counter += 1
            if(self.state_counter >= 100):
                self.state = DEAD
        else:
            if(self.vector[0] < 0):
                self.facing = LEFT
                self.animation_behavior = self.WALKING
            elif(self.vector[0] > 0):
                self.facing = RIGHT
                self.animation_behavior = self.WALKING
            else:
                self.animation_behavior = self.STANDING
            if(self.vector[1] != 0):
                self.animation_behavior = self.JUMPING
                
        if(self.hit_points <= 0): self.die
    
    def update_animation_frame(self):
        # Using the sprite's current animation state and various counters,
        # determine what the current image associated with this sprite should be.
        
        # STANDING
        if self.animation_behavior == self.STANDING:
            self.image = self.my_sprite_sheet.image_at((self.STANDING_START_FRAME,0,TILESIZE,TILESIZE)).convert_alpha()

        # WALKING
        if self.animation_behavior == self.WALKING:
            self.animation_delay +=1
            if(self.animation_delay > self.ANIMATION_SPEED):
                self.animation_frame += 1
                self.animation_delay = 0
            if(self.animation_frame>=self.ANIMATION_WALKING_FRAMES):
                self.animation_frame = 0
            # We find the right place on the sprite sheet.
            # Walking frames start at 0 and each frame is 16
            # pixels, wide, so...
            x_target = (TILESIZE*self.animation_frame)
            self.image = self.my_sprite_sheet.image_at((self.WALKING_START_FRAME+x_target,0,TILESIZE,TILESIZE)).convert_alpha()  

        # JUMPING
        if self.animation_behavior == self.JUMPING:
            self.image = self.my_sprite_sheet.image_at((self.JUMPING_START_FRAME,0,TILESIZE,TILESIZE)).convert_alpha()

        # IFRAMES
        # Blinking when you're damaged.
        if(self.i_frames>0):
            if(self.i_blink_counter<=0):
                if(self.i_blink==False):
                    self.i_blink=True
                    self.i_blink_counter=5
                else:
                    self.i_blink=False
                    self.i_blink_counter=5
            else: self.i_blink_counter -= 1

        # DYING
        if self.animation_behavior == DYING or self.animation_behavior == DEAD:
            self.image = self.my_sprite_sheet.image_at((self.DYING_START_FRAME,0,TILESIZE,TILESIZE)).convert_alpha()

        # Image will be facing right by default, because that is how it is
        # draw. Flip it depending on direction.
        # Note that we don't use .self here. Why? B'c this is a global constant
        # coming from our constants file, not a class constant!
        if self.facing == LEFT:
            # The flip function has three parameters: source image,
            # whether to flip horizonal, whether to flip vertical
            # Here, we flip horizontaly if facing left.
            self.image = pygame.transform.flip(self.image, True, False)
    
    # -----------------------                    
    # Update Method
    # ----------------------=
    def update(self, tmxdata, keys):
    
        # DYING STATE ------------------
        if(self.state == DYING) or (self.state == DEAD):
            self.vector[0] = 0
        
        # ALIVE STATE -----------------
        else:
            self.apply_input(keys)
            # Check if player is at bottom of screen. If so, damage it.
            if(self.rect.y >= (tmxdata.height * TILESIZE) - (TILESIZE)): self.take_damage()
            if(self.i_frames>0):
                self.i_frames -= 1
            else: self.i_blink = False

        # IN ALL STATES ---------------
        # Using the map data, modify movement according to situation.
        self.apply_gravity(tmxdata)
        self.apply_map_solidity(tmxdata)
                   
        # Update position based on vector
        self.rect.x = self.rect.x + self.vector[0]
        self.rect.y = self.rect.y + self.vector[1]
            
        # Update animation state and frame
        self.update_animation_state()
        self.update_animation_frame()    
 
# ============================================
# ==              ENEMY CLASS               ==
# ============================================

class Enemy(pygame.sprite.Sprite):
    
    # Initialization
    def __init__ (self,init_x,init_y,init_vector):
        
        # Call the init function of the sprite class from which this inherets.
        pygame.sprite.Sprite.__init__(self)
        
        # GRAPHICS SETUP ------------        
        # Instead of loading an image directly we will use the
        # spritesheet object, defined below. 
        self.my_sprite_sheet = Sprite_Sheet("Baddybad.png")
        # Now we will initially set the image of this sprite
        # to be the first image on the sprite sheet.
        # Why do we use two paratheses? Because the .image_at function
        # expects to get a single parameter: an array of 4 numbers.
        self.image = self.my_sprite_sheet.image_at((0,0,16,16))
        # Name. This game object needs a name so others can identify it.
        self.name = "enemy"
        
        # This will track the "state" of the object.
        # Different states will have different positions on the sprite sheet.
        # Use class-specific constants to make code easier to read.
        self.WALKING = 0
        self.WALKING_START_FRAME = 0 * TILESIZE
        self.DYING_START_FRAME = 4 * TILESIZE
        
        self.state = self.WALKING 
        self.animation_behavior = self.WALKING
        self.animation_frame = 0
        self.state_counter = 0
        
        # This will be used to determine what frame of animation
        # the object is currently displaying within that state.
        self.animation_frame = 0
        self.ANIMATION_SPEED = 8
        self.ANIMATION_WALKING_FRAMES = 4
        self.animation_delay = 0
        
        # Next, set the size and position of this object, which
        # is called it's "rect" based on the size of the image.
        # Rect objects actually have a ton of useful things we can use
        # that you normally would put in the code, like x, y, etc.
        # x,y,top, left, bottom, right,topleft, bottomleft, topright, bottomright,midtop, midleft, midbottom, midright,center, centerx, centery,size, width, height,w
        self.rect = pygame.Rect(init_x,init_y,TILESIZE,TILESIZE)
        
        # Sound effects
        self.sound_squish = pygame.mixer.Sound("Toot.wav")
        
        # The direction this sprite is moving is stored in a vector.
        self.vector = list(init_vector)
        # The direction this sprite is FACING when not moving.
        self.facing = RIGHT

    # Class Accessor Methods
    
    # Returns an ordered pair that defines this object's top left
    # corner [0] = x and [1] = y
    
    def getpos(self):
        temp_x=self.rect.x
        temp_y=self.rect.y
        return [temp_x,temp_y]
    
    # Returns the image of this object
    
    def draw(self, map_image):map_image.blit(self.image,(self.rect.x,self.rect.y))
            
    # Squished by player
    
    def got_squished(self):
        self.state = DYING
        self.animation_behavior = DYING
        self.state_counter = 0
        play_sound(self.sound_squish)
        self.vector = [0,0]
        
    # Update
    def update(self, tmxdata, keys):
    
        # Update behavior based on situation
        # If alive
        if(self.state == DYING):
            self.state_counter += 1
            if(self.state_counter>30):  self.state = DEAD
        else:
            if(self.facing==LEFT): self.vector[0] = -1
            elif(self.facing==RIGHT): self.vector[0] = 1
            # Die if you are on the bottom of the screen
            if(self.rect.y >= (tmxdata.height * TILESIZE) - (TILESIZE)): self.got_squished()
            
        # ------- MAP
        # Apply gravity by seeing what is on the tile below the player.
        # This is checking the TMX map for custom booleans named "solid"
        # or "platform"
        tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+TILESIZE)
        tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+TILESIZE)
        tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+TILESIZE)
        if (
        tile_to_check1['solid'] == False and tile_to_check1['platform'] == False and
        tile_to_check2['solid'] == False and tile_to_check2['platform'] == False and
        tile_to_check3['solid'] == False and tile_to_check3['platform'] == False):
            self.on_ground = False
            self.vector[1]+= GRAVITY_STRENGTH
            if(self.vector[1]>4): self.vector[1]=TERMINAL_VELOCITY #speed limit
                
        # Check for moiving onto solid blocks and stop if you are.
        # have to break this up depending on direction because we need to know if
        # the size of the tile matters. Remember, we measure from top left corner.
        if (self.vector[0] < 0): #moving left
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+(TILESIZE/2))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+self.vector[0], self.rect.y+TILESIZE-1)
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[0]= -self.vector[0]
    
        # I also want to check the tiles immediately in front of and below, so enemy doesn't walk off cliffs.
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]-2, self.rect.y+(TILESIZE)+1)
            if(tile_to_check1['solid'] == False):
                self.vector[0]= -self.vector[0]

        if (self.vector[0] > 0): #moving right
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+(TILESIZE/2))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE, self.rect.y+TILESIZE-1)
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[0]= -self.vector[0]
                
            # I also want to check the tiles immediately in front of and below, so enemy doesn't walk off cliffs.
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x+self.vector[0]+TILESIZE+2, self.rect.y+(TILESIZE)+1)
            if(tile_to_check1['solid'] == False):
                self.vector[0]= -self.vector[0]
                
        if (self.vector[1] < 0): #moving up.
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+(TILESIZE/4))
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+(TILESIZE/4))
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+(TILESIZE/4))
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True):
                self.vector[1]=0
                
        # Moving down is a little more complicated. We want to not fall through the floor, but also "snap to" the floor
        # when we land on it. We accomplish this by calculating how much the character needs to move to snap to the next
        # grid location. Note that this assumes solidity is only applicable in full TILESIZE tiles.
        if (self.vector[1] > 0): #moving down
            tile_to_check1 = get_tile_properties(tmxdata, self.rect.x, self.rect.y+self.vector[1]+TILESIZE)
            tile_to_check2 = get_tile_properties(tmxdata, self.rect.x+(TILESIZE/2), self.rect.y+self.vector[1]+TILESIZE)
            tile_to_check3 = get_tile_properties(tmxdata, self.rect.x+TILESIZE, self.rect.y+self.vector[1]+TILESIZE)
            if (tile_to_check1['solid'] == True) or (tile_to_check2['solid'] == True) or (tile_to_check3['solid'] == True or
                tile_to_check1['platform'] == True) or (tile_to_check2['platform'] == True) or (tile_to_check3['platform'] == True):
                 snap_to_grid = TILESIZE - (self.rect.y%TILESIZE)
                 self.rect.y += snap_to_grid
                 self.vector[1]=0
                 self.on_ground = True
   
        # ------- MOVE 
        # Update position based on vector
        self.rect.x = self.rect.x + self.vector[0]
        self.rect.y = self.rect.y + self.vector[1]
        
         # ------- ANIMATE
         
        # Update animation state.
        if(self.state == DYING):
            self.animation_behavior = DYING
        elif(self.vector[0] < 0):
            self.facing = LEFT
            self.animation_behavior = self.WALKING
        elif(self.vector[0] > 0):
            self.facing = RIGHT
            self.animation_behavior = self.WALKING
            
        # Walking. Frames of animation that change
        # on an interval defined by the animation speed.
        if self.animation_behavior == self.WALKING:
            self.animation_delay +=1
            if(self.animation_delay > self.ANIMATION_SPEED):
                self.animation_frame += 1
                self.animation_delay = 0
            if(self.animation_frame>=self.ANIMATION_WALKING_FRAMES):
                self.animation_frame = 0
            # We find the right place on the sprite sheet.
            # Walking frames start at 0 and each frame is 16
            # pixels, wide, so...
            x_target = (TILESIZE*self.animation_frame)
            self.image = self.my_sprite_sheet.image_at((self.WALKING_START_FRAME+x_target,0,TILESIZE,TILESIZE)).convert_alpha()  

        # Dying
        if self.animation_behavior == DYING:
             self.image = self.my_sprite_sheet.image_at(
             (self.DYING_START_FRAME,0,TILESIZE,TILESIZE)).convert_alpha()    

        # Image will be facing left by default, because that is how it is
        # draw. Flip it depending on direction.
        # Note that we don't use .self here. Why? B'c this is a global constant
        # coming from our constants file, not a class constant!
        if self.facing == RIGHT:
            # The flip function has three parameters: source image,
            # whether to flip horizonal, whether to flip vertical
            # Here, we flip horizontaly if facing left.
            self.image = pygame.transform.flip(self.image, True, False)
            
class Effect(pygame.sprite.Sprite):
    
    def __init__(self,init_x,init_y):
        
        # Call the init function of the sprite class from which this inherets.
        pygame.sprite.Sprite.__init__(self)
        
        # GRAPHICS SETUP ------------        
        # Instead of loading an image directly we will use the
        # spritesheet object, defined below. 
        self.my_sprite_sheet = Sprite_Sheet("Little_Boom.png")
        # Now we will initially set the image of this sprite
        # to be the first image on the sprite sheet.
        # Why do we use two paratheses? Because the .image_at function
        # expects to get a single parameter: an array of 4 numbers.
        self.image = self.my_sprite_sheet.image_at((0,0,16,16))
        # Name. This game object needs a name so others can identify it.
        self.name = "effect"
        
        # This will track the "state" of the object.
        # Different states will have different positions on the sprite sheet.
        # Use class-specific constants to make code easier to read.
        self.EXPLODE = 0
        self.EXPLODE_START_FRAME = 0 * TILESIZE
        self.state = self.EXPLODE
        self.state_counter = 0
        
        # This will be used to determine what frame of animation
        # the object is currently displaying within that state.
        self.animation_behavior = self.EXPLODE
        self.animation_frame = 0
        self.ANIMATION_SPEED = 4
        self.ANIMATION_EXPLODE_FRAMES = 5
        self.animation_delay = 0
        
        # As we set initial condition, understand the spawn point is going to be up
        # and to the right of where the initial x and y are because this is a larger sprite
        # And, remember, the Rect arguments are (x,y,h,w), not x1,y1 and x2,y2!
        self.rect = pygame.Rect(init_x-TILESIZE/2,init_y-TILESIZE/2,TILESIZE*2,TILESIZE*2)
        
    # Returns the image of this object
    def draw(self, map_image):
        map_image.blit(self.image,(self.rect.x,self.rect.y))
            
    def update(self):
        #All that the effect does is cycle through its animation and then die.
        if self.animation_behavior == self.EXPLODE:
            self.animation_delay +=1
            if(self.animation_delay > self.ANIMATION_SPEED):
                self.animation_frame += 1
                self.animation_delay = 0
            if(self.animation_frame>self.ANIMATION_EXPLODE_FRAMES):
                self.animation_frame = self.ANIMATION_EXPLODE_FRAMES
                self.state = DEAD
                
            # We find the right place on the sprite sheet.
            # Walking frames start at 0 and each frame is 16
            # pixels, wide, so...
            x_target = (TILESIZE*2*self.animation_frame)
            self.image = self.my_sprite_sheet.image_at((self.EXPLODE_START_FRAME+x_target,0,TILESIZE*2,TILESIZE*2)).convert_alpha()  

# ============================================
# ==                 HUD                    ==
# ============================================
# HUD is the object that stores things that
# get drawn on top of the screen, like life bars.

class Hud(object):
    
    def __init__(self):
        
         # Call the init function of the sprite class from which this inherets.
        pygame.sprite.Sprite.__init__(self)
        
        # GRAPHICS SETUP ------------        
        # Instead of loading an image directly we will use the
        # spritesheet object, defined below. 
        self.lifebar_sprite_sheet = Sprite_Sheet("Heart.png")

        # Now we will initially set the image of this sprite
        # to be the first image on the sprite sheet.
        # Why do we use two paratheses? Because the .image_at function
        # expects to get a single parameter: an array of 4 numbers.
        self.lifebar_image = self.lifebar_sprite_sheet.image_at((0,0,16,16))

        # Name. This game object needs a name so others can identify it.
        self.name = "HUD"
        # Starting hit points to display
        self.hit_points = 4
    
    def update(self, player_life):
        
        self.hit_points = player_life
        
    def draw(self):
        
        lifebar = pygame.Surface((16,16))
        lifebar = pygame.transform.scale(lifebar,(16*self.hit_points,16))
        for i in range(0,self.hit_points):
            lifebar.blit(self.lifebar_image,(16*i,0))
        lifebar.convert_alpha()
        return lifebar
        
    