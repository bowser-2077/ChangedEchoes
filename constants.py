SCREEN_W = 1024
SCREEN_H = 768
TILE_SIZE = 64
MAP_ROWS  = 8
# Vertical offset to center the tile map on screen
MAP_OFFSET_Y = (SCREEN_H - MAP_ROWS * TILE_SIZE) // 2
TARGET_FPS = 60      # reference FPS for speed scaling
FPS        = 60      # fallback cap (overridden at runtime by display refresh rate)
TITLE = "Changed: Echoes"

# Tile IDs
EMPTY = 0
VOID  = 14
WALL = 1
GROUND = 2
WALL_PIPE1 = 3
WALL_PIPE2 = 4
GLASS = 5
LIB_WALL = 6
LIB_GROUND = 7
INF_WALL = 8
INF_GROUND = 9
INF_WALLTOP1 = 10
INF_WALLTOP2 = 11
INF_GROUNDTOP = 12
PAWS_GROUND = 13
GOO_WALL    = 15
GOO_GROUND  = 16

SOLID_TILES = {WALL, WALL_PIPE1, WALL_PIPE2, GLASS, LIB_WALL, INF_WALL, INF_WALLTOP1, INF_WALLTOP2, VOID, GOO_WALL}

# Sanity
SANITY_MAX        = 100
SANITY_DRAIN_RATE = 1.08    # per second in goo rooms (~92s to drain fully)
SANITY_REGEN_RATE = 0.48    # per second outside goo rooms
SANITY_BAR_W      = 220
SANITY_BAR_H      = 14
