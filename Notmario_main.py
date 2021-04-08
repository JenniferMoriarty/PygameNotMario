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
from methods import *

#This file contains CONSTANTS. Technically, Python does
#not have a "constant" variable type. But, we just use
#regular old variables and treat them as constants. To
#remind us not to change them, we name them in all caps.
import constants
#More bad practice importing all of constant
from constants import *

#Import the game classes
import game_objects
import camera

# ============================================
# ==     I N I T I A L I Z A T I O N        ==
# ============================================
# This section sets up the objects and variables
# I will need in the game loop later.

#Screen - This is the game screen we'll see
# in windows.
pygame.init()
width, height = SCREEN_W, SCREEN_H
screen=pygame.display.set_mode((width, height))

#Input - This is an array that will hold
# information about what keys we pressed.
keys = [False, False, False, False, False, False, False, False]

# Create a new sprite handler object.
sprite_handler=game_objects.Sprite_Handler()

# Set the starting map
current_map = "Notlevel1.tmx"
screen_transition = False # A variable to tell us if we're in the middle of transitioning screens.
screen_transition_counter = 0

# Loading a new map and associated information
tmxdata = load_new_map(current_map, sprite_handler, RIGHT) # Load new map and ask Sprite Handler to redo sprites
                                                           # Use "RIGHT" as default entrance tile.

map_width = tmxdata.width*TILESIZE # Save the size of the incoming map
map_height = tmxdata.height*TILESIZE
map_image = load_map_image(tmxdata) # Set up an image size for the new map

loaded_map_image =  pygame.Surface((map_width, map_height)) # Save a copy of the new map's appareance
loaded_oldmap_image = pygame.Surface((SCREEN_W, SCREEN_H)) # Used during screen transitions
loaded_newmap_image = pygame.Surface((SCREEN_W, SCREEN_H)) # Used during screen transitions
blit_all_tiles(loaded_map_image, tmxdata, (0, 0)) 

# Set up the game music track.
background_music = pygame.mixer.Sound("lost_woods.wav")
background_music.set_volume(0.3)

# Create a new player object. Note that I have to use "game_object."
# to tell the code where to find the class definition because I did
# not expressly import that class from "game_object" above when I did
# my import statements.

# Create a game camera to handle rendering.
game_camera=camera.Camera()
# Tell camera to follow the player sprite
game_camera.change_follow(sprite_handler.get_player())
game_camera.snap_to_target()

# A variable to track if our code should exit
done = False

# A clock. This will make our game run the same speed regardless of hardware.
clock = pygame.time.Clock()

# Set up the menus
pygame.font.init()
myfont = pygame.font.SysFont('Times New Roman', 30)

# Start music once menu is done
background_music.play(-1)

# Variables to control the state of the game.
game_state = MAIN_MENU
player_has_died = False
player_death_counter = 0

# Oh boy it's the
# =========================================
# ==        G A M E  L O O P             ==
# =========================================
# This is the main function that runs the game

