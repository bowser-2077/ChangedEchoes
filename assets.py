import pygame
import os
from constants import TILE_SIZE

SFX_DIR = os.path.join(os.path.dirname(__file__), "sfx")

TEXTURE_DIR = os.path.join(os.path.dirname(__file__), "textures")

# Player sprites are high-res pixel art — cap their height so they fit within
# one tile without overflowing into the wall or void.
PLAYER_H = int(TILE_SIZE * 1.76)   # 112 px at TILE_SIZE=64  (2× original size)


def load_tile(filename):
    path = os.path.join(TEXTURE_DIR, filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))


def load_player_frame(filename):
    """Load a player sprite and scale it to a fixed height, preserving aspect ratio."""
    path = os.path.join(TEXTURE_DIR, filename)
    img  = pygame.image.load(path).convert_alpha()
    ow, oh = img.get_size()
    scale  = PLAYER_H / oh
    nw     = max(1, round(ow * scale))
    return pygame.transform.scale(img, (nw, PLAYER_H))


def load_all():
    assets = {
        "wall":         load_tile("sprite_wall.png"),
        "ground":       load_tile("sprite_ground.png"),
        "glass":        load_tile("sprite_extra_glass.png"),
        "lib_wall":     load_tile("special_library_wall.png"),
        "lib_ground":   load_tile("special_library_ground.png"),
        "inf_wall":     load_tile("special_infected_wall.png"),
        "inf_ground":   load_tile("special_infected_wall.png"),
        "inf_walltop1": load_tile("special_infected_walltop_extra_1.png"),
        "inf_walltop2": load_tile("special_infected_walltop_extra_2.png"),
        "inf_groundtop":load_tile("special_infected_groundtop_extra.png"),
        "paws_ground":  load_tile("paws_groundtop.png"),
    }

    # Player walk animation frames — 3 frames per direction
    for direction in ("right", "left", "front", "back"):
        frames = []
        for i in range(1, 4):
            frames.append(load_player_frame(f"walking_{direction}_{i}.png"))
        assets[f"walk_{direction}"] = frames

    # Door animation frames: step 0 = fully open, step 3 = fully closed
    door_size = TILE_SIZE * 2
    door_frames = []
    for i in range(4):
        path = os.path.join(TEXTURE_DIR, f"door_step_{i}.png")
        img  = pygame.image.load(path).convert_alpha()
        door_frames.append(pygame.transform.scale(img, (door_size, door_size)))
    assets["door_frames"] = door_frames

    # Goo room tiles — tinted versions of infected tiles for now
    goo_w = load_tile("special_infected_wall.png")
    goo_g = load_tile("special_infected_wall.png")
    # Apply green-black tint
    for surf in (goo_w, goo_g):
        tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        tint.fill((0, 40, 0, 80))
        surf.blit(tint, (0, 0))
    assets["goo_wall"]   = goo_w
    assets["goo_ground"] = goo_g

    # SFX — loaded only if the file exists (stubs until provided)
    assets["sfx"] = _load_sfx()

    return assets


def _load_sfx():
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    sfx = {}
    SFX_FILES = {
        "ambiant_normal":  "ambiant_normal.ogg",
        "ambiant_goo":     "ambient_goo.ogg",
        "footstep_normal": "footsteps_normal.ogg",
        "footstep_goo":    "footsteps_goo.ogg",
        "door_open":       "door_open.ogg",
        "door_close":      "door_close.ogg",
        "sanity_low":      "sanity_low.ogg",
        "player_death":    "death.ogg",
        "room_enter":      "room_enter.ogg",
    }
    for key, fname in SFX_FILES.items():
        path = os.path.join(SFX_DIR, fname)
        if os.path.exists(path):
            try:
                sfx[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[SFX] Failed to load {fname}: {e}")
                sfx[key] = None
        else:
            print(f"[SFX] Missing: {path}")
            sfx[key] = None
    return sfx
