import pygame
from constants import TILE_SIZE, MAP_OFFSET_Y

# Distance (world px) at which the door starts opening
OPEN_TRIGGER  = TILE_SIZE * 1.5
# Frames per animation step
ANIM_SPEED    = 6

# States
_CLOSED   = "closed"    # step=3, waiting
_OPENING  = "opening"   # step 3→0
_OPEN     = "open"      # step=0, player can pass
_CLOSING  = "closing"   # step 0→3 (plays when entering new room)


class Door:
    """
    A door placed on the wall face of a room.

    col      : tile column of the LEFT tile of the 2-wide door
    target   : room index to teleport to
    spawn    : (world_x, world_y) spawn in target room
    start_open: if True the door starts already open (used for the arrival side)
    """

    DOOR_W = TILE_SIZE * 2
    DOOR_H = TILE_SIZE * 2

    def __init__(self, col, target, spawn, start_open=False):
        self.col    = col
        self.target = target
        self.spawn  = spawn

        # World-space rect of the door (sits on the wall face, rows 1–2)
        wx = col * TILE_SIZE
        wy = 1 * TILE_SIZE          # row 1 = top of wall band
        self.world_rect = pygame.Rect(wx, wy, self.DOOR_W, self.DOOR_H)

        # Thin contact strip at the bottom of the door (where player walks in)
        self.contact_rect = pygame.Rect(wx, 3 * TILE_SIZE - 4, self.DOOR_W, 12)

        self._step  = 0 if start_open else 3
        self._state = _OPEN if start_open else _CLOSED
        self._tick  = 0
        self.triggered = False   # set True when player touches contact while open

    # ── public ────────────────────────────────────────────────────────

    def update(self, player_world_rect):
        """Call once per game frame. Returns exit dict or None."""
        dist = abs(player_world_rect.centerx - self.world_rect.centerx)

        if self._state == _CLOSED:
            if dist < OPEN_TRIGGER:
                self._state = _OPENING
                self._tick  = 0

        elif self._state == _OPENING:
            self._tick += 1
            if self._tick >= ANIM_SPEED:
                self._tick  = 0
                self._step -= 1
                if self._step <= 0:
                    self._step  = 0
                    self._state = _OPEN

        elif self._state == _OPEN:
            # close again if player walks away
            if dist > OPEN_TRIGGER * 1.6:
                self._state = _CLOSING
                self._tick  = 0
            # teleport if player touches contact strip
            elif player_world_rect.colliderect(self.contact_rect):
                self.triggered = True
                return {"target": self.target, "spawn": self.spawn}

        elif self._state == _CLOSING:
            # if player comes back, re-open
            if dist < OPEN_TRIGGER:
                self._state = _OPENING
                return None
            self._tick += 1
            if self._tick >= ANIM_SPEED:
                self._tick  = 0
                self._step += 1
                if self._step >= 3:
                    self._step  = 3
                    self._state = _CLOSED

        return None

    def start_closing(self):
        """Call on the arrival-side door so it closes after the player enters."""
        self._step  = 0
        self._state = _CLOSING
        self._tick  = 0

    @property
    def current_frame(self):
        return 3 - self._step

    def draw(self, surface, assets, camera_x):
        frames = assets["door_frames"]
        img    = frames[3 - self._step]
        sx     = self.world_rect.x - camera_x
        sy     = self.world_rect.y + MAP_OFFSET_Y
        surface.blit(img, (sx, sy))