while not done:
    
    # ----------------------------
    # Updating
    # ----------------------------
    # This section handles the games logic about updating all the
    # "under the hood" information like moving sprites around, checking
    # for input, changing states, etc.
    
    # Check for input in all states.
    
    for event in pygame.event.get():
        
        if event.type==pygame.QUIT:
            done = True
            
        # When I'm changing the keys array, see how I'm using UP, DOWN, LEFT, RIGHT
        # as my indexes? It makes it super easy to understand what each element in the
        # keys array is used for, right? That's why I used them as global constants!
        if event.type == pygame.KEYDOWN:
            if event.key==K_w:
                keys[UP]=True
            elif event.key==K_s:
                keys[DOWN]=True
            elif event.key==K_a:
                keys[LEFT]=True
            elif event.key==K_d:
                keys[RIGHT]=True
            elif event.key==K_SPACE:
                keys[JUMP]=True
            elif event.key==K_g:
                keys[ZOOM_IN]=True
            elif event.key==K_h:
                keys[ZOOM_OUT]=True
            elif event.key==K_ESCAPE:
                keys[PAUSE] = True
                
        if event.type == pygame.KEYUP:
            if event.key==K_w:
                keys[UP]=False
            elif event.key==K_s:
                keys[DOWN]=False
            elif event.key==K_a:
                keys[LEFT]=False
            elif event.key==K_d:
                keys[RIGHT]=False
            elif event.key==K_SPACE:
                keys[JUMP]=False
            elif event.key==K_g:
                keys[ZOOM_IN]=False
            elif event.key==K_h:
                keys[ZOOM_OUT]=False
            elif event.key==K_ESCAPE:
                keys[PAUSE] = False
    
    # Main menu state just displays the main menu until the state ends.
    if(game_state == MAIN_MENU):
        
        background_music.stop()
        main_menu(screen, clock, myfont)
        game_state = PLAYING
        background_music.play(-1)
        
    elif(game_state == GAME_OVER):
        
        background_music.stop()
        game_over_menu(screen, clock, myfont)
        
        # Add code to reload game from save (once save is made)        
        player_has_died = False
        player_death_counter = 0
        sprite_handler.reset_player(tmxdata)
        game_state = PLAYING
        background_music.play(-1)      
        
    # Paused state renders the background and but doesn't update sprites
    elif(game_state == PAUSED):
        
        print("paused!")
        if(keys[PAUSE] == True):
            game_state = PLAYING
            keys[PAUSE] = False
        
    # Playing state gives control of character        
    elif(game_state == PLAYING):
    
        # Pause if necessary
        if(keys[PAUSE] == True):
            game_state = PAUSED
            keys[PAUSE] = False
    
        # Check to see if we need to load a new map.
        checked_exit_dict = sprite_handler.check_for_map_exit(tmxdata)
        
        # Save the last image of the map in case we screen transition.
        # Important to do this before we update and redraw next frame.
        loaded_oldmap_image = game_camera.draw(map_image)
        
        # If player is on an exit tile, transition to new screen and start playing there.
        if(checked_exit_dict["dest"] != "none"):
            
            proposed_map = checked_exit_dict["dest"]
            new_tmxdata = preview_new_map(proposed_map) # Load new map and ask Sprite Handler to redo sprites
            landing_coords = get_landing_coords(new_tmxdata, checked_exit_dict["dir"])
            landing_x = landing_coords[0]
            landing_y = landing_coords[1]

            # Convert the direction of the transition to one of the globals. The map data will be in STRING format.
            direction = 0
            if(checked_exit_dict["dir"] == "UP"): direction = UP
            elif(checked_exit_dict["dir"] == "DOWN"): direction = DOWN
            elif(checked_exit_dict["dir"] == "LEFT"): direction = LEFT
            elif(checked_exit_dict["dir"] == "RIGHT"): direction = RIGHT
                             
            # Actually carry out the transition
            composite_screen = create_transition_screen(tmxdata, new_tmxdata,landing_x,landing_y,
                                                        direction,game_camera, keys)
            scroll_transition_screen(composite_screen, direction, screen, clock)
            
            # Load the new map and get ready to play on it.        
            current_map = proposed_map
            tmxdata = load_new_map(current_map, sprite_handler,direction) # Load new map and ask Sprite Handler to redo sprites
            game_camera.snap_to_target()
            map_width = tmxdata.width*TILESIZE # Save the size of the incoming map
            map_height = tmxdata.height*TILESIZE
            map_image = load_map_image(tmxdata) # Set up an image size for the new map
            loaded_map_image =  pygame.Surface((map_width, map_height)) # Save a copy of the new map's appareance
            blit_all_tiles(loaded_map_image, tmxdata, (0, 0))

        # Update game objects
        sprite_handler.update(tmxdata, keys)
        
        # Check for collisions
        sprite_handler.player_enemy_collision_check()
        
        # Update the camera
        game_camera.update(map_width,map_height,keys)
        
        # Stop music if player died.
        check_player = sprite_handler.get_player()
        if check_player.state == DEAD:
            background_music.stop()
            player_has_died = True
            
        if(player_has_died == True):
            player_death_counter += 1
            if(player_death_counter >= 200): game_state = GAME_OVER
        
    # ----------------------------
    # Rendering (Do this in all states)
    # ----------------------------
    # This section handles actually preparing and drawing the screen
    # based on what the currently updated state of the game is.

    # Build the map_image
    # Note that we're applying camera offsets because, if we draw the whole map at once
    # first, it starts to slow down dramatically.
    map_image.fill(0)
    map_image.blit((loaded_map_image),(0,0))
        
    # Draw sprites on map
    sprite_handler.draw(map_image)
    map_image.convert()
        
    # Draw the right portion of the map to the screen    
    screen.fill(0)
    screen.blit(game_camera.draw(map_image),(0,0))
    screen.blit(sprite_handler.draw_hud(),(16,16))

    # No matter what state we are in, flip the screen.
    #Update the screen
    pygame.display.flip()
    
    # Set the game to run at 60fps
    clock.tick(60)
