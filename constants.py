# ============================================
# ==           GLOBAL CONSTANTS             ==
# ============================================
# Some values are used by lots of parts of the
# code and it would be helpful to be able to
# keep track of them universally or to be able
# to change them in one place. They go here.

# Directions

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# Buttons
# (Directions double as buttons for those directions)
JUMP = 4
ZOOM_IN = 5
ZOOM_OUT = 6
PAUSE = 7

# Physics Information
GRAVITY_STRENGTH = 0.2
TERMINAL_VELOCITY = 4

# Screen Information
SCREEN_W = 640
SCREEN_H = 480
STARTING_CAMERA_ZOOM = 1.5

# Map Information

TILESIZE = 16
BLOCK_LAYER = 2 # This is the layerID in Tiled we use for solidity checks with tiles on the map.

# Sprite IDs
PLAYER = 0
ENEMY = 100

# Sprite State Flags
# Each Sprite will have their own unique state flags, but we'll make some of them
# universal because they matter for sprite_handler things like collision checks.
DYING = -1
DEAD = -2

# Game States
MAIN_MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3

# Graphics information
TRANSPARENT_COLOR = 0